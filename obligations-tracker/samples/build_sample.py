"""Build the demo deal: a hand-checked ("gold") extraction of the fictional
Brightwater SPA, plus illustrative outcomes.

The gold extraction doubles as the first eval fixture: once an API key is
available, run tracker.extract on brightwater-spa.md and diff against this.

    python -m samples.build_sample   # writes samples/brightwater-tracked.json and demo/data.js
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tracker.dates import track
from tracker.schema import (
    Anchor as A,
    Category as C,
    DealExtraction,
    Obligation,
    Outcome,
    OutcomeStatus as S,
    Terms,
    Timing,
)

HERE = Path(__file__).parent


def O(id, category, title, description, obligor, timing, section, quote, terms=None, beneficiary=None,
      consequence=None, confidence=0.95):
    return Obligation(
        id=id, category=category, title=title, description=description, obligor=obligor,
        beneficiary=beneficiary, timing=timing, terms=terms or Terms(), section_ref=section,
        source_quote=quote, consequence_if_missed=consequence, confidence=confidence,
    )


def earnout(year: int, target: float) -> list[Obligation]:
    y = str(year)
    return [
        O(f"earnout-{y}-statement", C.EARNOUT, f"FY{y} Earnout Statement due",
          f"Buyer delivers its calculation of FY{y} Net Revenue to the Sellers' Representative.",
          "Buyer", Timing(anchor=A.FISCAL_YEAR_END, fiscal_year=year, offset_days=90), "2.6(b)",
          "Within ninety (90) days after the end of each of Fiscal Year 2025 and Fiscal Year 2026, Buyer shall "
          "deliver to the Sellers' Representative a statement setting forth its calculation of Net Revenue for "
          "such Fiscal Year (each, an \"Earnout Statement\").",
          Terms(metric="Net Revenue", threshold_usd=target), beneficiary="Sellers"),
        O(f"earnout-{y}-dispute", C.EARNOUT, f"FY{y} earnout dispute window closes",
          "Last day for the Sellers' Representative to dispute the Earnout Statement. Runs from actual "
          "delivery; the date shown assumes delivery on the due date.",
          "Sellers' Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on=f"earnout-{y}-statement", offset_days=30), "2.6(c)",
          "The Sellers' Representative shall have thirty (30) days after delivery of an Earnout Statement to "
          "deliver a written notice of dispute.",
          consequence="Earnout Statement becomes final if no dispute notice is delivered."),
        O(f"earnout-{y}-payment", C.EARNOUT, f"FY{y} earnout payment (if earned)",
          f"$10M is payable if FY{y} Net Revenue is at least ${target / 1e6:.0f}M; all-or-nothing, no partial payment. "
          "Earliest date shown assumes no dispute.",
          "Buyer",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on=f"earnout-{y}-dispute", offset_days=10, business_days=True),
          "2.6(a), 2.6(d)",
          "Buyer shall pay any Earnout Payment that becomes payable within ten (10) Business Days after the final "
          "determination of Net Revenue for the applicable Fiscal Year.",
          Terms(amount_usd=10_000_000, metric="Net Revenue", threshold_usd=target,
                notes="All-or-nothing: \"No partial Earnout Payment shall be payable.\""),
          beneficiary="Sellers", confidence=0.85),
    ]


OBLIGATIONS = [
    O("ppa-closing-statement", C.PURCHASE_PRICE_ADJUSTMENT, "Closing Statement due",
      "Buyer delivers its calculation of Closing Working Capital, Cash and Indebtedness.", "Buyer",
      Timing(anchor=A.CLOSING, offset_days=90), "2.4(a)",
      "Within ninety (90) days after the Closing Date, Buyer shall prepare and deliver to the Sellers' "
      "Representative a statement (the \"Closing Statement\") setting forth Buyer's good faith calculation of "
      "Closing Working Capital, Closing Cash and Closing Indebtedness."),
    O("ppa-objection-deadline", C.PURCHASE_PRICE_ADJUSTMENT, "Closing Statement objection deadline",
      "Sellers' Representative must object within 45 days of delivery or the Closing Statement becomes binding.",
      "Sellers' Representative",
      Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-closing-statement", offset_days=45), "2.4(b)",
      "If the Sellers' Representative does not deliver an Objection Notice prior to the expiration of the Review "
      "Period, the Closing Statement shall be final and binding on the parties.",
      consequence="Closing Statement becomes final and binding."),
    O("ppa-escrow-release", C.ESCROW_RELEASE, "Adjustment escrow release",
      "Joint instruction to the Escrow Agent: any shortfall to Buyer, the balance of the $1.5M Adjustment "
      "Escrow to Sellers. Earliest date shown assumes no objection.",
      "Buyer and Sellers' Representative",
      Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-objection-deadline", offset_days=5, business_days=True),
      "2.3, 2.4(c)",
      "Within five (5) Business Days after the final determination of the Closing Statement, (i) if the Final "
      "Purchase Price is less than the Estimated Purchase Price, Buyer and the Sellers' Representative shall "
      "jointly instruct the Escrow Agent to release to Buyer from the Adjustment Escrow Amount the amount of such "
      "shortfall, and (ii) the Escrow Agent shall release the remaining Adjustment Escrow Amount to the Sellers.",
      Terms(max_amount_usd=1_500_000), confidence=0.9),
    O("escrow-first-release", C.ESCROW_RELEASE, "Indemnity escrow: first release (50%)",
      "$4.5M (50% of the $9M Indemnity Escrow) goes to Sellers, less pending good-faith claims.",
      "Escrow Agent", Timing(anchor=A.CLOSING, offset_months=12), "2.5(a)",
      "On the date that is twelve (12) months after the Closing Date, the Escrow Agent shall release to the "
      "Sellers fifty percent (50%) of the Indemnity Escrow Amount, less the aggregate amount of all then-pending "
      "claims for indemnification made in good faith by Buyer.",
      Terms(amount_usd=4_500_000, percent_of_price=3.75), beneficiary="Sellers"),
    O("escrow-final-release", C.ESCROW_RELEASE, "Indemnity escrow: final release",
      "Remaining Indemnity Escrow balance goes to Sellers, less pending good-faith claims. Buyer must have "
      "any claims on file before this date.",
      "Escrow Agent", Timing(anchor=A.CLOSING, offset_months=18), "2.5(b)",
      "On the date that is eighteen (18) months after the Closing Date (the \"Final Release Date\"), the Escrow "
      "Agent shall release to the Sellers the remaining balance of the Indemnity Escrow Amount, less the aggregate "
      "amount of all then-pending claims for indemnification made in good faith by Buyer.",
      Terms(max_amount_usd=4_500_000), beneficiary="Sellers",
      consequence="Unclaimed escrow is released; Buyer loses its secured recovery source."),
    *earnout(2025, 48_000_000),
    *earnout(2026, 58_000_000),
    O("survival-general", C.INDEMNITY_SURVIVAL, "General reps survival ends",
      "Last day to bring claims for breach of general representations and warranties.", "Buyer",
      Timing(anchor=A.CLOSING, offset_months=18), "8.1(a), 8.5",
      "The representations and warranties of the Company and the Sellers contained in this Agreement (other than "
      "the Fundamental Representations and the Tax Representations) shall survive the Closing until the date that "
      "is eighteen (18) months after the Closing Date.",
      Terms(duration_months=18, threshold_usd=900_000, max_amount_usd=9_000_000,
            notes="$900K deductible; cap equals the Indemnity Escrow Amount."),
      consequence="Claims for breach of general reps are barred."),
    O("survival-fundamental", C.INDEMNITY_SURVIVAL, "Fundamental reps survival ends",
      "Last day to bring claims for breach of Fundamental Representations.", "Buyer",
      Timing(anchor=A.CLOSING, offset_months=72), "8.1(b)",
      "The Fundamental Representations shall survive the Closing until the date that is six (6) years after the "
      "Closing Date.", Terms(duration_months=72)),
    O("survival-tax", C.INDEMNITY_SURVIVAL, "Tax reps survival ends",
      "Tax representations survive until 60 days after the applicable statute of limitations expires. The "
      "date depends on each tax period.", "Buyer",
      Timing(anchor=A.EVENT, event_description="60 days after expiry of the applicable statute of limitations",
             offset_days=60), "8.1(c)",
      "The Tax Representations shall survive until sixty (60) days after the expiration of the applicable "
      "statute of limitations.", confidence=0.9),
    O("claim-response", C.INDEMNITY_CLAIM_PROCEDURE, "Claim Notice response window",
      "Indemnifying Party has 30 days after receiving a Claim Notice to object, or the claim is deemed accepted.",
      "Indemnifying Party",
      Timing(anchor=A.EVENT, event_description="30 days after receipt of each Claim Notice", offset_days=30),
      "8.4",
      "The Indemnifying Party shall have thirty (30) days after receipt of a Claim Notice to deliver a written "
      "objection; if no objection is delivered within such period, the Indemnifying Party shall be deemed to "
      "have accepted the claim.", consequence="Claim is deemed accepted."),
    O("noncompete", C.RESTRICTIVE_COVENANT, "Key Seller non-compete expires",
      "Elena Voss, Marcus Oyelaran and Priya Natarajan may not compete in the US or Canada until this date.",
      "Key Sellers", Timing(anchor=A.CLOSING, offset_months=60), "6.2(a)",
      "For a period of five (5) years after the Closing Date, no Key Seller shall, directly or indirectly, engage "
      "in, own, manage or operate any business that competes with the Business anywhere in the United States or "
      "Canada.", Terms(duration_months=60), beneficiary="Buyer"),
    O("nonsolicit", C.RESTRICTIVE_COVENANT, "Seller employee non-solicit expires",
      "Sellers may not solicit or hire Company employees until this date.", "Sellers",
      Timing(anchor=A.CLOSING, offset_months=24), "6.2(b)",
      "For a period of two (2) years after the Closing Date, no Seller shall, directly or indirectly, solicit for "
      "employment or hire any employee of the Company.", Terms(duration_months=24), beneficiary="Buyer"),
    O("dno-tail", C.INSURANCE, "D&O tail: no cancellation or amendment",
      "Buyer must keep the Company from cancelling or modifying the 6-year D&O tail policy.", "Buyer",
      Timing(anchor=A.CLOSING, offset_months=72), "6.3",
      "Prior to the Closing, the Company shall purchase a six (6)-year \"tail\" directors' and officers' "
      "liability insurance policy, and for six (6) years after the Closing Date, Buyer shall cause the Company "
      "not to cancel, amend or otherwise modify such policy.", Terms(duration_months=72),
      beneficiary="Former directors and officers"),
    O("tax-refunds", C.TAX, "Pass through pre-closing tax refunds",
      "Buyer must pay any Pre-Closing Tax Refund (net of costs) to the Sellers' Representative within 15 days "
      "of receipt.", "Buyer",
      Timing(anchor=A.EVENT, event_description="15 days after receipt of each Pre-Closing Tax Refund",
             offset_days=15), "6.4",
      "Buyer shall pay to the Sellers' Representative, for the benefit of the Sellers, the amount of any "
      "Pre-Closing Tax Refund received by Buyer or the Company, net of reasonable out-of-pocket costs, within "
      "fifteen (15) days after receipt thereof.", beneficiary="Sellers"),
    O("retention-bonuses", C.DEFERRED_PAYMENT, "Retention bonus payments",
      "$2M aggregate retention bonuses to Continuing Employees on Schedule 6.5 still employed at the first "
      "anniversary.", "Buyer (through the Company)", Timing(anchor=A.CLOSING, offset_months=12), "6.5",
      "On the first anniversary of the Closing Date, Buyer shall cause the Company to pay retention bonuses in an "
      "aggregate amount of $2,000,000 to the Continuing Employees listed on Schedule 6.5 who remain employed by "
      "the Company on such date.", Terms(max_amount_usd=2_000_000), beneficiary="Continuing Employees"),
]

DEAL = DealExtraction(
    deal_name="Project Brightwater",
    agreement_title="Stock Purchase Agreement",
    buyer="Meridian Ridge Holdings, LLC",
    seller="Stockholders of Brightwater Analytics, Inc.",
    target="Brightwater Analytics, Inc.",
    signing_date=date(2025, 2, 14),
    closing_date=date(2025, 3, 31),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=120_000_000,
    governing_law="Delaware",
    obligations=OBLIGATIONS,
)

# Illustrative, invented outcomes. They show the outcome-capture design.
OUTCOMES = [
    Outcome(obligation_id="ppa-closing-statement", status=S.SATISFIED, recorded_on=date(2025, 6, 20),
            notes="Delivered June 20, 2025."),
    Outcome(obligation_id="ppa-objection-deadline", status=S.SATISFIED, recorded_on=date(2025, 8, 4),
            notes="No Objection Notice delivered; statement final."),
    Outcome(obligation_id="ppa-escrow-release", status=S.SATISFIED, recorded_on=date(2025, 8, 11),
            amount_usd=412_000, notes="$412,000 released to Buyer (working capital shortfall); $1,088,000 to Sellers."),
    Outcome(obligation_id="retention-bonuses", status=S.PARTIAL, recorded_on=date(2026, 3, 31),
            amount_usd=1_850_000, notes="Two listed employees departed before the anniversary."),
    Outcome(obligation_id="escrow-first-release", status=S.PARTIAL, recorded_on=date(2026, 3, 31),
            amount_usd=3_200_000, notes="$3.2M released; $1.3M retained against pending Claim Notice."),
    Outcome(obligation_id="survival-general", status=S.CLAIM_MADE, recorded_on=date(2026, 2, 10),
            amount_usd=1_300_000, notes="Claim Notice re: undisclosed breach of a top-10 customer contract."),
    Outcome(obligation_id="earnout-2025-statement", status=S.SATISFIED, recorded_on=date(2026, 3, 27),
            notes="FY2025 Net Revenue reported at $46.1M vs. $48.0M target: not earned per Buyer."),
    Outcome(obligation_id="earnout-2025-dispute", status=S.DISPUTED, recorded_on=date(2026, 4, 24),
            notes="Sellers' Rep disputes revenue recognition on two multi-year contracts; referred to Independent Accountant."),
]


def main() -> None:
    tracked = track(DEAL, source="samples/brightwater-spa.md", is_sample=True)
    tracked.outcomes = OUTCOMES
    data = tracked.model_dump(mode="json")
    (HERE / "brightwater-tracked.json").write_text(json.dumps(data, indent=2) + "\n")
    demo = HERE.parent / "demo" / "data.js"
    demo.parent.mkdir(exist_ok=True)
    demo.write_text("// Generated by samples/build_sample.py. Do not edit.\nwindow.DEALS = "
                    + json.dumps([data], indent=2) + ";\n")
    print(f"{len(tracked.obligations)} obligations -> samples/brightwater-tracked.json, demo/data.js")


if __name__ == "__main__":
    main()
