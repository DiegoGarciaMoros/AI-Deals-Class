"""Four more fictional deals so the demo can show a whole fund's docket.

Everything here is invented: the fund, the companies, the clauses and the
outcomes. Brightwater (build_sample.py) is the only deal with a full sample
agreement; these carry just the clauses that create each obligation.
"""

from __future__ import annotations

from datetime import date

from tracker.schema import (
    Anchor as A,
    Category as C,
    DealExtraction,
    Outcome,
    OutcomeStatus as S,
    Terms,
    Timing,
)

from .build_sample import O

FUND = {"name": "Calder Point Capital Fund III", "note": "Fictional fund"}


KEEL = DealExtraction(
    deal_name="Project Keel",
    agreement_title="Membership Interest Purchase Agreement",
    buyer="Keel Acquisition Corp.",
    seller="Keelson Holdings, Inc.",
    target="Keelson Marine Services, LLC",
    signing_date=date(2024, 10, 1),
    closing_date=date(2024, 11, 16),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=85_000_000,
    governing_law="New York",
    obligations=[
        O("escrow-release", C.ESCROW_RELEASE, "Indemnity escrow release",
          "The $8.5M indemnity escrow goes to Seller at the second anniversary, less unresolved claims. File any claim before this date.",
          "Escrow Agent", Timing(anchor=A.CLOSING, offset_months=24), "2.4(b)",
          "On the second anniversary of the Closing Date, the Escrow Agent shall release to Seller the then-remaining "
          "Indemnity Escrow Funds, less the amount of any unresolved claims set forth in Claim Notices delivered prior to such date.",
          Terms(amount_usd=8_500_000, percent_of_price=10.0), beneficiary="Seller",
          consequence="Unclaimed escrow is released to Seller."),
        O("special-escrow", C.ESCROW_RELEASE, "Environmental special escrow",
          "$1.5M stays in escrow until the state agency issues a No Further Action letter for the Norfolk yard.",
          "Escrow Agent", Timing(anchor=A.EVENT, event_description="Receipt of a No Further Action letter for the Norfolk Facility"),
          "2.4(c)",
          "The Special Escrow Funds shall be released to Seller within ten (10) Business Days after Buyer's receipt of a "
          "No Further Action letter with respect to the Norfolk Facility.",
          Terms(amount_usd=1_500_000), beneficiary="Seller"),
        O("survival-general", C.INDEMNITY_SURVIVAL, "General reps survival ends",
          "Last day to bring claims for breach of general representations.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=24), "9.1(a)",
          "The representations and warranties contained in this Agreement shall survive the Closing until the second "
          "anniversary of the Closing Date, other than the Fundamental Representations, which shall survive until the "
          "sixth anniversary of the Closing Date.",
          Terms(duration_months=24), consequence="Claims for breach of general reps are barred."),
        O("survival-fundamental", C.INDEMNITY_SURVIVAL, "Fundamental reps survival ends",
          "Last day to bring claims for breach of Fundamental Representations.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=72), "9.1(a)",
          "The representations and warranties contained in this Agreement shall survive the Closing until the second "
          "anniversary of the Closing Date, other than the Fundamental Representations, which shall survive until the "
          "sixth anniversary of the Closing Date.", Terms(duration_months=72)),
        O("earnout-2025-statement", C.EARNOUT, "FY2025 EBITDA statement due",
          "Buyer delivers FY2025 EBITDA to Seller for the earnout.", "Buyer",
          Timing(anchor=A.FISCAL_YEAR_END, fiscal_year=2025, offset_days=120), "2.6(b)",
          "Within one hundred twenty (120) days after the end of fiscal year 2025, Buyer shall deliver to Seller a "
          "statement of EBITDA for such fiscal year (the \"EBITDA Statement\").",
          Terms(metric="EBITDA", threshold_usd=12_000_000), beneficiary="Seller"),
        O("earnout-2025-review", C.EARNOUT, "FY2025 EBITDA review period ends",
          "Seller has 45 days to object to the EBITDA Statement.", "Seller",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="earnout-2025-statement", offset_days=45), "2.6(c)",
          "Seller shall have forty-five (45) days after delivery of the EBITDA Statement to notify Buyer of any objection.",
          consequence="EBITDA Statement becomes final."),
        O("earnout-2025-payment", C.EARNOUT, "FY2025 earnout payment (if earned)",
          "$7.5M if FY2025 EBITDA is at least $12M.", "Buyer",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="earnout-2025-review", offset_days=30), "2.6(d)",
          "Buyer shall pay the Earnout Payment, if any, within thirty (30) days after the EBITDA Statement becomes final.",
          Terms(amount_usd=7_500_000, metric="EBITDA", threshold_usd=12_000_000), beneficiary="Seller"),
        O("noncompete", C.RESTRICTIVE_COVENANT, "Seller non-compete expires",
          "Seller may not compete in marine services on the East Coast until this date.", "Seller",
          Timing(anchor=A.CLOSING, offset_months=48), "6.7",
          "For a period of four (4) years following the Closing Date, Seller shall not, directly or indirectly, engage "
          "in the Business anywhere on the Atlantic seaboard of the United States.",
          Terms(duration_months=48), beneficiary="Buyer"),
    ],
)
KEEL_OUTCOMES = [
    Outcome(obligation_id="earnout-2025-statement", status=S.SATISFIED, recorded_on=date(2026, 4, 28),
            notes="FY2025 EBITDA $13.4M vs. $12.0M target: earned."),
    Outcome(obligation_id="earnout-2025-review", status=S.SATISFIED, recorded_on=date(2026, 6, 12),
            notes="Review period ran with no objection."),
    Outcome(obligation_id="earnout-2025-payment", status=S.SATISFIED, recorded_on=date(2026, 7, 10),
            amount_usd=7_500_000, notes="Paid by wire."),
]


