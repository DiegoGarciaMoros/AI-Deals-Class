"""Brief every opinion in data/opinions/ in my property-notes format, via OpenRouter.

For each opinion the model writes:
  1. a brief in my format  -> briefs/<case>.md (and all of them in briefs/ALL_BRIEFS.md)
  2. coded fields + themes  -> data/case_data.csv (used by visualize.py)
                               data/casebook.json (used by app.py)

The prompt and the themes are in briefing.py.

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
from pathlib import Path

from briefing import CASES, DEFAULT_MODEL, THEMES, brief_opinion, normalize

HERE = Path(__file__).parent
OPINION_DIR = HERE / "data" / "opinions"
BRIEF_DIR = HERE / "briefs"
JSONL_PATH = HERE / "data" / "briefs.jsonl"
CSV_PATH = HERE / "data" / "case_data.csv"
CASEBOOK_PATH = HERE / "data" / "casebook.json"

CSV_FIELDS = ["slug", "class_topic", "case_name", "citation", "year", "court", "court_level",
              "plaintiff", "defendant", "winner", "disposition", "property_holder", "challenger",
              "owner_prevailed", "owner_prevailed_why", *THEMES, "principle", "remedy",
              "has_dissent", "has_concurrence", "doctrines", "check_flags", "model"]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def write_outputs():
    records = [json.loads(l) for l in JSONL_PATH.read_text().splitlines() if l.strip()]
    records = {r["slug"]: r for r in records if "error" not in r}  # latest wins
    syllabus = {slugify(r["case_name"]): r for r in CASES}
    order = list(syllabus)
    slugs = sorted(records, key=lambda s: order.index(s) if s in order else 999)

    casebook, rows = [], []
    for slug in slugs:
        r, row = records[slug], syllabus.get(slug, {})
        fields = normalize(dict(r["fields"]))
        entry = dict(fields, slug=slug, model=r["model"], brief=r["brief"],
                     case_name=row.get("case_name", fields.get("case_name")),
                     citation=row.get("citation", ""),
                     class_topic=row.get("class_topic", "Other"))
        casebook.append(entry)
        flat = {k: "; ".join(v) if isinstance(v, list) else v for k, v in entry.items()}
        rows.append(flat)

    CASEBOOK_PATH.write_text(json.dumps(casebook, indent=1))
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r.get("year") or 0))

    # One combined file to read or print, ordered like the syllabus.
    parts = ["# Property Case Briefs\n\n*AI-drafted study aid. Check every brief against the opinion.*\n"]
    parts += [records[s]["brief"] for s in slugs]
    (BRIEF_DIR / "ALL_BRIEFS.md").write_text("\n\n---\n\n".join(parts) + "\n")
    print(f"wrote {len(rows)} cases to {CSV_PATH.name}, {CASEBOOK_PATH.name} and briefs/ALL_BRIEFS.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL))
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
            brief, fields, usage = brief_opinion(api_key, args.model, path.read_text())
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
