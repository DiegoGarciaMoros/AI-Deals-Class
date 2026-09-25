from datetime import date

from tracker.dates import add_business_days, add_months, track
from tracker.schema import Anchor, Category, DealExtraction, Obligation, Terms, Timing


def ob(id, timing, **kw):
    return Obligation(
        id=id, category=kw.get("category", Category.OTHER), title=id, description="d",
        obligor="Buyer", timing=timing, terms=Terms(), section_ref="1.1",
        source_quote="q", confidence=0.9,
    )


def deal(obligations, closing=date(2025, 3, 31)):
    return DealExtraction(
        deal_name="Test", agreement_title="SPA", buyer="B", seller="S", target="T",
        signing_date=date(2025, 2, 14), closing_date=closing, fiscal_year_end_month_day="12-31",
        obligations=obligations,
    )


def test_add_months_clamps_to_month_end():
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2025, 3, 31), 18) == date(2026, 9, 30)


def test_add_business_days_skips_weekends():
    # Friday + 1 business day = Monday
    assert add_business_days(date(2025, 3, 28), 1) == date(2025, 3, 31)
    assert add_business_days(date(2025, 3, 31), 10) == date(2025, 4, 14)


def test_closing_fiscal_year_and_dependency_chain():
    stmt = ob("stmt", Timing(anchor=Anchor.FISCAL_YEAR_END, fiscal_year=2025, offset_days=90))
    objection = ob("objection", Timing(anchor=Anchor.OTHER_OBLIGATION, depends_on="stmt", offset_days=45))
    pay = ob("pay", Timing(anchor=Anchor.OTHER_OBLIGATION, depends_on="objection", offset_days=5, business_days=True))
    escrow = ob("escrow", Timing(anchor=Anchor.CLOSING, offset_months=18))
    t = track(deal([stmt, objection, pay, escrow]))
    due = {o.id: o.due_date for o in t.obligations}
    assert due["stmt"] == date(2026, 3, 31)
    assert due["objection"] == date(2026, 5, 15)
    assert due["pay"] == date(2026, 5, 22)
    assert due["escrow"] == date(2026, 9, 30)


def test_missing_closing_and_event_triggers_have_no_date():
    escrow = ob("escrow", Timing(anchor=Anchor.CLOSING, offset_months=12))
    claim = ob("claim", Timing(anchor=Anchor.EVENT, event_description="30 days after Claim Notice"))
    t = track(deal([escrow, claim], closing=None))
    assert [o.due_date for o in t.obligations] == [None, None]
    assert t.obligations[0].due_date_basis == "Needs closing date"
    assert t.obligations[1].due_date_basis == "30 days after Claim Notice"


def test_circular_dependency_is_reported():
    a = ob("a", Timing(anchor=Anchor.OTHER_OBLIGATION, depends_on="b", offset_days=1))
    b = ob("b", Timing(anchor=Anchor.OTHER_OBLIGATION, depends_on="a", offset_days=1))
    t = track(deal([a, b]))
    assert all(o.due_date is None for o in t.obligations)
