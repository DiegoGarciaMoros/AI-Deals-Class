"""Brief every opinion in data/opinions/ in my property-notes format, via OpenRouter.

For each opinion the model writes:
  1. a brief in my format  -> briefs/<case>.md (and all of them in briefs/ALL_BRIEFS.md)
  2. a few coded fields     -> data/case_data.csv (used by visualize.py)

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python brief_cases.py --limit 2          # try two cases first
    python brief_cases.py                    # the rest (re-runnable; skips finished cases)
    python brief_cases.py --model anthropic/claude-sonnet-4.5 --redo
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Any id from https://openrouter.ai/models. A long-context model is needed:
# some opinions (Moore, Intel) run past 100,000 characters.
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
MAX_CHARS = 250_000

HERE = Path(__file__).parent
OPINION_DIR = HERE / "data" / "opinions"
BRIEF_DIR = HERE / "briefs"
JSONL_PATH = HERE / "data" / "briefs.jsonl"
CSV_PATH = HERE / "data" / "case_data.csv"

TOPICS = sorted({r["class_topic"] for r in csv.DictReader(open(HERE / "cases.csv"))})
COURSE_CASES = [r["case_name"] for r in csv.DictReader(open(HERE / "cases.csv"))]

PROMPT = f"""You are my briefing assistant for first-year Property at NYU Law. Brief the
opinion below in MY format, shown here. Use short bullets, plain sentences, and bold
doctrine names. Accuracy matters more than polish.

FORMAT (Markdown):

## [Case Name] ([Court], [Year])

**Facts**
- [Only the facts the court relied on, in chronological order. Who did what to whom.]

**Procedural History**
- [Trial court result, any intermediate appeal, who appealed]

**Issue**
- [One plain-English question, e.g. "Can a landlord retake a leased property by changing the locks while the tenant is away, without going to court?"]

**Holding**
- [Winner (role) wins.] [One or two sentences answering the Issue.] [Affirmed / Reversed / Remanded.]

**Rules**
- **[Short bold label].** [One general sentence I could paste into an outline.]
- [One bullet per rule the court states or applies, including rules it rejects, marked "Rejected:".]