LANTERN = DealExtraction(
    deal_name="Project Lantern",
    agreement_title="Agreement and Plan of Merger",
    buyer="Harbor Lane Software, Inc.",
    seller="Stockholders of Lanternfish Labs, Inc.",
    target="Lanternfish Labs, Inc.",
    signing_date=date(2026, 6, 2),
    closing_date=date(2026, 6, 30),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=42_000_000,
    governing_law="Delaware",
    obligations=[
        O("ppa-closing-statement", C.PURCHASE_PRICE_ADJUSTMENT, "Closing Statement due",
          "Parent delivers its calculation of closing working capital, cash and debt.", "Parent (Harbor Lane)",
          Timing(anchor=A.CLOSING, offset_days=60), "2.9(a)",
          "Within sixty (60) days following the Closing Date, Parent shall prepare and deliver to the Stockholder "
          "Representative the Closing Statement.",
          consequence="Parent may lose the chance to run the adjustment on its own numbers."),
        O("ppa-objection", C.PURCHASE_PRICE_ADJUSTMENT, "Closing Statement objection window ends",
          "Stockholder Representative has 30 days after delivery to object.", "Stockholder Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-closing-statement", offset_days=30), "2.9(b)",
          "The Stockholder Representative shall have thirty (30) days following delivery of the Closing Statement to "
          "deliver a Notice of Disagreement."),
        O("holdback-release", C.HOLDBACK_RELEASE, "Holdback release",
          "Parent pays the $2.1M holdback to stockholders, less pending claims.", "Parent (Harbor Lane)",
          Timing(anchor=A.CLOSING, offset_months=12), "2.10",
          "On the date that is twelve (12) months after the Closing Date, Parent shall pay to the Paying Agent, for "
          "further distribution to the Stockholders, the Holdback Amount, less any amounts subject to pending claims.",
          Terms(amount_usd=2_100_000, percent_of_price=5.0), beneficiary="Stockholders"),
        O("deferred-payment", C.DEFERRED_PAYMENT, "Deferred consideration payment",
          "$5M fixed deferred payment on the second anniversary.", "Parent (Harbor Lane)",
          Timing(anchor=A.CLOSING, offset_months=24), "2.11",
          "On the second anniversary of the Closing Date, Parent shall pay the Deferred Consideration of $5,000,000 to "
          "the Paying Agent for distribution to the Stockholders.",
          Terms(amount_usd=5_000_000), beneficiary="Stockholders"),
        O("earnout-arr-statement", C.EARNOUT, "ARR earnout statement due",
          "Parent reports ARR at December 31, 2027. $6M is payable if ARR is at least $18M.", "Parent (Harbor Lane)",
          Timing(anchor=A.FISCAL_YEAR_END, fiscal_year=2027, offset_days=75), "2.12",
          "Within seventy-five (75) days after December 31, 2027, Parent shall deliver to the Stockholder "
          "Representative a statement setting forth ARR as of such date.",
          Terms(amount_usd=6_000_000, metric="ARR", threshold_usd=18_000_000), beneficiary="Stockholders",
          confidence=0.82),
        O("nonsolicit", C.RESTRICTIVE_COVENANT, "Founder non-solicit expires",
          "Founders may not solicit Lanternfish customers or employees until this date.", "Founders",
          Timing(anchor=A.CLOSING, offset_months=24), "6.4",
          "For twenty-four (24) months following the Closing, no Founder shall solicit any customer or employee of the "
          "Company.", Terms(duration_months=24), beneficiary="Parent"),
    ],
)


