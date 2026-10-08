"""Write the doctrinal overview: for each syllabus chapter a short intro, and for each class
unit a structured study guide (summary, black-letter rules, case table, tensions, exam traps,
exam tip). Writes data/overview.json, shown in the app's "Doctrinal overview" tab next to the
hand-written guides and diagrams in doctrine.py.

One call per chapter, given the briefs of every case in that chapter plus any hand-written
guide for its units (which the model must follow). Cases are cited as [[Exact Case Name]] so
the app can link them to their briefs.

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python make_overview.py [--model google/gemini-2.5-pro] [--redo] [--only "5. The Forms of Ownership"]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import doctrine
import practice
from briefing import TAXONOMY

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
OUT_PATH = HERE / "data" / "overview.json"

PROMPT = """You are writing a study guide to one chapter of my syllabus for {course}
Write for a 1L reviewing for the exam: precise black-letter law, plain English, short items.
Doctrinal accuracy matters more than anything else.

CHAPTER: {chapter}
CLASS UNITS (key: title):
{units}

{guides}

Return JSON:
{{"intro": "90-140 words: what the chapter is about, how its units fit together, and how it bears on the course question (when does the law side with the owner, and what beats ownership?)",
  "units": {{
    "<unit key>": {{
      "summary": "one or two sentences: the core idea of the unit",
      "rules": [{{"rule": "one black-letter rule, stated precisely, as you'd write it in an outline", "cases": ["[[Case Name]]"]}}],
      "cases": [{{"case": "[[Case Name]]", "year": 1900, "question": "the question the court decided, in plain words", "answer": "who won and the rule, in one sentence", "why": "why it matters for the unit, in one sentence"}}],
      "tensions": ["one policy tension or open question, citing cases where useful"],
      "traps": ["one common exam mistake and how to avoid it"],
      "exam_tip": "one concrete instruction for spotting and analyzing this unit's issues"
    }}
  }}
}}

REQUIREMENTS
- Every unit key above must appear. 4-8 rules, 2-4 tensions, 2-4 traps per unit.
- "cases": one row for EVERY case filed in that unit (see the [unit: ...] tag in each brief
  heading), in chronological order. Do not list cases from other units there.
- Cite cases only as [[Exact Case Name]], using names exactly as in the brief headings. You may
  mention other famous cases (e.g. Boomer, Loretto) in plain italics without brackets only
  if you are certain of what they held.
- State majority rules as majority rules and minority rules as minority rules. Don't overstate
  a single case as the universal rule; say "in [state]" when a case applies one state's law.
- If a hand-written guide is given for a unit, follow it: never contradict it, and use its
  terminology. Your job there is to add the case table, tensions and traps, not to restate it.

{guardrails}

BRIEFS (each heading gives the case name, year and its unit):
{context}
"""


def write_chapter(api_key, model, chapter, units, casebook):
    cases = [c for c in casebook if c.get("chapter") == chapter or c.get("area") == chapter]
    unit_lines = "\n".join(f"- {key}: {label}" for key, label in units.items())
    guides = "\n\n".join(f"HAND-WRITTEN GUIDE FOR UNIT {key} (authoritative):\n{doctrine.GUIDES[key]}"
                         for key in units if key in doctrine.GUIDES)
    prompt = PROMPT.format(course=practice.COURSE, chapter=chapter, units=unit_lines, guides=guides,
                           guardrails=practice.GUARDRAILS, context=practice.brief_context(cases, 140_000))
    data = practice.ask_json(api_key, model, prompt)
    got = data.get("units") or {}
    missing = [k for k in units if not isinstance(got.get(k), dict)]
    return chapter, {"intro": data.get("intro", ""), "units": {k: got.get(k) or {} for k in units},
                     "model": model}, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemini-2.5-pro")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--only", help="one chapter title, to rewrite just that chapter")
    args = ap.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")
    casebook = json.loads(CASEBOOK_PATH.read_text())
    out = {} if args.redo or not OUT_PATH.exists() else json.loads(OUT_PATH.read_text())
    out = {k: v for k, v in out.items() if isinstance(next(iter(v.get("units", {}).values()), {}), dict)}
    todo = [(ch, units) for ch, units in TAXONOMY.items()
            if (args.only == ch) or (not args.only and ch not in out)]

    with ThreadPoolExecutor(4) as pool:
        jobs = [pool.submit(write_chapter, api_key, args.model, ch, units, casebook) for ch, units in todo]
        for job in jobs:
            try:
                chapter, entry, missing = job.result()
            except Exception as e:  # noqa: BLE001 - report and keep going
                print(f"FAILED: {e}")
                continue
            if missing:
                print(f"{chapter}: missing units {missing}; not saved")
                continue
            out[chapter] = entry
            print(f"{chapter}: {len(entry['units'])} units")
            OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"overview covers {len(out)} of {len(TAXONOMY)} chapters")


if __name__ == "__main__":
    main()
