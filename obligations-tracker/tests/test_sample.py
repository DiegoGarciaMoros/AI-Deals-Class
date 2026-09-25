import json
import re
from pathlib import Path

from samples.build_sample import DEAL, OUTCOMES
from tracker.dates import track

ROOT = Path(__file__).parent.parent
AGREEMENT = re.sub(r"\s+", " ", (ROOT / "samples/brightwater-spa.md").read_text().replace("**", ""))


def test_every_source_quote_is_verbatim():
    for ob in DEAL.obligations:
        assert re.sub(r"\s+", " ", ob.source_quote) in AGREEMENT, ob.id


def test_outcomes_reference_real_obligations():
    ids = {o.id for o in DEAL.obligations}
    assert all(o.obligation_id in ids for o in OUTCOMES)


def test_key_dates():
    due = {o.id: str(o.due_date) for o in track(DEAL).obligations}
    assert due["escrow-first-release"] == "2026-03-31"
    assert due["escrow-final-release"] == "2026-09-30"
    assert due["earnout-2025-statement"] == "2026-03-31"
    assert due["noncompete"] == "2030-03-31"
    assert due["survival-tax"] == "None"
