"""Write a course synthesis that ties the casebook together, from the coded briefs.

Reads data/casebook.json (from brief_cases.py), makes one OpenRouter call, and
writes data/course_synthesis.md, which app.py shows under "Casebook map".

Usage:
    python synthesize.py [--model anthropic/claude-sonnet-4.5]
"""
import argparse
import json
from collections import Counter
import os
import sys
from pathlib import Path

from briefing import THEMES, call_openrouter

HERE = Path(__file__).parent
CASEBOOK_PATH = HERE / "data" / "casebook.json"
OUT_PATH = HERE / "data" / "course_synthesis.md"

PROMPT = """You are helping a first-year NYU Law student understand how the cases in their
Property course fit together. Below is every case they studied, coded on the course's themes,
with the principle each one stands for. Write a synthesis in Markdown, using ONLY this data.

## How my casebook fits together

### The big picture
[One paragraph: what these cases, taken together, say about owner sovereignty and its limits.
Use the counts in the data.]

### Threads that run through the course
[5-7 threads. Each thread is a ### heading naming the idea (e.g. "Necessity and the right to
exclude"), then 2-4 sentences that place 3-6 named cases on it, saying how each one moves the
idea forward, cuts back on it, or answers the same question differently. Cross unit lines: the
point is connections the syllabus order hides.]

### Rules vs. standards
[Which cases chose bright-line rules and which chose flexible standards, and what explains the choice.]

### Property rules vs. liability rules
[How the remedies protect (or don't protect) entitlements, with named cases.]

### Time and possession
[How the passage of time creates or ends rights across units.]

### Tensions to raise in class
[3-4 bullets, each pairing two named cases that seem to point in opposite directions.]

### Questions to ask of any property dispute
[A numbered checklist of 6-8 questions drawn from these cases, each followed by the case(s) it comes from.]

RULES
- Use the COUNTS below exactly; do not count anything yourself.
- In each section, name the 3-5 most telling cases. Never list every case that fits a code.
- Name only cases in the data. Never invent holdings: rely on the principle, holder,
  challenger and codes given.
- Write for a student: plain sentences, case names in *italics*, no filler.
- 1000-1400 words.
"""

KEEP = ["case_name", "year", "class_topic", "property_holder", "challenger", "owner_prevailed",
        "owner_prevailed_why", *THEMES, "remedy", "doctrines", "principle"]


def counts(cases):
    """Exact tallies for the model to quote, so it never has to count."""
    lines = [f"cases: {len(cases)}",
             f"owner_prevailed: {dict(Counter(c['owner_prevailed'] for c in cases))}",
             f"owner_prevailed before 1960: {dict(Counter(c['owner_prevailed'] for c in cases if c['year'] < 1960))}",
             f"owner_prevailed 1960 on: {dict(Counter(c['owner_prevailed'] for c in cases if c['year'] >= 1960))}"]
    for name, (kind, _, _) in THEMES.items():
        tally = Counter(v for c in cases for v in (c[name] if kind == "many" else [c[name]]))
        lines.append(f"{name}: {dict(tally.most_common())}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="anthropic/claude-sonnet-4.5")
    args = ap.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY first (https://openrouter.ai/keys).")

    cases = json.loads(CASEBOOK_PATH.read_text())
    data = "\n".join(json.dumps({k: c.get(k) for k in KEEP}) for c in cases)
    reply, usage = call_openrouter(api_key, args.model,
                                   PROMPT + f"\nCOUNTS:\n{counts(cases)}\n\nDATA (one JSON object per case):\n" + data)
    note = (f"\n\n---\n*Written by {args.model} from the coded briefs of all {len(cases)} cases. "
            "Check it against the cases themselves.*\n")
    OUT_PATH.write_text(reply.strip() + note)
    print(f"wrote {OUT_PATH} ({usage.get('completion_tokens')} tokens)")


if __name__ == "__main__":
    main()