TESSERA = DealExtraction(
    deal_name="Project Tessera (exit)",
    agreement_title="Unit Purchase Agreement",
    buyer="Northgate Health Partners, Inc.",
    seller="Calder Point Capital Fund III, L.P. and other Sellers",
    target="Tessera Health Staffing, LLC",
    signing_date=date(2025, 11, 3),
    closing_date=date(2025, 12, 19),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=210_000_000,
    governing_law="Delaware",
    obligations=[
        O("ppa-closing-statement", C.PURCHASE_PRICE_ADJUSTMENT, "Buyer's Closing Statement due",
          "Buyer delivers its working capital calculation to the Sellers' Representative.", "Buyer",
          Timing(anchor=A.CLOSING, offset_days=90), "2.5(a)",
          "Within ninety (90) days after the Closing Date, Buyer shall deliver to the Sellers' Representative the "
          "Closing Statement.", beneficiary="Sellers"),
        O("ppa-objection", C.PURCHASE_PRICE_ADJUSTMENT, "Our objection deadline",
          "Sellers' Representative (Calder Point) has 45 days to object to Buyer's numbers.", "Sellers' Representative",
          Timing(anchor=A.OTHER_OBLIGATION, depends_on="ppa-closing-statement", offset_days=45), "2.5(b)",
          "The Sellers' Representative shall have forty-five (45) days after receipt of the Closing Statement to "
          "deliver an Objection Notice.", consequence="Buyer's Closing Statement becomes binding on Sellers."),
        O("retention-escrow", C.ESCROW_RELEASE, "Retention escrow release to Sellers",
          "The $1.05M retention escrow (the R&W policy retention) comes back to Sellers, less pending claims.",
          "Escrow Agent", Timing(anchor=A.CLOSING, offset_months=15), "2.3(c)",
          "On the date that is fifteen (15) months after the Closing Date, the Escrow Agent shall release to Sellers the "
          "remaining Retention Escrow Amount, less the amount of any pending claims.",
          Terms(amount_usd=1_050_000, percent_of_price=0.5), beneficiary="Sellers (incl. Calder Point)"),
        O("survival-general", C.INDEMNITY_SURVIVAL, "Buyer's claim window closes",
          "After this date Buyer cannot bring general rep claims against Sellers; the R&W policy covers the rest.",
          "Buyer", Timing(anchor=A.CLOSING, offset_months=15), "8.1",
          "The representations and warranties of the Sellers shall survive the Closing until the date that is fifteen "
          "(15) months after the Closing Date.", Terms(duration_months=15), beneficiary="Sellers"),
        O("claim-response", C.INDEMNITY_CLAIM_PROCEDURE, "Respond to Buyer's claim notice",
          "Buyer's Claim Notice (received 14 Sep 2026) seeks $640K for unpaid pre-closing payroll taxes. Object in "
          "writing or it is deemed accepted.", "Sellers' Representative",
          Timing(anchor=A.FIXED_DATE, fixed_date=date(2026, 10, 14)), "8.4",
          "The Sellers' Representative shall have thirty (30) days after receipt of a Claim Notice to deliver a written "
          "objection thereto, failing which the claim shall be conclusively deemed a liability of the Sellers.",
          Terms(amount_usd=640_000), consequence="Claim is deemed accepted and paid from the retention escrow."),
        O("nonsolicit", C.RESTRICTIVE_COVENANT, "Seller non-solicit expires",
          "Calder Point and its affiliates may not solicit Tessera employees until this date.", "Sellers (incl. Calder Point)",
          Timing(anchor=A.CLOSING, offset_months=24), "6.3",
          "For two (2) years following the Closing Date, no Seller shall, and each Seller shall cause its Affiliates not "
          "to, solicit for employment any Company Employee.", Terms(duration_months=24), beneficiary="Buyer"),
    ],
)
TESSERA_OUTCOMES = [
    Outcome(obligation_id="ppa-closing-statement", status=S.SATISFIED, recorded_on=date(2026, 3, 16),
            notes="Received from Buyer."),
    Outcome(obligation_id="ppa-objection", status=S.WAIVED, recorded_on=date(2026, 4, 30),
            notes="Reviewed with deal team; no objection. Sellers received a $1.1M upward adjustment."),
]


