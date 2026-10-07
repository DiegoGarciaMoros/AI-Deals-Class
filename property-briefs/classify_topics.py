"""File each casebook case under a syllabus chapter and 1-2 class units (see TAXONOMY in
briefing.py), from its existing brief. Cheap: it sends the brief, not the opinion.

Writes data/topic_codes.json, then rebuilds data/casebook.json with brief_cases.write_outputs
(which files syllabus cases in their own unit first). New briefs from the app are filed
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

from brief_cases import write_outputs
from briefing import DEFAULT_MODEL, SYLLABUS_UNIT, call_openrouter, normalize_topics, split_reply, taxonomy_lines

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
CODES_PATH = HERE / "data" / "topic_codes.json"

PROMPT = f"""File this Property case brief in my syllabus: the chapter and class unit it mainly
belongs in, plus at most one other unit it also speaks to. Use ONLY these keys.

SYLLABUS CHAPTERS AND CLASS UNITS (chapter: unit keys):
{taxonomy_lines()}

Reply with only a fenced ```json block:
{{"area": "chapter", "doctrine_tags": ["main unit key", "optional second unit key"]}}
The first unit must belong to "area". If the brief's case is assigned in a unit, use that unit first.

BRIEF:
"""


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
        assigned = SYLLABUS_UNIT.get(case["case_name"])
        note = f"(This case is assigned in unit: {assigned})\n\n" if assigned else ""
        reply, _ = call_openrouter(api_key, args.model, PROMPT + note + case["brief"])
        _, fields = split_reply("\n" + reply)
        return case["slug"], normalize_topics(fields)

    with ThreadPoolExecutor(6) as pool:
        for slug, fields in pool.map(classify, todo):
            codes[slug] = {"area": fields["area"], "doctrine_tags": fields["doctrine_tags"]}
            print(f"{slug}: {fields['area']} / {', '.join(fields['doctrine_tags'])}")

    CODES_PATH.write_text(json.dumps(codes, indent=1, sort_keys=True) + "\n")
    print(f"filed {len(codes)} cases")
    write_outputs()  # rebuild the casebook so syllabus cases stay in their own unit


if __name__ == "__main__":
    main()
