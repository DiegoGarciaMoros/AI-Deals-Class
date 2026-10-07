"""Annotate each deal announcement with an LLM via the OpenRouter API.

Reads data/documents/*.txt, sends each document with PROMPT to OpenRouter,
parses the JSON answer, and writes:
    data/annotations.jsonl   one raw record per document (resumable)
    data/annotations.csv     flat table for analysis / visualization

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python annotate.py                      # default free model
    python annotate.py --model openai/gpt-4o-mini --limit 5
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
# Any model id from https://openrouter.ai/models works. Ids ending in ":free"
# cost nothing (rate-limited: 50/day unpaid, 1,000/day after a $10 top-up).
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

HERE = Path(__file__).parent
DOC_DIR = HERE / "data" / "documents"
JSONL_PATH = HERE / "data" / "annotations.jsonl"
CSV_PATH = HERE / "data" / "annotations.csv"
MAX_CHARS = 15000  # press releases rarely need more; keeps prompts cheap

INDUSTRIES = ["biotech_pharma", "banking_finance", "technology", "healthcare_services",
              "industrials", "energy", "real_estate", "consumer_retail", "media_telecom",
              "transportation", "other"]

PROMPT = f"""You are an M&A analyst. Read the press release below, which announces
a merger or acquisition, and return ONLY a JSON object with these keys:

"acquirer": name of the buying company (string)
"target": name of the company being acquired (string)
"target_industry": one of {INDUSTRIES}
"deal_type": one of ["strategic", "private_equity", "spac", "reverse_merger", "merger_of_equals"]
"consideration": one of ["all_cash", "all_stock", "cash_and_stock", "cvr_plus_cash", "other"]
"deal_value_usd_millions": total equity or enterprise value in US$ millions as a number, or null if not stated
"premium_pct": premium to the unaffected share price in percent as a number, or null if not stated
"expected_close": expected closing period as written, e.g. "Q3 2025" or "second half of 2025", or null
"board_unanimous": true if the target board approved unanimously, false if not, null if not stated
"hype_score": integer 1-5 rating how promotional the language is (1 = dry and factual,
              5 = heavy on "transformational", "synergies", "compelling value", etc.)
"hype_quote": the single most promotional phrase from the release, verbatim (max 25 words)
"mentions_ai": true if the release mentions artificial intelligence or machine learning, else false

If something is not in the text, use null. Do not guess numbers.

PRESS RELEASE:
"""


def call_openrouter(api_key, model, text, retries=5):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT + text[:MAX_CHARS]}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "AI Deals class - deal annotation",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                wait = 2 ** (attempt + 2)
                print(f"  HTTP {e.code}, retrying in {wait}s: {msg}")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from e


def parse_json(reply):
    """Models sometimes wrap JSON in ```json fences or add chatter; dig it out."""
    match = re.search(r"\{.*\}", reply, re.S)
    if not match:
        raise ValueError(f"no JSON in reply: {reply[:200]}")
    return json.loads(match.group(0))


def write_csv():
    rows = [json.loads(line) for line in JSONL_PATH.read_text().splitlines() if line.strip()]
    rows = [r for r in rows if "error" not in r]
    fields = ["doc_id", "source_url", "filed", "model", "acquirer", "target", "target_industry",
              "deal_type", "consideration", "deal_value_usd_millions", "premium_pct",
              "expected_close", "board_unanimous", "hype_score", "hype_quote", "mentions_ai"]
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {CSV_PATH}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, help="only annotate the first N documents")
    ap.add_argument("--redo", action="store_true", help="ignore previous results")
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")

    if args.redo and JSONL_PATH.exists():
        JSONL_PATH.unlink()
    done = set()
    if JSONL_PATH.exists():
        for line in JSONL_PATH.read_text().splitlines():
            rec = json.loads(line)
            if "error" not in rec:
                done.add(rec["doc_id"])

    docs = sorted(DOC_DIR.glob("*.txt"))[: args.limit]
    for i, path in enumerate(docs, 1):
        doc_id = path.stem
        if doc_id in done:
            continue
        raw = path.read_text()
        header = dict(re.findall(r"^(SOURCE|FILED): (.*)$", raw, re.M))
        print(f"[{i}/{len(docs)}] {doc_id}")
        record = {"doc_id": doc_id, "source_url": header.get("SOURCE"),
                  "filed": header.get("FILED"), "model": args.model}
        try:
            record.update(parse_json(call_openrouter(api_key, args.model, raw)))
        except Exception as e:  # noqa: BLE001 - log and keep going
            print(f"  failed: {e}")
            record["error"] = str(e)
        with JSONL_PATH.open("a") as f:
            f.write(json.dumps(record) + "\n")

    write_csv()


if __name__ == "__main__":
    main()
