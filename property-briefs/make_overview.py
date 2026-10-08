"""Write the doctrinal overview: a short essay for each syllabus chapter and class unit,
citing the casebook cases that build each doctrine. Writes data/overview.json, shown in the
app's "Doctrinal overview" tab, where each cited case links to its brief.

One call per chapter, given the briefs of every case filed in that chapter. Cases are cited
as [[Exact Case Name]] so the app can link them; names that don't match a casebook case are
shown as plain text.

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python make_overview.py [--model google/gemini-2.5-pro] [--redo]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import practice
from briefing import TAXONOMY

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
OUT_PATH = HERE / "data" / "overview.json"

PROMPT = """You are writing a doctrinal overview of one chapter of my syllabus for {course}

CHAPTER: {chapter}
CLASS UNITS IN THIS CHAPTER (key: title):
{units}

Write:
1. "intro": 120-200 words on what this chapter is about and how its units fit together, and
   how it bears on the course's running question: when does the law side with the owner, and
   what beats ownership when it loses?
2. "units": for EACH unit key above, a mini-essay of 250-450 words in Markdown:
   - open with the core rule(s) in one or two plain sentences;
   - then how the unit's cases build, limit or split on the doctrine, in a logical (not
     case-by-case) order, citing each case where it supports a point;
   - the main tension, open question or policy debate;
   - end with a line starting "**Exam tip:**".
   Use short paragraphs and, where helpful, a short bulleted list. No headings inside a unit essay.

CITING CASES: write every case citation as [[Exact Case Name]] using the name exactly as it
appears in the briefs' headings below (e.g. [[Pierson v. Post]]). Cite only those cases.
Cite each unit's own cases at least once.

{guardrails}

Output only JSON: {{"intro": "...", "units": {{"unit_key": "essay", ...}}}}

BRIEFS (each heading gives the case name, year and its unit):
{context}
"""


def write_chapter(api_key, model, chapter, units, casebook):
    cases = [c for c in casebook if c.get("chapter") == chapter or c.get("area") == chapter]
    unit_lines = "\n".join(f"- {key}: {label}" for key, label in units.items())
    prompt = PROMPT.format(course=practice.COURSE, chapter=chapter, units=unit_lines,
                           guardrails=practice.GUARDRAILS, context=practice.brief_context(cases, 120_000))
    data = practice.ask_json(api_key, model, prompt)
    essays = data.get("units") or {}
    missing = [k for k in units if not essays.get(k)]
    return chapter, {"intro": data.get("intro", ""), "units": {k: essays.get(k, "") for k in units},
                     "cases": [c["case_name"] for c in cases], "model": model}, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemini-2.5-pro")
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")
    casebook = json.loads(CASEBOOK_PATH.read_text())
    out = {} if args.redo or not OUT_PATH.exists() else json.loads(OUT_PATH.read_text())
    todo = [(ch, units) for ch, units in TAXONOMY.items() if ch not in out]

    with ThreadPoolExecutor(4) as pool:
        jobs = [pool.submit(write_chapter, api_key, args.model, ch, units, casebook) for ch, units in todo]
        for job in jobs:
            try:
                chapter, entry, missing = job.result()
            except Exception as e:  # noqa: BLE001 - report and keep going
                print(f"FAILED: {e}")
                continue
            out[chapter] = entry
            print(f"{chapter}: {len(entry['units'])} units" + (f"  (missing: {missing})" if missing else ""))
            OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"overview covers {len(out)} of {len(TAXONOMY)} chapters")


if __name__ == "__main__":
    main()
