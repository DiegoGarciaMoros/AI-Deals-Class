"""Turn extracted timing rules into concrete due dates.

Deliberately deterministic: the model extracts the *rule* ("18 months after
Closing"), and plain code computes the *date*. Date math is where LLMs slip,
and it has to be auditable.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Optional

from .schema import Anchor, DealExtraction, Obligation, TrackedDeal, TrackedObligation


def add_months(d: date, months: int) -> date:
    """Calendar-month arithmetic, clamping to month end (Jan 31 + 1 month = Feb 28/29)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_business_days(d: date, days: int) -> date:
    """Weekends only; bank holidays are not modeled (flagged in the basis text)."""
    step = 1 if days >= 0 else -1
    remaining = abs(days)
    current = d
    while remaining:
        current += timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current


def _apply_offset(start: date, ob: Obligation) -> date:
    t = ob.timing
    result = start
    if t.offset_months:
        result = add_months(result, t.offset_months)
    if t.offset_days:
        result = (
            add_business_days(result, t.offset_days)
            if t.business_days
            else result + timedelta(days=t.offset_days)
        )
    return result


def _describe_offset(ob: Obligation) -> str:
    t = ob.timing
    parts = []
    if t.offset_months:
        parts.append(f"{t.offset_months} month{'s' if t.offset_months != 1 else ''}")
    if t.offset_days:
        unit = "business day" if t.business_days else "day"
        parts.append(f"{t.offset_days} {unit}{'s' if t.offset_days != 1 else ''}")
    return " + ".join(parts) if parts else "0 days"


def compute_due_date(
    ob: Obligation,
    deal: DealExtraction,
    by_id: dict[str, Obligation],
    _seen: Optional[set[str]] = None,
) -> tuple[Optional[date], str]:
    """Return (due_date, human-readable basis). None when the trigger is an event."""
    seen = _seen or set()
    if ob.id in seen:
        return None, "Circular dependency between obligations"
    seen = seen | {ob.id}

    t = ob.timing
    if t.anchor == Anchor.FIXED_DATE:
        return t.fixed_date, "Fixed date in agreement" if t.fixed_date else "Fixed date missing"

    if t.anchor == Anchor.CLOSING:
        if not deal.closing_date:
            return None, "Needs closing date"
        return _apply_offset(deal.closing_date, ob), f"Closing + {_describe_offset(ob)}"

    if t.anchor == Anchor.SIGNING:
        if not deal.signing_date:
            return None, "Needs signing date"
        return _apply_offset(deal.signing_date, ob), f"Signing + {_describe_offset(ob)}"

    if t.anchor == Anchor.FISCAL_YEAR_END:
        if not (t.fiscal_year and deal.fiscal_year_end_month_day):
            return None, "Needs fiscal year and fiscal year end"
        month, day = (int(x) for x in deal.fiscal_year_end_month_day.split("-"))
        fye = date(t.fiscal_year, month, day)
        return _apply_offset(fye, ob), f"FY{t.fiscal_year} year end + {_describe_offset(ob)}"

    if t.anchor == Anchor.OTHER_OBLIGATION:
        parent = by_id.get(t.depends_on or "")
        if not parent:
            return None, f"Depends on unknown obligation '{t.depends_on}'"
        parent_due, _ = compute_due_date(parent, deal, by_id, seen)
        if not parent_due:
            return None, f"Waiting on '{parent.title}'"
        return _apply_offset(parent_due, ob), f"'{parent.title}' + {_describe_offset(ob)}"

    return None, t.event_description or "Triggered by an event, not a date"


def track(deal: DealExtraction, source: Optional[str] = None, is_sample: bool = False) -> TrackedDeal:
    by_id = {o.id: o for o in deal.obligations}
    tracked = []
    for ob in deal.obligations:
        due, basis = compute_due_date(ob, deal, by_id)
        if due and ob.timing.business_days:
            basis += " (weekends skipped; holidays not modeled)"
        tracked.append(TrackedObligation(**ob.model_dump(), due_date=due, due_date_basis=basis))
    return TrackedDeal(
        **deal.model_dump(exclude={"obligations"}),
        obligations=tracked,
        source=source,
        is_sample=is_sample,
    )
