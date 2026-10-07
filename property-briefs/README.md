# Property case briefs with the OpenRouter API

An AI pipeline and web app that brief Property cases **in my own note format**
(Facts / Procedural History / Issue / Holding / Rules / Reasoning / Dissent / NOTES / Takeaway),
code each case on the course's themes, and tie the cases together. The main theme:
**how often does the court side with the owner, and what beats ownership when it loses?**

## The app (`app.py`)

**Property Case Briefer**, a Streamlit app that runs on my OpenRouter key:

The casebook is every case on my Fall 2026 syllabus (Brooks, Property; Merrill, Smith & Brady,
4th ed.), listed by class in `cases.csv`: **88 of the 96 assigned cases are briefed**, plus three
from an earlier syllabus (Hecht, eBay, Producers Lumber).

- **Brief a case.** Type any published U.S. citation (e.g. `209 Wis. 2d 605`) or paste an opinion.
  The app pulls the full text from the Caselaw Access Project, briefs it in my format, codes it
  on every theme below, files it under the syllabus chapter and class unit it belongs in, and
  names the 3 closest casebook cases by shared themes and units.
- **Add to casebook.** After a brief, one click adds the case to the casebook for everyone who
  uses the site. It then counts in every chart, table, Browse, and "closest cases". Added cases
  are saved to `data/added_cases.json` in this repo (see Deploy, step 4).
- **Casebook map.** Filter by syllabus chapter and class unit, then see how often the owner won
  in each unit and how the course's themes play out within that slice: charts by theme, a
  timeline (added cases are diamonds), and a sortable table. Below it, a written synthesis.
- **Statistics.** Tables that each ask "when does the owner win?" against one factor:
  by syllabus chapter, by class unit, and by any coded factor (what competed with ownership,
  theory of property, stick, resource, rule vs. standard, entitlement protection, who made the
  law, time, remedy, court, era, whether the owner sued or was sued, disposition, dissent), each
  with a factor × chapter count table and a factor × era win-rate table. Built in `stats.py`;
  `python stats.py` exports them all to `data/stats/*.csv`.
- **Browse my briefs.** Every brief in syllabus order, filterable by chapter.

### Syllabus chapters and class units (`TAXONOMY` in `briefing.py`)

Built from `cases.csv`, so it follows the syllabus: 10 chapters (What is Property?, Acquisition
and Claim Scope, Values Subject to Ownership, Owner Sovereignty and Its Limits, The Forms of
Ownership, Entity Property, Security Interests, Title Records and the Transfer of Property, The
Law of Neighbors, Government Forbearance and Takings) and their 26 class units. A syllabus case
is filed in its own unit, plus at most one other unit it also speaks to (from
`classify_topics.py`, saved in `data/topic_codes.json`, editable by hand). Cases from outside
the syllabus are filed by the model.

### Not briefed yet: paste their text

These aren't in the Caselaw Access Project, so `fetch_opinions.py` can't get them. Paste each
opinion into `data/opinions/<name>.txt` (names below) and run `python brief_cases.py`:

| Case | Why | File |
|---|---|---|
| Keeble v. Hickeringill (1707) | English | `keeble-v-hickeringill.txt` |
| Armory v. Delamirie (1722) | English | `armory-v-delamirie.txt` |
| Hannah v. Peel (1945) | English | `hannah-v-peel.txt` |
| Wood v. Leadbitter (1845) | English | `wood-v-leadbitter.txt` |
| Charles v. Barzey, [2002] UKPC 68 | Privy Council | `charles-v-barzey.txt` |
| Briggs v. Southwestern Energy (Pa. 2020) | too recent for CAP | `briggs-v-southwestern-energy-production-co.txt` |
| Cedar Point Nursery v. Hassid (2021) | too recent for CAP | `cedar-point-nursery-v-hassid.txt` |
| Timmer v. Gray | citation not found; add it to `cases.csv` | `timmer-v-gray.txt` |

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
| 1. Get opinions | `fetch_opinions.py` | `data/opinions/*.txt`, full text of the cases in `cases.csv` |
| 2. Brief + code | `brief_cases.py` | `briefs/<case>.md`, `briefs/ALL_BRIEFS.md`, `data/case_data.csv`, `data/casebook.json` |
| 2b. File by unit | `classify_topics.py` | `data/topic_codes.json` (each case's chapter, unit, and one other unit it speaks to) |
| 2c. Statistics | `stats.py` | `data/stats/*.csv` (the tables in the Statistics tab) |
| 3. Synthesize | `synthesize.py` | `data/course_synthesis.md` |
| 4. Chart | `visualize.py` | `data/owner_sovereignty.png` |

```bash
pip install -r requirements.txt
python fetch_opinions.py                 # anything it can't find: paste the text into data/opinions/
export OPENROUTER_API_KEY=sk-or-...      # https://openrouter.ai/keys
python brief_cases.py --limit 2          # try two first and read them
python brief_cases.py                    # the rest (re-runnable; skips finished cases)
python classify_topics.py --redo
python stats.py
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