**Reasoning**
- [The court's main reasons, as short bullets. Sub-bullets for supporting points.]

**Dissent ([Judge])** / **Concurrence ([Judge])**
- [Core disagreement and the alternative rule.] If none, write "None."

**NOTES:**
1. [Why this case matters for the course, and how it connects to other cases I've studied. Only name cases from this list or cases cited in the opinion: {", ".join(COURSE_CASES)}]
2. [Any tension, open question, or hypo worth raising in class]

**Takeaway:** [One sentence.]

GUARDRAILS
- Every fact, holding, and rule must come from the opinion text. Do not add facts from memory.
- Never invent a case, citation, or quote. Quote only exact words from the opinion.
- Keep majority and dissent reasoning separate. Mark anything the court didn't need to decide as *(dicta)*.
- If something is unclear, write [CHECK: reason] instead of guessing.
- Aim for 350-650 words.

AFTER the brief, output a fenced ```json block with these fields:
{{
  "case_name": "...",
  "year": 1900,
  "court": "full court name",
  "court_level": one of ["trial", "intermediate_appellate", "state_supreme", "federal_appellate", "us_supreme_court", "other"],
  "plaintiff": "...",
  "defendant": "...",
  "winner": one of ["plaintiff", "defendant", "mixed"],
  "disposition": one of ["affirmed", "reversed", "reversed_and_remanded", "affirmed_in_part", "original_decision"],
  "owner_prevailed": one of ["yes", "no", "mixed", "not_applicable"],
  "owner_prevailed_why": "one sentence: who held the property interest at stake and whether the court protected it",
  "remedy": one of ["injunction", "damages", "restitution", "title_or_declaration", "criminal_conviction", "none", "other"],
  "has_dissent": true/false,
  "has_concurrence": true/false,
  "doctrines": ["2-4 short doctrine names"],
  "check_flags": number of [CHECK] flags in your brief
}}

"owner_prevailed" asks the theme of the course: did the court side with the person
holding the record title / ownership / possession claim (owner sovereignty), or did
another interest (necessity, custom, public rights, equity, a non-owner) win?

OPINION:
"""


def call_openrouter(api_key, model, text, retries=5):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT + text[:MAX_CHARS]}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "Property case briefs",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read())
            if "choices" not in data:
                raise RuntimeError(f"unexpected response: {str(data)[:300]}")
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                wait = 2 ** (attempt + 2)
                print(f"  HTTP {e.code}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from e


def split_reply(reply):
    """Return (brief_markdown, fields_dict) from the model's reply."""
    blocks = list(re.finditer(r"```json\s*(\{.*?\})\s*```", reply, re.S))
    if not blocks:
        raise ValueError("no ```json block in reply")
    last = blocks[-1]
    return reply[: last.start()].strip(), json.loads(last.group(1))


def write_outputs():
    records = [json.loads(l) for l in JSONL_PATH.read_text().splitlines() if l.strip()]
    records = {r["slug"]: r for r in records if "error" not in r}  # latest wins
    topic_by_slug = {re.sub(r"[^a-z0-9]+", "-", r["case_name"].lower()).strip("-"): r["class_topic"]
                     for r in csv.DictReader(open(HERE / "cases.csv"))}
    fields = ["slug", "class_topic", "case_name", "year", "court", "court_level", "plaintiff",
              "defendant", "winner", "disposition", "owner_prevailed", "owner_prevailed_why",
              "remedy", "has_dissent", "has_concurrence", "doctrines", "check_flags", "model"]
    rows = []
    for slug, r in sorted(records.items(), key=lambda kv: kv[1].get("year") or 0):
        row = dict(r["fields"], slug=slug, model=r["model"],
                   class_topic=topic_by_slug.get(slug, "Other"))
        row["doctrines"] = "; ".join(row.get("doctrines") or [])
        rows.append(row)
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # One combined file to read or print, ordered like the syllabus.
    order = list(topic_by_slug)
    parts = ["# Property Case Briefs\n\n*AI-drafted study aid. Check every brief against the opinion.*\n"]
    for slug in sorted(records, key=lambda s: order.index(s) if s in order else 999):
        parts.append(records[slug]["brief"])
    (BRIEF_DIR / "ALL_BRIEFS.md").write_text("\n\n---\n\n".join(parts) + "\n")
    print(f"wrote {len(rows)} rows to {CSV_PATH} and briefs/ALL_BRIEFS.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")
    BRIEF_DIR.mkdir(exist_ok=True)

    done = set()
    if JSONL_PATH.exists() and not args.redo:
        done = {json.loads(l)["slug"] for l in JSONL_PATH.read_text().splitlines()
                if l.strip() and "error" not in json.loads(l)}

    opinions = sorted(OPINION_DIR.glob("*.txt"))[: args.limit]
    if not opinions:
        sys.exit("No opinions in data/opinions/. Run fetch_opinions.py first.")
    for i, path in enumerate(opinions, 1):
        slug = path.stem
        if slug in done:
            continue
        print(f"[{i}/{len(opinions)}] {slug}")
        record = {"slug": slug, "model": args.model}
        try:
            reply, usage = call_openrouter(api_key, args.model, path.read_text())
            brief, fields = split_reply(reply)
            record.update(brief=brief, fields=fields, usage=usage)
            (BRIEF_DIR / f"{slug}.md").write_text(brief + "\n")
        except Exception as e:  # noqa: BLE001 - log and continue
            print(f"  failed: {e}")
            record["error"] = str(e)
        with JSONL_PATH.open("a") as f:
            f.write(json.dumps(record) + "\n")

    write_outputs()


if __name__ == "__main__":
    main()
