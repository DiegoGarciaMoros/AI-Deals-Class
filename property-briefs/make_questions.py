"""Build the exam-practice question bank: data/question_bank.json.

For each class unit: 5 multiple-choice + 2 short-answer questions on the unit's cases, plus
2 easy multiple-choice + 1 easy short-answer question.
For each case: 2 multiple-choice + 1 short-answer question on that case.
Every MC answer key is checked by a second model answering blind; questions where the two
models disagree are dropped (their count is printed), so the bank keeps only keys that two
models agree on.

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python make_questions.py                # re-runnable: skips scopes already in the bank
    python make_questions.py --only units   # or: --only cases
    python make_questions.py --redo
"""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import practice
from briefing import DOCTRINE_AREA, DOCTRINE_LABEL

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
BANK_PATH = HERE / "data" / "question_bank.json"


def scopes(casebook, only=None):
    """(scope_id, kind, label, cases, n_mc, n_sa, difficulty) for every unit and case, plus an
    extra set of easy questions per unit (the main pass skews medium/hard)."""
    out = []
    if only in (None, "units"):
        for unit, label in DOCTRINE_LABEL.items():
            cases = practice.unit_cases(casebook, unit)
            if cases:
                out.append((f"unit:{unit}", "unit", f"the class unit '{label}'", cases, 5, 2, None))
                out.append((f"unit-easy:{unit}", "unit", f"the class unit '{label}'", cases, 2, 1, "easy"))
    if only in (None, "cases"):
        for c in casebook:
            out.append((f"case:{c['slug']}", "case", f"the case {c['case_name']} ({c.get('year')})", [c], 2, 1, None))
    return out


def build(api_key, scope):
    scope_id, kind, label, cases, n_mc, n_sa, difficulty = scope
    context = practice.brief_context(cases)
    kept, dropped = [], 0
    try:
        questions = practice.generate(api_key, label, context, n_mc, n_sa, difficulty=difficulty)
    except Exception as e:  # noqa: BLE001 - report and keep going
        return scope_id, [], 0, str(e)
    main = cases[0]
    unit = scope_id.split(":", 1)[1] if kind == "unit" else (main.get("doctrine_tags") or ["other"])[0]
    for q in questions:
        if q["type"] == "mc":
            try:
                q["checked_by"] = practice.CHECK_MODEL
                if practice.check_mc(api_key, q, context) != q["answer"]:
                    dropped += 1
                    continue
            except Exception:  # noqa: BLE001 - unverifiable: drop
                dropped += 1
                continue
        q.update(scope=scope_id, kind=kind, unit=unit, chapter=DOCTRINE_AREA.get(unit, "Other"),
                 case_slug=main["slug"] if kind == "case" else None, model=practice.PRACTICE_MODEL)
        q["id"] = hashlib.sha1((scope_id + q["stem"]).encode()).hexdigest()[:10]
        kept.append(q)
    return scope_id, kept, dropped, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["units", "cases"])
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")

    casebook = json.loads(CASEBOOK_PATH.read_text())
    bank = [] if args.redo or not BANK_PATH.exists() else json.loads(BANK_PATH.read_text())
    done = {q["scope"] for q in bank}
    todo = [s for s in scopes(casebook, args.only) if s[0] not in done]
    print(f"{len(todo)} scopes to write")

    total_dropped = 0
    with ThreadPoolExecutor(args.workers) as pool:
        for i, (scope_id, kept, dropped, error) in enumerate(pool.map(lambda s: build(api_key, s), todo), 1):
            total_dropped += dropped
            bank += kept
            print(f"[{i}/{len(todo)}] {scope_id}: kept {len(kept)}, dropped {dropped}" + (f"  ERROR {error}" if error else ""))
            if i % 10 == 0:  # save progress
                BANK_PATH.write_text(json.dumps(bank, indent=1))
    BANK_PATH.write_text(json.dumps(bank, indent=1))
    mc = sum(q["type"] == "mc" for q in bank)
    print(f"bank: {len(bank)} questions ({mc} MC, {len(bank) - mc} short answer); "
          f"dropped {total_dropped} MC this run where the two models disagreed")


if __name__ == "__main__":
    main()
