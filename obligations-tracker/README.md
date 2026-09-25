# Postclose (working name)

Turns a signed acquisition agreement into a dated, sourced calendar of
post-closing obligations (earnouts, escrow releases, price adjustments,
survival periods, covenants) and records what actually happened.

**Live demo:** https://claude.ai/artifact/4f5ByjrZVFxzVGhmdvpKSg (fictional sample deal)

## Layout

| Path | What it is |
|---|---|
| `tracker/schema.py` | Data model: obligations, timing rules, structured terms, outcomes |
| `tracker/dates.py` | Deterministic deadline math (months, business days, dependency chains) |
| `tracker/extract.py` | Claude-based extraction from an agreement to tracker JSON |
| `tracker/fetch_edgar.py` | Downloads public merger agreements (8-K Ex. 2.1) from SEC EDGAR |
| `samples/` | Fictional sample agreement and its hand-checked gold extraction |
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

## Design rules

1. The model extracts timing *rules*; code computes *dates*.
2. Every obligation carries a verbatim source quote and section number.
3. Terms are stored as structured fields and outcomes are recorded, so
   benchmark data can build up over time (with customer permission).
