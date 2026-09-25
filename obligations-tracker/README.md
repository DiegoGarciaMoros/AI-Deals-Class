# Postclose (working name)

Turns a signed acquisition agreement into a dated, sourced calendar of
post-closing obligations (earnouts, escrow releases, price adjustments,
survival periods, covenants) and records what actually happened.

**Live demo:** https://claude.ai/artifact/4f5ByjrZVFxzVGhmdvpKSg (fictional fund, five deals)

**Pitch deck:** https://claude.ai/artifact/GthTv3ajb1vpdtCjWUVZsW

## Layout

| Path | What it is |
|---|---|
| `tracker/schema.py` | Data model: obligations, timing rules, structured terms, outcomes |
| `tracker/dates.py` | Deterministic deadline math (months, business days, dependency chains) |
| `tracker/extract.py` | Claude-based extraction from an agreement to tracker JSON |
| `tracker/fetch_edgar.py` | Downloads public merger agreements (8-K Ex. 2.1) from SEC EDGAR |
| `samples/` | Fictional sample agreement with its hand-checked gold extraction, plus four more fictional deals for the fund view |
| `demo/` | Static tracker UI (`index.html` + generated `data.js`) |
| `docs/` | Operating plan, interview script, one-pager |

## Run

```bash
pip install -r requirements.txt
python -m pytest -q                              # date math + sample checks
python -m samples.build_sample                   # regenerate demo data

# Needs network access to sec.gov and an Anthropic API key:
SEC_USER_AGENT="Your Name you@example.com" python -m tracker.fetch_edgar --limit 20
python -m tracker.extract data/edgar/<file>.htm --closing-date 2025-06-30 -o data/deal.json
```

Open `demo/index.html` and use **Open tracker file** to load any `deal.json`.

**Real deals:** `demo/index.html?data=edgar` shows two public agreements from
EDGAR (Climb Global / Douglas Stewart, 2024; Sterling / CEC Facilities, 2025),
built by `python -m samples.edgar_deals`. These were extracted by hand, not by
`tracker.extract`, as a stand-in until the pipeline runs with an API key.
`tests/test_edgar_deals.py` checks every source quote verbatim against the
downloaded filings.

## Design rules

1. The model extracts timing *rules*; code computes *dates*.
2. Every obligation carries a verbatim source quote and section number.
3. Terms are stored as structured fields and outcomes are recorded, so
   benchmark data can build up over time (with customer permission).
