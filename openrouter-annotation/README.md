# Annotating M&A deal announcements with the OpenRouter API

**Question:** In 2025 merger announcements, who is buying whom, how do they pay,
what premium do they offer — and how much hype do the press releases use?

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1. Collect documents | `fetch_documents.py` | `data/documents/*.txt` — 40 press releases (8-K Exhibit 99.1) announcing a "definitive merger agreement", pulled from SEC EDGAR full-text search |
| 2. Annotate with an LLM | `annotate.py` | `data/annotations.jsonl` + `data/annotations.csv` |
| 3. Visualize | `visualize.py` | `data/deal_dashboard.png` |

The prompt (in `annotate.py`) asks the model for: acquirer, target, target industry,
deal type (strategic / PE / SPAC / reverse merger / MOE), form of consideration,
deal value, premium, expected close, whether the board was unanimous, a 1–5
**hype score** with the most promotional quote, and whether the release mentions AI.

## Run it

```bash
pip install -r requirements.txt

# 1. (already done — documents are committed) re-collect if you want a new sample
python fetch_documents.py --n 40 --year 2025

# 2. annotate — create a key at https://openrouter.ai/keys
export OPENROUTER_API_KEY=sk-or-...
python annotate.py --limit 3        # smoke test first
python annotate.py                  # the rest; safe to re-run, it resumes

# optional: pick another model (browse https://openrouter.ai/models, ":free" ids cost $0)
python annotate.py --model google/gemini-2.5-flash --redo

# 3. chart
python visualize.py
```

Free models allow 50 requests/day on an unpaid account and 1,000/day after a
one-time $10 credit purchase; 40 documents fit in either.
