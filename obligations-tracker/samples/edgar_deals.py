"""Two real deals from SEC EDGAR, extracted by hand (not by tracker.extract).

These are public 8-K exhibits fetched with tracker.fetch_edgar. The
extraction was written in a working session without an API key, reading each
agreement directly, so it is a stand-in until the pipeline runs on them.
Every source_quote is checked verbatim against the filing by
tests/test_edgar_deals.py when the downloaded filings are present.

Outcomes are left empty: what actually happened on these deals is not
recorded here.

    python -m samples.edgar_deals   # writes samples/edgar-tracked.json and demo/edgar-data.js
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tracker.dates import track
from tracker.schema import Anchor as A, Category as C, DealExtraction, Terms, Timing

from .build_sample import O

HERE = Path(__file__).parent

FUND = {"name": "Public deals from SEC EDGAR",
        "note": "Real agreements · hand-extracted, pipeline not yet run"}

CLIMB_URL = "https://www.sec.gov/Archives/edgar/data/945983/000143774924024891/ex_708589.htm"
STERLING_URL = "https://www.sec.gov/Archives/edgar/data/874238/000119312525142774/d949187dex21.htm"


def quarter_report(qid, quarter_end, label, final=False):
    if final:
        return O("earnout-final-calc", C.EARNOUT, "Final Earn-Out Calculations due",
                 "Buyer delivers Q3 2025 Gross Profit and the resulting Earn-Out Payment for the "
                 "Oct 2024 to Sep 2025 Earnout Period.", "Buyer",
                 Timing(anchor=A.FIXED_DATE, fixed_date=quarter_end, offset_days=30), "1.03(a)",
                 "with respect to the final calendar quarter during the Earnout Period (i.e., the quarter ending "
                 "September 30, 2025), the resulting Earn-Out Payment, together with reasonable schedules and data "
                 "to support the calculations contained therein",
                 Terms(metric="Gross Profit"), beneficiary="Seller", confidence=0.9)
    return O(qid, C.REPORTING_OR_NOTICE, f"Interim earn-out report ({label})",
             f"Buyer delivers Gross Profit for {label} to Seller.", "Buyer",
             Timing(anchor=A.FIXED_DATE, fixed_date=quarter_end, offset_days=30), "1.03(a)",
             "Not later than thirty (30) days after the close of each calendar quarter during the Earnout Period "
             "(e.g., December 31, 2024, March 31, 2025, etc.), Buyer shall cause to be prepared and delivered to "
             "Seller its good faith calculation of (i) the Gross Profit of the Company for the three months in "
             "such calendar quarter",
             Terms(metric="Gross Profit"), beneficiary="Seller")


CLIMB = DealExtraction(
    deal_name="Climb / Douglas Stewart (DSS)",
    agreement_title="Membership Interest Purchase Agreement",
    buyer="Climb Global Solutions DSS, LLC",
    seller="The Douglas Stewart Company, Inc.",
    target="Douglas Stewart Company education business (Florida LLC)",
    signing_date=date(2024, 7, 31),
    closing_date=date(2024, 7, 31),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=20_256_600,
    governing_law="Delaware",
    obligations=[
        O("ppa-statement", C.PURCHASE_PRICE_ADJUSTMENT, "Closing BS Differential due",
          "Buyer delivers its calculation of Cash-Like Items less Debt-Like Items at closing.", "Buyer",
          Timing(anchor=A.CLOSING, offset_days=60), "1.02(d)(i)",
          "As promptly as possible, but in any event within sixty (60) days after the Closing Date, Buyer will "
          "deliver to Seller its good faith calculations of the amount by which the Cash-Like Items of the "
          "Business as of the Calculation Time is greater or less than the Debt-Like Items of the Business as of "
          "the Calculation Time",
          consequence="Seller's estimate of each item becomes final, binding and non-appealable."),
        O("ppa-objection", C.PURCHASE_PRICE_ADJUSTMENT, "Objections Statement deadline",
          "Seller has 30 days after delivery to object, or Buyer's figure becomes final.", "Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-statement", offset_days=30), "1.02(d)(ii)",
          "If an Objections Statement is not delivered to Buyer within thirty (30) days after timely delivery of "
          "the Buyer Closing BS Differential, the Buyer Closing BS Differential will be final, binding and "
          "non-appealable by the Parties.",
          consequence="Buyer Closing BS Differential becomes final."),
        O("ppa-payment", C.PURCHASE_PRICE_ADJUSTMENT, "Price adjustment true-up payment",
          "Whichever side owes the difference pays within 5 Business Days of final determination. "
          "Earliest date shown assumes no objection.", "Buyer or Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-objection", offset_days=5, business_days=True),
          "1.02(d)(vi)-(vii)",
          "If the Final Closing Consideration is greater than the Estimated Closing Consideration, then Buyer "
          "shall pay the amount of the excess to Seller by wire transfer of immediately available funds to the "
          "accounts designated by Seller within five (5) Business Days after the determination thereof.",
          confidence=0.85),
        O("ppa-allocation", C.TAX, "Purchase Price Allocation draft due",
          "Buyer delivers its draft Section 1060 allocation within 30 days after the closing consideration is final.",
          "Buyer",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-objection", offset_days=30), "8.05",
          "Buyer shall prepare an initial draft allocation of the Tax Consideration applying the Allocation "
          "Methodology (the \"Purchase Price Allocation\") and deliver a copy thereof to Seller within thirty "
          "(30) days of the finalization of the Final Closing Consideration",
          beneficiary="Seller", confidence=0.85),
        quarter_report("earnout-q4-2024", date(2024, 12, 31), "Q4 2024"),
        quarter_report("earnout-q1-2025", date(2025, 3, 31), "Q1 2025"),
        quarter_report("earnout-q2-2025", date(2025, 6, 30), "Q2 2025"),
        quarter_report("earnout-final-calc", date(2025, 9, 30), "Q3 2025", final=True),
        O("earnout-objection", C.EARNOUT, "Earn-Out Objection Notice deadline",
          "Seller has 30 days from receipt of the Final Earn-Out Calculations to object.", "Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="earnout-final-calc", offset_days=30), "1.03(b)",
          "In the event that Seller does not provide an Earn-Out Objection Notice within such thirty (30) day "
          "period, Seller shall be deemed to have accepted in full the Final Earn-Out Calculations as prepared "
          "by Buyer, which shall be final, binding and conclusive for all purposes hereunder.",
          consequence="Buyer's calculation is deemed accepted."),
        O("earnout-payment", C.EARNOUT, "Earn-Out Payment (if earned)",
          "Tiered payment of $2.27M to $4.21M based on 12-month Gross Profit to Sep 30, 2025 (thresholds "
          "redacted in the filing). Earliest date shown assumes no objection.", "Buyer",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="earnout-objection", offset_days=10, business_days=True),
          "1.03(d)",
          "If the amount of the Earn-Out Payment, as finally determined in accordance with this Section 1.03 "
          "(such final determination date, the \"Earn-Out Determination Date\"), is greater than zero, then "
          "within ten (10) Business Days following the Earn-Out Determination Date, Buyer shall deliver to Seller",
          Terms(max_amount_usd=4_212_000, metric="Gross Profit",
                notes="Tiers: $2,268,000 / $2,754,000 / $3,240,000 / $3,726,000 / $4,212,000. Subject to set-off (7.05(a))."),
          beneficiary="Seller", confidence=0.85),
        O("contingency-final-calc", C.ESCROW_RELEASE, "Final Cash to EBITDA calculation due",
          "Buyer delivers the final Cash Balance minus EBITDA calculation for the 12-month Contingency Period, "
          "which decides who gets the $650K Contingency Escrow.", "Buyer",
          Timing(anchor=A.FIXED_DATE, fixed_date=date(2025, 7, 31), offset_days=30), "1.04(c)",
          "Not later than thirty (30) days after each of October 31, 2024, January 31, 2025, April 30, 2025 and "
          "July 31, 2025, Buyer shall cause to be prepared and delivered to Seller its good faith calculation of",
          Terms(amount_usd=650_000, metric="Cash Balance minus EBITDA"), beneficiary="Seller", confidence=0.9),
        O("contingency-objection", C.ESCROW_RELEASE, "Cash to EBITDA objection deadline",
          "Seller has 30 days after receipt of the final calculation to object.", "Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="contingency-final-calc", offset_days=30), "1.04(d)",
          "If Seller disagrees in whole or in part with the Final Buyer Cash to EBITDA Calculations, then within "
          "thirty (30) days after its receipt thereof, Seller shall notify Buyer of such disagreement in writing",
          confidence=0.9),
        O("contingency-release", C.ESCROW_RELEASE, "Contingency Escrow release",
          "Joint instructions to the Escrow Agent: all, part or none of the $650K to Seller depending on the "
          "Cash to EBITDA Differential (thresholds redacted). Earliest date shown assumes no objection.",
          "Buyer and Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="contingency-objection", offset_days=5, business_days=True),
          "1.04(a)",
          "then Buyer and Seller shall execute and deliver joint written instructions to the Escrow Agent within "
          "five (5) Business Days to pay to Seller all of the Contingency Escrow Amount.",
          Terms(max_amount_usd=650_000), beneficiary="Seller or Buyer", confidence=0.8),
        O("indemnity-escrow-release", C.ESCROW_RELEASE, "Indemnity escrow release",
          "$686,231 Indemnity Escrow goes to Seller on the General Survival Date, less pending claims.",
          "Escrow Agent", Timing(anchor=A.CLOSING, offset_months=18), "1.07",
          "In accordance with the Escrow Agreement, on the General Survival Date, the Escrow Agent shall "
          "distribute to Seller the balance of the Escrow Amount, if any (the \"Remaining Amount\") less the "
          "aggregate dollar amount of any bona fide claim or claims for indemnification",
          Terms(amount_usd=686_231), beneficiary="Seller",
          consequence="Unclaimed escrow is released to Seller."),
        O("survival-general", C.INDEMNITY_SURVIVAL, "General reps survival ends",
          "Last day for Buyer to bring claims on non-fundamental reps.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=18), "7.04(a)(i)",
          "shall survive the Closing and shall continue in full force and effect until the date that is eighteen "
          "(18) months immediately following the Closing Date",
          Terms(duration_months=18, threshold_usd=202_566, max_amount_usd=2_025_660,
                notes="$202,566 tipping basket; $2,025,660 cap; $10,000 de minimis."),
          consequence="Claims for breach of general reps are barred."),
        O("survival-fundamental", C.INDEMNITY_SURVIVAL, "Fundamental reps survival ends",
          "Last day for claims on Fundamental Representations.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=60), "7.04(a)(ii)",
          "shall survive the Closing and shall continue in full force and effect until the date that is sixty "
          "(60) months immediately following the Closing Date",
          Terms(duration_months=60)),
        O("survival-tax", C.INDEMNITY_SURVIVAL, "Statutory reps survival ends",
          "Survive until 60 days after the applicable statute of limitations expires.", "Buyer",
          Timing(anchor=A.EVENT, event_description="60 days after expiry of the applicable statute of limitations",
                 offset_days=60), "7.04(a)(iii)",
          "shall survive the Closing continue and remain in full force and effect until the date that is sixty "
          "(60) days after the expiration of the applicable statute of limitations",
          confidence=0.85),
        O("claim-response", C.INDEMNITY_CLAIM_PROCEDURE, "Claim Notice response window",
          "Indemnifying Person has 30 days after receiving an Indemnification Claim Notice to admit or dispute it.",
          "Indemnifying Person",
          Timing(anchor=A.EVENT, event_description="30 days after receipt of each Indemnification Claim Notice",
                 offset_days=30), "7.03",
          "The Indemnifying Person shall, within thirty (30) days after his, her or its receipt of an "
          "Indemnification Claim Notice, notify the Indemnified Person in writing as to whether the Indemnifying "
          "Person admits or disputes the claim described in the notice.",
          consequence="Failure to respond is treated as admitting the claim."),
        O("noncompete", C.RESTRICTIVE_COVENANT, "Seller non-compete expires",
          "Seller and the Shareholders may not compete in the Restricted Territory until this date.",
          "Seller and Shareholders", Timing(anchor=A.CLOSING, offset_months=36), "6.03(a)",
          "Neither Seller nor the Shareholders shall, during the period ending three (3) years after the Closing "
          "Date, directly or indirectly, own, manage, operate, join, control, finance or participate in",
          Terms(duration_months=36), beneficiary="Buyer"),
        O("nonsolicit", C.RESTRICTIVE_COVENANT, "Customer/supplier non-solicit expires",
          "Seller and the Shareholders may not solicit customers, vendors or suppliers away until this date.",
          "Seller and Shareholders", Timing(anchor=A.CLOSING, offset_months=36), "6.03(b)",
          "Neither Seller nor the Shareholders shall, during the period ending three (3) years after the Closing "
          "Date, either directly or indirectly, (i) induce, attempt to induce, solicit, attempt to solicit",
          Terms(duration_months=36), beneficiary="Buyer"),
        O("dno-indemnity", C.INSURANCE, "D&O exculpation provisions locked",
          "Buyer may not amend the Company's exculpation and indemnification provisions for pre-closing D&Os.",
          "Buyer", Timing(anchor=A.CLOSING, offset_months=72), "6.08(b)",
          "For a period of six (6) years after the Closing, Buyer shall not, and shall not permit the Company to, "
          "amend, repeal or otherwise modify any provision in the Company's Organizational Documents relating to "
          "the exculpation or indemnification",
          Terms(duration_months=72), beneficiary="Former directors and officers"),
        O("tax-refunds", C.TAX, "Pass through pre-closing tax refunds",
          "Buyer pays any pre-closing Refund (net of taxes and costs) to Seller within 30 days of receipt.",
          "Buyer",
          Timing(anchor=A.EVENT, event_description="30 days after receipt of each pre-closing tax Refund",
                 offset_days=30), "8.07",
          "If any Refund is received by Buyer or the Company, Buyer shall pay to Seller an amount equal to such "
          "Refund",
          beneficiary="Seller"),
    ],
)


def sterling_earnout(prefix, title, year, section, description, terms, quote_section="1.8(e)"):
    return [
        O(f"{prefix}-statement", C.EARNOUT, f"{title}: FY{year} statement due",
          description, "Purchaser",
          Timing(anchor=A.FIXED_DATE, fixed_date=date(year + 1, 3, 31)), f"{section}, {quote_section}",
          "On or before March 31 of the calendar year following each First Earn-Out Period and the Second "
          "Earn-Out Period, as applicable, Purchaser shall deliver to Sellers' Representative a statement",
          Terms(metric=terms.metric), beneficiary="Seller Parties"),
        O(f"{prefix}-objection", C.EARNOUT, f"{title}: FY{year} objection window closes",
          "Sellers' Representative has 45 days from receipt to object. Assumes delivery on the due date.",
          "Sellers' Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on=f"{prefix}-statement", offset_days=45), "1.8(e)",
          "During the forty-five (45)-day period immediately following receipt of each Earn-Out Period Payment "
          "Statement (each an \"Earn-Out Review Period\"), Sellers' Representative may dispute the calculation of "
          "Operating Income",
          consequence="Purchaser's Operating Income calculation becomes final."),
        O(f"{prefix}-payment", C.EARNOUT, f"{title}: FY{year} payment (if earned)",
          "Payable within 5 Business Days after the amount is final. Earliest date shown assumes no objection.",
          "Purchaser",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on=f"{prefix}-objection", offset_days=5, business_days=True),
          "1.8(f)",
          "Within five (5) Business Days after a First Earn-Out Payment and/or a Second Earn-Out Payment, as "
          "applicable, has been deemed final or is finally determined pursuant to Section 1.8(e)",
          terms, beneficiary="Seller Parties", confidence=0.85),
    ]


STERLING = DealExtraction(
    deal_name="Sterling / CEC Facilities",
    agreement_title="Asset Purchase Agreement",
    buyer="CEC Facilities, LLC (Sterling Infrastructure, Inc.)",
    seller="CEC Facilities Group, LLC and MCEC, LLC",
    target="CEC Facilities Group business",
    signing_date=date(2025, 6, 16),
    # Not in the agreement: Sterling's Sep 2, 2025 press release (8-K Ex. 99.1) says the deal has closed.
    closing_date=date(2025, 9, 2),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=505_000_000,
    governing_law="Delaware",
    obligations=[
        O("ppa-notice", C.PURCHASE_PRICE_ADJUSTMENT, "Adjustment Notice due",
          "Purchaser delivers closing balance sheet and its calculation of cash, debt, expenses, working "
          "capital and retention items.", "Purchaser",
          Timing(anchor=A.CLOSING, offset_days=120), "1.7(a)",
          "No later than one hundred and twenty (120) days after the Closing Date, Purchaser shall prepare and "
          "deliver to the Sellers' Representative written notice in the same form as the Closing Cash Payment "
          "Statement (the \"Adjustment Notice\")",
          Terms(notes="Working capital adjusts only outside a 90%-110% collar, capped at 10% of target."),
          confidence=0.85),
        O("ppa-response", C.PURCHASE_PRICE_ADJUSTMENT, "Dispute Notice deadline",
          "Sellers' Representative must agree or dispute within 60 days of delivery.", "Sellers' Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-notice", offset_days=60), "1.7(b)-(c)",
          "If the Sellers' Representative fails to take either of the foregoing actions within sixty (60) days "
          "after delivery of the Adjustment Notice, then the Seller Parties will be deemed to have irrevocably "
          "accepted Purchaser's calculation of the Adjustment Amount",
          consequence="Purchaser's Adjustment Amount is deemed accepted."),
        O("ppa-settlement", C.ESCROW_RELEASE, "Adjustment escrow release and true-up",
          "Joint instructions on the $2.63M Adjustment Escrow and any top-up payment, within 5 Business Days "
          "of final determination. Earliest date shown assumes no dispute.", "Purchaser and Sellers' Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-response", offset_days=5, business_days=True),
          "1.7(g)-(h)",
          "Purchaser shall, no later than five (5) Business Days after such determination, deliver or cause to be "
          "delivered the amount of such Adjustment Amount by wire transfer of immediately available funds",
          Terms(max_amount_usd=2_633_229.55), confidence=0.85),
        *sterling_earnout(
            "earnout-first", "First earn-out", 2026, "1.8(a)",
            "One-time $30M if Operating Income for a calendar year beats the target (redacted). Tested every "
            "year from 2026 until earned; FY2026 shown.",
            Terms(amount_usd=30_000_000, metric="Operating Income",
                  notes="One-time; repeats annually from FY2026 until earned. Aggregate earn-out cap $80M (1.8(c))."),
        ),
        *sterling_earnout(
            "earnout-second", "Second earn-out", 2029, "1.8(b)",
            "Up to $50M for calendar 2029 Operating Income, interpolated between Tier 1 and Tier 2 targets.",
            Terms(max_amount_usd=50_000_000, metric="Operating Income",
                  notes="Linear between Tier 1 and Tier 2 targets. Aggregate earn-out cap $80M (1.8(c))."),
        ),
        O("escrow-first-release", C.ESCROW_RELEASE, "Indemnity escrow: first release (50%)",
          "50% of the remaining $11.26M Indemnity Escrow to Sellers, less unresolved claims asserted by the "
          "12-month anniversary.", "Purchaser and Sellers' Representative",
          Timing(anchor=A.CLOSING, offset_months=12, offset_days=2, business_days=True), "7.14(a)",
          "On the second (2nd) Business Day following the twelve (12) month anniversary of the Closing Date, "
          "Purchaser and the Sellers' Representative shall deliver to the Escrow Agent joint written instructions",
          Terms(max_amount_usd=5_631_250, notes="Indemnity Escrow = $10M + $1,262,500 Seller R&W retention."),
          beneficiary="Seller Parties"),
        O("escrow-final-release", C.ESCROW_RELEASE, "Indemnity escrow: final release",
          "Remaining Indemnity Escrow to Sellers, less unresolved claims asserted by the 24-month anniversary.",
          "Purchaser and Sellers' Representative",
          Timing(anchor=A.CLOSING, offset_months=24, offset_days=2, business_days=True), "7.14(b)",
          "On the second (2nd) Business Day following the twenty four (24) month anniversary of the Closing "
          "Date, Purchaser and the Sellers' Representative shall deliver to the Escrow Agent joint written "
          "instructions",
          beneficiary="Seller Parties", consequence="Unclaimed escrow is released to Sellers."),
        O("survival-general", C.INDEMNITY_SURVIVAL, "General reps survival ends",
          "Last day for claims on non-fundamental reps (both sides). R&W insurance policy sits behind the escrow.",
          "Purchaser", Timing(anchor=A.CLOSING, offset_months=12), "7.1(a)",
          "the representations and warranties of the Seller Parties and the Ownership Group Members contained in "
          "this Agreement and in any certificate delivered pursuant hereto (other than the Fundamental "
          "Representations) shall survive the Closing for a period of twelve (12) months from the Closing Date",
          Terms(duration_months=12), consequence="Claims for breach of general reps are barred."),
        O("survival-fundamental", C.INDEMNITY_SURVIVAL, "Fundamental reps survival ends",
          "Last day for claims on Fundamental Representations other than taxes.", "Purchaser",
          Timing(anchor=A.CLOSING, offset_months=48), "7.1(c)",
          "the Fundamental Representations (other than the representations and warranties in Section 2.17 "
          "(Taxes)) shall survive the Closing for a period of four (4) years from the Closing Date",
          Terms(duration_months=48)),
        O("survival-tax", C.INDEMNITY_SURVIVAL, "Tax reps survival ends",
          "Last day for claims on the tax representations.", "Purchaser",
          Timing(anchor=A.CLOSING, offset_months=72), "7.1(d)",
          "the representations and warranties in Section 2.17 (Taxes) shall survive the Closing for a period of "
          "six (6) years from the Closing Date",
          Terms(duration_months=72)),
        O("epl-tail", C.INSURANCE, "EPL tail claims period ends",
          "Sellers bought 6-year tail EPL coverage at closing; claims under it must be made by this date.",
          "Seller Parties", Timing(anchor=A.CLOSING, offset_months=72), "6.23(b)",
          "the Seller Parties shall obtain, as of the Closing Date, \"tail\" employment practices liability "
          "insurance policies with a claims period of six (6) years from the Closing Date",
          Terms(duration_months=72), confidence=0.8),
    ],
)

DEALS = [(CLIMB, CLIMB_URL), (STERLING, STERLING_URL)]


def main() -> None:
    tracked = [track(deal, source=url).model_dump(mode="json") for deal, url in DEALS]
    (HERE / "edgar-tracked.json").write_text(json.dumps(tracked, indent=2) + "\n")
    demo = HERE.parent / "demo" / "edgar-data.js"
    demo.write_text("// Generated by samples/edgar_deals.py. Do not edit.\n"
                    f"window.PORTFOLIO = {json.dumps(FUND)};\n"
                    f"window.DEALS = {json.dumps(tracked, indent=2)};\n")
    n = sum(len(d["obligations"]) for d in tracked)
    print(f"{len(tracked)} deals, {n} obligations -> samples/edgar-tracked.json, demo/edgar-data.js")


if __name__ == "__main__":
    main()
