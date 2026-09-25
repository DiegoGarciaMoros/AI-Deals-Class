"""Data model for post-closing obligations extracted from deal agreements.

Three design rules from the product plan live here:
  1. Terms are stored as structured fields (percent, cap, months), not just
     calendar text, so they can later feed deal-term benchmarks.
  2. Every obligation carries a verbatim source quote and section reference
     so a lawyer can verify it in seconds.
  3. Outcomes (paid, disputed, waived, claim amount) are first-class, because
     "what actually happened" is the rarest data in the market.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    EARNOUT = "earnout"
    ESCROW_RELEASE = "escrow_release"
    HOLDBACK_RELEASE = "holdback_release"
    PURCHASE_PRICE_ADJUSTMENT = "purchase_price_adjustment"
    INDEMNITY_SURVIVAL = "indemnity_survival"
    INDEMNITY_CLAIM_PROCEDURE = "indemnity_claim_procedure"
    RESTRICTIVE_COVENANT = "restrictive_covenant"  # non-compete, non-solicit
    DEFERRED_PAYMENT = "deferred_payment"
    TAX = "tax"
    REPORTING_OR_NOTICE = "reporting_or_notice"
    INSURANCE = "insurance"  # e.g. D&O tail, R&W policy
    OTHER = "other"


class Anchor(str, Enum):
    """The event a relative deadline is measured from."""

    CLOSING = "closing"
    SIGNING = "signing"
    FISCAL_YEAR_END = "fiscal_year_end"
    OTHER_OBLIGATION = "other_obligation"
    FIXED_DATE = "fixed_date"
    EVENT = "event"  # e.g. "within 30 days after receipt of a Claim Notice"


class Timing(BaseModel):
    anchor: Anchor
    offset_days: Optional[int] = Field(
        None, description="Days after the anchor. Use for 'within 90 days after Closing'."
    )
    offset_months: Optional[int] = Field(
        None, description="Calendar months after the anchor. Use for '18 months after Closing'."
    )
    fixed_date: Optional[date] = Field(None, description="Only when anchor is fixed_date.")
    fiscal_year: Optional[int] = Field(
        None, description="Only when anchor is fiscal_year_end: which fiscal year (e.g. 2025)."
    )
    depends_on: Optional[str] = Field(
        None, description="Only when anchor is other_obligation: the id of that obligation."
    )
    event_description: Optional[str] = Field(
        None, description="Plain-English description of the trigger when it is not a date."
    )
    business_days: bool = Field(False, description="True if the offset is in business days.")


class Terms(BaseModel):
    """Structured economics. Leave fields null when the agreement is silent."""

    amount_usd: Optional[float] = None
    max_amount_usd: Optional[float] = Field(None, description="Cap on a payment or on liability.")
    percent_of_price: Optional[float] = Field(None, description="e.g. 10.0 for a 10% escrow.")
    threshold_usd: Optional[float] = Field(
        None, description="Earnout target, indemnity basket/deductible, or similar threshold."
    )
    metric: Optional[str] = Field(None, description="Earnout metric, e.g. 'Net Revenue', 'EBITDA'.")
    duration_months: Optional[int] = Field(None, description="Survival or covenant length.")
    notes: Optional[str] = None


class Obligation(BaseModel):
    id: str = Field(description="Short stable slug, e.g. 'escrow-general-release'.")
    category: Category
    title: str = Field(description="Under 70 characters, e.g. 'General escrow release'.")
    description: str = Field(description="One or two sentences a deal lawyer would write.")
    obligor: str = Field(description="Party that must act, e.g. 'Buyer', 'Seller', 'Escrow Agent'.")
    beneficiary: Optional[str] = None
    timing: Timing
    terms: Terms
    section_ref: str = Field(description="Section number(s), e.g. '2.6(b)'.")
    source_quote: str = Field(
        description="Verbatim excerpt (1-3 sentences) from the agreement that creates this obligation."
    )
    consequence_if_missed: Optional[str] = Field(
        None, description="What happens if the deadline passes, when the agreement says so."
    )
    confidence: float = Field(ge=0, le=1, description="Extractor confidence, 0-1.")


class DealExtraction(BaseModel):
    """What the extractor returns for one agreement."""

    deal_name: str
    agreement_title: str
    buyer: str
    seller: str
    target: str
    signing_date: Optional[date] = None
    closing_date: Optional[date] = Field(
        None, description="Only if stated or the agreement closed at signing."
    )
    fiscal_year_end_month_day: Optional[str] = Field(
        None, description="Target's fiscal year end as MM-DD, e.g. '12-31'."
    )
    base_purchase_price_usd: Optional[float] = None
    governing_law: Optional[str] = None
    obligations: list[Obligation]


class OutcomeStatus(str, Enum):
    PENDING = "pending"
    SATISFIED = "satisfied"  # performed / paid / released on time
    PARTIAL = "partial"
    DISPUTED = "disputed"
    CLAIM_MADE = "claim_made"
    WAIVED = "waived"
    EXPIRED = "expired"  # lapsed with no action


class Outcome(BaseModel):
    obligation_id: str
    status: OutcomeStatus
    recorded_on: date
    amount_usd: Optional[float] = None
    notes: Optional[str] = None


class TrackedObligation(Obligation):
    """An obligation with its computed deadline, ready for the tracker UI."""

    due_date: Optional[date] = None
    due_date_basis: str = ""


class TrackedDeal(DealExtraction):
    obligations: list[TrackedObligation]  # type: ignore[assignment]
    outcomes: list[Outcome] = []
    source: Optional[str] = None
    is_sample: bool = False
