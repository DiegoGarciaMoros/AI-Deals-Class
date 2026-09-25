"""Checks for the hand-extracted EDGAR deals (samples/edgar_deals.py)."""

import re
from pathlib import Path

import pytest

from samples.edgar_deals import CLIMB, DEALS, STERLING
from tracker.dates import track

EDGAR_DIR = Path(__file__).parent.parent / "data" / "edgar"
FILES = {
    CLIMB.deal_name: "0001437749-24-024891_ex_708589.htm",
    STERLING.deal_name: "0001193125-25-142774_d949187dex21.htm",
}


def _norm(text: str) -> str:
    """Compare ignoring whitespace, quote style and case (EDGAR HTML splits defined terms oddly)."""
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", "", text).lower()


@pytest.mark.parametrize("deal", [d for d, _ in DEALS], ids=lambda d: d.deal_name)
def test_source_quotes_are_verbatim(deal):
    path = EDGAR_DIR / FILES[deal.deal_name]
    if not path.exists():
        pytest.skip("filing not downloaded; run python -m tracker.fetch_edgar")
    from tracker.extract import load_text

    body = _norm(load_text(path))
    missing = [o.id for o in deal.obligations if _norm(o.source_quote) not in body]
    assert not missing, f"quotes not found verbatim: {missing}"


def test_every_deal_tracks_with_unique_ids():
    for deal, _ in DEALS:
        ids = [o.id for o in deal.obligations]
        assert len(ids) == len(set(ids))
        tracked = track(deal)
        undated = [o.id for o in tracked.obligations if o.due_date is None and o.timing.anchor.value != "event"]
        assert not undated, undated


def test_fixed_date_with_offset():
    by_id = {o.id: o for o in track(CLIMB).obligations}
    assert str(by_id["earnout-final-calc"].due_date) == "2025-10-30"
    assert str(by_id["contingency-final-calc"].due_date) == "2025-08-30"
