"""File each casebook case under an area of property law and 1-2 doctrines (see TAXONOMY
in briefing.py), from its existing brief. Cheap: it sends the brief, not the opinion.

Writes data/topic_codes.json (kept by brief_cases.py when it rebuilds the casebook) and
adds "area" and "doctrine_tags" to data/casebook.json. New briefs from the app are filed
as they're written, so this is only for cases briefed before the taxonomy existed.

Usage:
    python classify_topics.py [--redo]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from briefing import DEFAULT_MODEL, call_openrouter, normalize_topics, split_reply, taxonomy_lines

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
CODES_PATH = HERE / "data" / "topic_codes.json"

PROMPT = f"""File this Property case brief under the area of property law it is mainly about,
and the 1-2 doctrines it most directly decides. Use ONLY these keys.

AREAS AND DOCTRINES (area: doctrine keys):
{taxonomy_lines()}

Reply with only a fenced ```json block:
{{"area": "...", "doctrine_tags": ["main doctrine key", "optional second key"]}}
The first doctrine must belong to "area".

BRIEF:
"""


def apply_codes(casebook, codes):
    for case in casebook:
        case.update(codes.get(case["slug"], {}))
    return casebook


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL))
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")

    casebook = json.loads(CASEBOOK_PATH.read_text())
    codes = {} if args.redo or not CODES_PATH.exists() else json.loads(CODES_PATH.read_text())
    todo = [c for c in casebook if c["slug"] not in codes]

    def classify(case):
        reply, _ = call_openrouter(api_key, args.model, PROMPT + case["brief"])
        _, fields = split_reply("\n" + reply)
        return case["slug"], normalize_topics(fields)

    with ThreadPoolExecutor(6) as pool:
        for slug, fields in pool.map(classify, todo):
            codes[slug] = {"area": fields["area"], "doctrine_tags": fields["doctrine_tags"]}
            print(f"{slug}: {fields['area']} / {', '.join(fields['doctrine_tags'])}")

    CODES_PATH.write_text(json.dumps(codes, indent=1, sort_keys=True) + "\n")
    CASEBOOK_PATH.write_text(json.dumps(apply_codes(casebook, codes), indent=1))
    print(f"filed {len(codes)} cases")


if __name__ == "__main__":
    main()
