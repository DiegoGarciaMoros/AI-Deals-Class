# Postclose: operating plan

*Working name. Last updated 2026-09-25.*

## Thesis

After a deal closes, the money and the risk are still live: earnouts, escrow
releases, purchase price true-ups, survival deadlines, restrictive covenants.
The terms are in a 100-page agreement. Tracking is done in Excel by whoever
remembers. Missing a date costs real money: an indemnity claim filed a day late
is barred, and an unclaimed escrow is released.

Postclose reads the signed agreement, turns every post-closing obligation into
a dated, sourced calendar item, and records what actually happened.

**First buyers:** PE funds (deal team, portfolio operations, fund GC) and
corporate development or legal teams at serial acquirers. These are clients of
law firms, not law firms, which keeps the conflict risk with a future employer
low.

**Why now:** AI models can now read long agreements reliably enough for the
job, as long as a lawyer can check every item against its source clause.

## Where the moat comes from (in order of certainty)

1. **Switching costs.** Once live deadlines are in Postclose, leaving is risky.
2. **Accuracy from corrections.** Every user fix becomes a test case.
3. **Deal-term and outcome benchmarks.** Requires scale and a data-rights
   clause. Built into the product from day one: structured terms, outcome
   capture, and an anonymized-data clause with an opt-out.

## The next two weeks

| # | Owner | Task | Done when |
|---|---|---|---|
| 1 | Diego | Read offer letter and firm policies on outside activities and IP | Know whether approval is needed and what it covers |
| 2 | Diego | Allow `sec.gov` and `efts.sec.gov` in this environment's network settings | `python -m tracker.fetch_edgar` runs |
| 3 | Diego | Add an Anthropic API key to the environment | `python -m tracker.extract` runs |
| 4 | Claude | Pull 20 EDGAR agreements, extract, hand-check 5 against the sample's gold standard | Accuracy numbers per category |
| 5 | Claude | Load real extractions into the demo | Demo shows real public deals |
| 6 | Diego | 8 discovery interviews (see `interviews.md`) | Notes logged in the tracker table |
| 7 | Diego | 2–3 control interviews for option #1 (AI governance) | Notes logged |
| 8 | Both | Decision review | Go / pivot / kill, written down |

## Decision criteria (end of week 2)

**Go** if at least 2 of the 8 target interviewees say they would pilot it on a
live deal, and at least 4 describe losing money or nearly missing a deadline.

**Pivot** to AI governance if those interviews show clearly more pain or budget
than the PE and in-house interviews.

**Rethink** if most people say "our paralegal and Excel handle it fine."

## Days 15–90 (if Go)

- **Weeks 3–5:** Build the pilot version: login, upload a PDF, email reminders, CSV/ICS export. Security basics (encryption, no training on customer data, deletion on request).
- **Weeks 5–8:** 2–3 free pilots on closed deals. Each pilot delivers a checked calendar within 48 hours.
- **Weeks 8–12:** Convert one pilot to paid. Starting price to test: $15k/year per fund or $1,500 per deal.
- **Ongoing:** Weekly review every Monday: pipeline, product, what we learned. Claude drafts, Diego decides.

## Company setup (not yet: only after a Go decision)

- Delaware C-corp via Stripe Atlas or Clerky (~$500) once there is a paying pilot or co-founder
- Business bank account, a domain, and Google Workspace
- Standard terms: MSA, DPA, and the data-rights clause
- 83(b) election within 30 days of founder stock issuance

## Risks we are watching

| Risk | Mitigation |
|---|---|
| Employer conflict or IP claim | Offer letter review first; build only on public data; sell to non-law-firm buyers |
| Extraction error causes a missed deadline | Every item shows its source quote; low-confidence items are flagged; human review before a calendar goes live |
| Customers won't upload confidential agreements | Start with closed deals; encrypt everything; guarantee deletion on request |
| Litera, Ironclad or Harvey adds this | Stay narrow and outcome-focused; their products are broad |
| Market too small | Test willingness to pay early; expand to financing covenants and commercial contracts later |