JUNIPER = DealExtraction(
    deal_name="Project Juniper",
    agreement_title="Stock Purchase Agreement",
    buyer="Juniper Holdco, LLC",
    seller="Founders of Juniper Cold Chain Logistics, Inc.",
    target="Juniper Cold Chain Logistics, Inc.",
    signing_date=date(2023, 6, 20),
    closing_date=date(2023, 8, 1),
    fiscal_year_end_month_day="12-31",
    base_purchase_price_usd=140_000_000,
    governing_law="Delaware",
    obligations=[
        O("escrow-release", C.ESCROW_RELEASE, "Indemnity escrow release",
          "$10.5M indemnity escrow to Sellers at 18 months, less pending claims.", "Escrow Agent",
          Timing(anchor=A.CLOSING, offset_months=18), "2.4",
          "Eighteen (18) months after the Closing Date, the Escrow Agent shall release the Indemnity Escrow Amount to "
          "the Sellers, less the amount of any pending claims.",
          Terms(amount_usd=10_500_000, percent_of_price=7.5), beneficiary="Sellers"),
        O("survival-general", C.INDEMNITY_SURVIVAL, "General reps survival ends",
          "Last day to bring general rep claims.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=18), "8.1(a)",
          "The general representations and warranties shall survive the Closing for eighteen (18) months.",
          Terms(duration_months=18)),
        O("survival-fundamental", C.INDEMNITY_SURVIVAL, "Fundamental reps survival ends",
          "Last day to bring claims on title, capitalization and authority.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=60), "8.1(b)",
          "The Fundamental Representations shall survive the Closing for five (5) years.", Terms(duration_months=60)),
        O("earnout-2025-statement", C.EARNOUT, "FY2025 EBITDA statement due",
          "Buyer reports FY2025 EBITDA; $12M is payable if it reaches $20M.", "Buyer",
          Timing(anchor=A.FISCAL_YEAR_END, fiscal_year=2025, offset_days=90), "2.7(b)",
          "Within ninety (90) days after the end of each of fiscal years 2025 and 2026, Buyer shall deliver to the "
          "Sellers' Representative a statement of EBITDA for such fiscal year.",
          Terms(amount_usd=12_000_000, metric="EBITDA", threshold_usd=20_000_000), beneficiary="Sellers"),
        O("earnout-2026-statement", C.EARNOUT, "FY2026 EBITDA statement due",
          "Buyer reports FY2026 EBITDA; $15M is payable if it reaches $22M.", "Buyer",
          Timing(anchor=A.FISCAL_YEAR_END, fiscal_year=2026, offset_days=90), "2.7(b)",
          "Within ninety (90) days after the end of each of fiscal years 2025 and 2026, Buyer shall deliver to the "
          "Sellers' Representative a statement of EBITDA for such fiscal year.",
          Terms(amount_usd=15_000_000, metric="EBITDA", threshold_usd=22_000_000), beneficiary="Sellers"),
        O("noncompete", C.RESTRICTIVE_COVENANT, "Founder non-compete expires",
          "Founders may not compete in cold-chain logistics in North America until this date.", "Founders",
          Timing(anchor=A.CLOSING, offset_months=60), "6.5",
          "For five (5) years after the Closing Date, no Founder shall engage in the cold-chain logistics business in "
          "North America.", Terms(duration_months=60), beneficiary="Buyer"),
        O("dno-tail", C.INSURANCE, "D&O tail: keep in force",
          "Buyer must not cancel the 6-year D&O tail.", "Buyer",
          Timing(anchor=A.CLOSING, offset_months=72), "6.8",
          "For six (6) years after the Closing, Buyer shall not cause the D&O Tail Policy to be cancelled or modified.",
          Terms(duration_months=72), beneficiary="Former directors and officers"),
    ],
)
JUNIPER_OUTCOMES = [
    Outcome(obligation_id="escrow-release", status=S.SATISFIED, recorded_on=date(2025, 2, 3),
            amount_usd=10_500_000, notes="Released in full; no claims pending."),
    Outcome(obligation_id="earnout-2025-statement", status=S.SATISFIED, recorded_on=date(2026, 3, 30),
            notes="FY2025 EBITDA $19.8M vs. $20.0M target: not earned. Sellers did not dispute."),
]

# (deal, outcomes, fund_role)
DEALS = [
    (KEEL, KEEL_OUTCOMES, "buyer"),
    (LANTERN, [], "buyer"),
    (TESSERA, TESSERA_OUTCOMES, "seller"),
    (JUNIPER, JUNIPER_OUTCOMES, "buyer"),
]
