# Property case briefs with the OpenRouter API

An AI pipeline and web app that brief Property cases **in my own note format**
(Facts / Procedural History / Issue / Holding / Rules / Reasoning / Dissent / NOTES / Takeaway),
code each case on the course's themes, and tie the cases together. The main theme:
**how often does the court side with the owner, and what beats ownership when it loses?**

## The app (`app.py`)

**Property Case Briefer**, a Streamlit app that runs on my OpenRouter key:

- **Brief a case.** Type any published U.S. citation (e.g. `209 Wis. 2d 605`) or paste an opinion.
  The app pulls the full text from the Caselaw Access Project, briefs it in my format, codes it
  on every theme below, files it under an area of property law and its doctrines, and places it
  in my casebook. It names the 3 closest casebook cases by shared themes and doctrines and adds a
  "Connections to my casebook" section to the brief.
- **Add to casebook.** After a brief, one click adds the case to the casebook for everyone who
  uses the site. It then counts in every chart, the table, Browse, and "closest cases". Added cases
  are saved to `data/added_cases.json` in this repo (see Deploy, step 4).
- **Casebook map.** Filter by area of property law and doctrine, then see how often the owner
  won in each doctrine and how the course's themes play out within that slice: charts by theme,
  a timeline (added cases are diamonds), and a sortable table. Below it, a written synthesis of
  the original 34 cases.
- **Browse my briefs.** Every brief, sorted by area and doctrine, with its theme codes and nearest
  neighbors.

### Areas and doctrines (`TAXONOMY` in `briefing.py`)

Each case is filed under one area and one or two doctrines, from a fixed list so cases sort
consistently: Acquiring property, Rights and limits of ownership, Bailments and licenses,
Remedies, Public and common property, Water, Estates and future interests, Co-ownership and
leases, Land use and servitudes, Transfers and takings. New briefs are filed as they're written.
The original 34 were filed from their briefs by `classify_topics.py`; the result is in
`data/topic_codes.json`, which you can edit by hand to re-file a case.

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
| 2b. File by topic | `classify_topics.py` | `data/topic_codes.json` (area + doctrines for cases briefed before the taxonomy) |
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
   To save cases added through the app, also add a GitHub token. On GitHub: Settings → Developer
   settings → Fine-grained tokens → Generate new token, choose **only this repository**, and set
   **Contents** to **Read and write**. Then add it on its own line:
   ```toml
   GITHUB_TOKEN = "github_pat_..."
   ```
   Without it the app still works, but added cases disappear when the app restarts. If you deploy
   from a branch other than `claude/amazing-gauss-ggp9w6`, add `GITHUB_BRANCH = "main"` (or yours).
5. Deploy. The keys stay on Streamlit's server; visitors never see them.

To remove a case someone added, delete its entry from `data/added_cases.json` on GitHub.

**Study aid only.** Read every case yourself and check each brief against the opinion.
