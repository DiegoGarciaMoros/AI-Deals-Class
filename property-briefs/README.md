# Property case briefs with the OpenRouter API

An AI pipeline that briefs the cases from my Property course **in my own note format**
(Facts / Procedural History / Issue / Holding / Rules / Reasoning / Dissent / NOTES / Takeaway),
codes each case's outcome, and charts one theme of the course: **how often does the
court side with the owner?**

| Step | Script | Output |
|---|---|---|
| 1. Get opinions | `fetch_opinions.py` | `data/opinions/*.txt`, full text of the 34 cases in `cases.csv`, from the Caselaw Access Project (static.case.law) |
| 2. Brief + code with an LLM | `brief_cases.py` | `briefs/<case>.md`, `briefs/ALL_BRIEFS.md`, `data/case_data.csv` |
| 3. Chart | `visualize.py` | `data/owner_sovereignty.png` |

The prompt is in `brief_cases.py`. It asks for my brief format, forbids invented facts, cases
or quotes, and asks for `[CHECK]` flags where the opinion is unclear. After each brief, the model
returns coded fields: winner, disposition, remedy, dissent, doctrines, and
**`owner_prevailed`** (did the holder of the property interest win, or did necessity,
custom, public rights or equity beat them?).

## Run it

```bash
pip install -r requirements.txt
python fetch_opinions.py                 # anything it can't find: paste the text into data/opinions/
export OPENROUTER_API_KEY=sk-or-...      # https://openrouter.ai/keys
python brief_cases.py --limit 2          # try two first and read them
python brief_cases.py                    # the rest (re-runnable; skips finished cases)
python visualize.py
```

Change the model with `--model <id>` (see https://openrouter.ai/models). It must have a long
context window, since some opinions are over 100,000 characters.

**Study aid only.** Read every case yourself and check each brief against the opinion.
