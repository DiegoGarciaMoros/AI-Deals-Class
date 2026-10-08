# Property case briefs with the OpenRouter API

An AI pipeline and web app that brief Property cases **in my own note format**
(Facts / Procedural History / Issue / Holding / Rules / Reasoning / Dissent / NOTES / Takeaway),
code each case on the course's themes, and tie the cases together. The main theme:
**how often does the court side with the owner, and what beats ownership when it loses?**

## The app (`app.py`)

**Foundations of Property Law**, a Streamlit app that runs on my OpenRouter key:

The casebook is every case on my Fall 2026 syllabus (Brooks, Property; Merrill, Smith & Brady,
4th ed.), listed by class in `cases.csv`: **88 of the 96 assigned cases are briefed**, plus three
from an earlier syllabus (Hecht, eBay, Producers Lumber).

- **Search for a case.** Find any published U.S. opinion by name, with a Westlaw-style
  **Advanced search**: terms & connectors (`AND`, `OR`, `NOT`, "phrases", `~` proximity,
  `*` wildcards), jurisdiction (federal + every state), court level (highest / intermediate
  appellate / trial), decision years, citation, judge, docket number, minimum citing references,
  published-only, and sort (relevance, most cited, newest, oldest). Results come from
  CourtListener (Free Law Project); "Brief this case" gets the full text from the Caselaw Access
  Project by citation, or from CourtListener. Code: `search.py`.
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
- **Doctrinal overview.** A study guide to each syllabus chapter and its 26 class units: pick a
  chapter, then a unit. Each unit shows the black-letter rules (each tied to its cases), diagrams
  (decision trees and flowcharts drawn with Graphviz), a table of the unit's cases (question,
  holding, why it matters), tensions, exam traps and an exam tip. The estates units (Traditional
  Forms, Waste & Restraints, Concurrent Owners) are **hand-written** guides in `doctrine.py`, with
  tables of present estates and future interests, a future-interest classification tree, the Rule
  Against Perpetuities, restraints on alienation, and the forms of co-ownership. The other units
  are written by `make_overview.py` (into `data/overview.json`) with the hand-written guides as
  authority, then reviewed and corrected by hand. Every cited case links to its brief.
- **Treatises on Property Law.** Hand-written briefs (`treatises.py`) of every academic reading the
  syllabus assigns (Calabresi & Melamed, Commons, Hahn, Wahl, Bertrand, with classes and pages):
  the thesis, the argument, key terms, the cases each connects to, how to use it on the exam, and
  its limits. Plus short entries for the theorists excerpted in the casebook (Demsetz, Radin,
  Hardin, Ostrom, Heller, Rose, Sax, Coase, Penner, Grey).
- **Practice.** Exam-style multiple-choice and short-answer questions, **by topic** (chapter or
  class unit), **by case**, or **ask anything**, filtered by **difficulty** (easy / medium / hard;
  pick one level and newly written questions match it) (a freestyle question gets a tutor-style answer
  from the casebook, or "quiz me" writes a question on it). Multiple choice is graded instantly
  with an explanation of every option. Short answers are graded by AI against a 10-point rubric:
  score, rubric breakdown, what worked, what to fix, cases and doctrine to cite (linked), an
  improved version of your answer, and the model answer. The bank (`data/question_bank.json`,
  416 questions: 5 MC + 2 short answer per unit plus 2 easy MC + 1 easy short answer per unit, and 2 MC + 1 short answer per case) is built by
  `make_questions.py`; every MC answer key was checked by a second model (GPT-4.1 mini)
  answering blind, and questions where the two disagreed were dropped. "Write me a new one"
  makes a fresh question (its key isn't double-checked). Code: `practice.py`.
- **Statistics** also has charts: the owner's share of wins by era, by whether the owner sued
  or was sued, by chapter, by unit, and by whichever factor you pick.
- **Browse my briefs.** Every brief in syllabus order, filterable by chapter. Links like
  `?case=pierson-v-post` open a case's brief directly.

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

Each visit is capped at 8 briefs and 40 practice requests (new questions, grading, freestyle
answers), and results are cached, so repeat lookups cost nothing.

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
| 2d. Overview | `make_overview.py` | `data/overview.json` (doctrinal essays per chapter and unit) |
| 2e. Questions | `make_questions.py` | `data/question_bank.json` (practice questions, MC keys double-checked) |
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
python make_overview.py
python make_questions.py
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
   Optional, for case search: a free CourtListener token (courtlistener.com, sign up, then
   Profile → API) raises the search limit and lets the app download opinions CourtListener
   doesn't serve anonymously:
   ```toml
   COURTLISTENER_TOKEN = "..."
   ```
5. Deploy. The keys stay on Streamlit's server; visitors never see them.

To remove a case someone added, delete its entry from `data/added_cases.json` on GitHub.

**Study aid only.** Read every case yourself and check each brief against the opinion.
