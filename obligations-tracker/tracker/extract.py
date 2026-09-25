"""Extract post-closing obligations from an agreement with Claude.

Usage:
    python -m tracker.extract path/to/agreement.(txt|htm|html|md) [--closing-date YYYY-MM-DD] [-o out.json]

Requires ANTHROPIC_API_KEY (or another credential the Anthropic SDK can find).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import anthropic

from .dates import track
from .schema import DealExtraction

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are a senior M&A associate building a post-closing obligations \
calendar for a client. You read the full acquisition agreement and list every obligation, \
right or deadline that continues after closing and that someone must calendar or act on.

Include, where present: earnout periods, statements, objection windows and payments; escrow \
and holdback releases (general, special, adjustment); purchase price adjustment statements, \
objection periods and true-up payments; survival periods for general, fundamental and tax \
representations and for specific indemnities; claim notice procedures; non-compete, \
non-solicit and confidentiality covenants with their durations; deferred or installment \
payments; tax filings, elections and refunds; D&O tail and R&W insurance obligations; \
and notice or reporting obligations.

Exclude pre-closing covenants and closing conditions unless they survive closing.

Rules:
- Model timing as a rule, not a date: anchor + offset. Never compute calendar dates yourself.
  "18 months after the Closing Date" -> anchor closing, offset_months 18.
  "within 90 days after the end of fiscal year 2025" -> anchor fiscal_year_end, fiscal_year 2025, offset_days 90.
  "10 Business Days after the Final Closing Statement" -> anchor other_obligation, depends_on that obligation's id, offset_days 10, business_days true.
  Triggers with no date (e.g. after receipt of a claim notice) -> anchor event with event_description.
- Split multi-stage mechanics into separate obligations linked with depends_on
  (statement due -> objection deadline -> payment).
- source_quote must be copied verbatim from the agreement, 1-3 sentences.
- Fill Terms only with numbers stated in the agreement. Leave unknowns null; do not guess.
- confidence below 0.7 means a lawyer should look closely (ambiguous drafting, cross-references you could not resolve).
- Use defined party names as the agreement uses them (e.g. "Buyer", "Sellers' Representative")."""


def load_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".htm", ".html"}:
        from bs4 import BeautifulSoup

        return BeautifulSoup(raw, "html.parser").get_text("\n")
    return raw


def extract(agreement_text: str, client: anthropic.Anthropic | None = None) -> DealExtraction:
    client = client or anthropic.Anthropic()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"<agreement>\n{agreement_text}\n</agreement>\n\n"
                "Extract the deal header and every post-closing obligation.",
            }
        ],
        output_format=DealExtraction,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model declined the request: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Output hit max_tokens; split the agreement or raise the limit.")
    if response.parsed_output is None:
        raise RuntimeError("No structured output returned.")
    return response.parsed_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agreement", type=Path)
    parser.add_argument("--closing-date", type=date.fromisoformat, help="Override or supply closing date.")
    parser.add_argument("-o", "--output", type=Path, help="Write tracked deal JSON here.")
    args = parser.parse_args(argv)

    deal = extract(load_text(args.agreement))
    if args.closing_date:
        deal.closing_date = args.closing_date
    tracked = track(deal, source=str(args.agreement))

    out = json.dumps(tracked.model_dump(mode="json"), indent=2)
    if args.output:
        args.output.write_text(out + "\n")
        print(f"Wrote {len(tracked.obligations)} obligations to {args.output}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
