# Property case briefs with the OpenRouter API

An AI pipeline and web app that brief Property cases **in my own note format**
(Facts / Procedural History / Issue / Holding / Rules / Reasoning / Dissent / NOTES / Takeaway),
code each case on the course's themes, and tie the cases together. The main theme:
**how often does the court side with the owner, and what beats ownership when it loses?**

## The app (`app.py`)

**Property Case Briefer**, a Streamlit app that runs on my OpenRouter key:

- **Brief a case.** Type any published U.S. citation (e.g. `209 Wis. 2d 605`) or paste an opinion.
  The app pulls the full text from the Caselaw Access Project, briefs it in my format, codes it
  on every theme below, and places it in my casebook. It names the 3 closest casebook cases by
  shared themes and adds a "Connections to my casebook" section to the brief.
- **Casebook map.** Charts of all 34 casebook cases by any theme, colored by whether the owner
  won, on a timeline, plus a written synthesis of the threads that run through the course.
- **Browse my briefs.** Every casebook brief with its theme codes and nearest neighbors.

Each visit is capped at 8 briefs, and results are cached, so repeat lookups cost nothing.

### Themes each case is coded on (`briefing.py`)

| Theme | Question |
|---|---|
| Property holder / challenger | Whose property interest is at stake, and who is attacking it? |
| Owner prevailed | Did the court protect the property holder? |
| Competing values | What was weighed against ownership: necessity, custom, public rights, equity, reliance, labor, personhood, productive use, contract, third parties? |
| Justifications | Which theory of property the court relied on: first possession, labor, efficiency, personhood, custom, public trust, fairness, settled expectations, clear rules, owner autonomy, precedent |
| Sticks | Which sticks in the bundle are at stake: exclude, use, possess, transfer, destroy, abandon, inherit, commodify, income |
| Resource | Land, water, wild animals, chattels, the human body, IP, digital systems, cultural artifacts |
| Rule or standard | Bright-line rule or flexible standard? |
| Entitlement protection | Property rule, liability rule, or inalienability (Calabresi & Melamed) |
| Lawmaker | Did the court make new law, apply existing law, apply a statute, or defer to the legislature? |
| Time shifts rights | Did the passage of time create or end a right? |

## The pipeline

| Step | Script | Output |
|---|---|---|
| 1. Get opinions | `fetch_opinions.py` | `data/opinions/*.txt`, full text of the 34 cases in `cases.csv` |
| 2. Brief + code | `brief_cases.py` | `briefs/<case>.md`, `briefs/ALL_BRIEFS.md`, `data/case_data.csv`, `data/casebook.json` |
| 3. Synthesize | `synthesize.py` | `data/course_synthesis.md` |
| 4. Chart | `visualize.py` | `data/owner_sovereignty.png` |

```bash
pip install -r requirements.txt
python fetch_opinions.py                 # anything it can't find: paste the text into data/opinions/
export OPENROUTER_API_KEY=sk-or-...      # https://openrouter.ai/keys
python brief_cases.py --limit 2          # try two first and read them
python brief_cases.py                    # the rest (re-runnable; skips finished cases)
python synthesize.py
python visualize.py
streamlit run app.py                     # the app, locally
```

## Deploy the app (Streamlit Community Cloud, free)

1. In OpenRouter, create a **separate key with a credit limit** (e.g. $5) for the app. The link
   is public, so the limit is what protects you.
2. Go to https://share.streamlit.io, sign in with GitHub, and click **Create app**.
3. Pick this repo and branch, and set the main file path to `property-briefs/app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   OPENROUTER_API_KEY = "sk-or-..."
   ```
5. Deploy. The key stays on Streamlit's server; visitors never see it.

**Study aid only.** Read every case yourself and check each brief against the opinion.
