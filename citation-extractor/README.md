# Citation Extractor

A small web app that pulls every citation out of a judicial opinion and turns them
into a clean, de-duplicated table of authorities, with links to each case.

- **Input:** the text of a case. Paste it in or upload a file; plain text and HTML both work.
- **Output:** a parsed list of authorities (cases, statutes/rules/regulations, and
  secondary sources). Under each one you get every place it is cited, with the
  surrounding text, plus export files.

## Quick start

```bash
cd citation-extractor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COURTLISTENER_API_TOKEN=...   # optional, see below
python app.py                        # → http://127.0.0.1:5000
```

Click **Load sample** to try it on `samples/sample_opinion.txt`.

There is also a command-line version that writes every export to a folder:

```bash
python cli.py samples/sample_opinion.txt --out exports/ --lookup
```

## What it does

| Step | Details |
| --- | --- |
| **Clean** | Strips HTML, normalizes odd whitespace, curly quotes and soft hyphens, re-joins words hyphenated across lines, and unwraps hard line breaks so a citation split over two lines still parses. |
| **Parse** | Uses [eyecite](https://github.com/freelawproject/eyecite) (from Free Law Project) to find full case citations, short cites (`550 U.S. at 555`), `Id.`, `supra`, statutes and law-review articles. A second regex pass catches U.S.C./C.F.R. sections that eyecite misses or cuts short (`42 U.S.C. § 2000e-2`, `17 C.F.R. § 240.10b-5`) and the Federal Rules (`Fed. R. Civ. P. 12(b)(6)`). |
| **Normalize** | Standardizes reporter abbreviations (`410 U. S. 113` → `410 U.S. 113`). Repairs case names eyecite truncates (`Bell Atlantic Corp.`, `Flagg Bros., Inc.`, `United States v. …`) and strips introductory signals out of party names. Picks each case's most common year and court. |
| **De-duplicate** | Each authority appears once. Repeat full cites, short cites, `Id.` and `supra` are grouped under it, and parallel citations (`550 U.S. 544, 127 S. Ct. 1955, 167 L. Ed. 2d 929`) are merged into one entry. With lookup turned on, any two cites that CourtListener resolves to the same opinion are also merged. |
| **Context** | Every citation keeps its pin cite, introductory signal (*See*, *But see*, *Cf.*, …), explanatory parenthetical, and about 220 characters of text on either side. The **Annotated text** tab highlights each citation in the opinion; click one to jump to its authority. |
| **Link** | When lookup is on, the app makes one batched call to the [CourtListener citation lookup API](https://www.courtlistener.com/help/api/rest/citation-lookup/) and attaches the matching opinion's URL. Ambiguous citations list all the candidate opinions. Every case also gets a CourtListener citation-redirect link that needs no API call, and U.S.C., C.F.R. and Federal Rules entries link to Cornell LII. |

### Exports

| File | Contents |
| --- | --- |
| `citations-authorities.csv` | One row per authority: name, citation, parallel cites, court, year, times cited (broken down by full, short, *Id.* and *supra*), pin cites, signals, parentheticals, lookup status and link |
| `citations-occurrences.csv` | One row per citation in document order, with its context (the citation itself is wrapped in `[[ ]]`) |
| `table-of-authorities.html` / `.md` | Table of authorities grouped by type, ready to print or paste |
| `annotated-opinion.html` | The cleaned opinion text with every citation highlighted and linked |
| `citations.json` | Everything above, as structured data |
| `citations-export.zip` | All of the files above |

## CourtListener API token

CourtListener's citation lookup API needs a free API token. Sign in at
courtlistener.com and go to **Profile → Developer Tools**. Then do one of these:

- set `COURTLISTENER_API_TOKEN` before starting the server, or
- paste the token into the field in the UI. It is sent only to this app's server. It is
  saved in your browser only if you tick "Remember".

The API accepts up to 250 citations per request and limits how many citations you can
look up per minute. The client batches citations to fit, caches results in memory, and
shows any error (bad token, throttling, network) in a banner without failing the rest of
the analysis.

## API

```
POST /api/analyze        {"text": "...", "lookup": true, "token": "optional"}  → JSON result
POST /api/export/<fmt>   body = the JSON result; fmt ∈ authorities_csv, occurrences_csv,
                         toa_html, toa_md, annotated_html, json, zip
```

## Tests

```bash
pip install pytest && python -m pytest -q
```

The tests cover parsing, name repair, parallel and short-form grouping, statutes and rules,
the exports, the Flask endpoints, and the CourtListener client (against a mocked HTTP session).

## Notes and limitations

- `eyecite` is pinned to **2.6.11**. Versions 2.7.x attach the wrong year and court to a
  citation when another citation follows in the next sentence.
- `supra` and short cites resolve only when the full citation appears earlier in the same text.
- Constitutional provisions, state codes other than those eyecite recognizes, and docket
  numbers are not extracted.
- Always check the output against the opinion before relying on it.
