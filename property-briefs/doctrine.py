"""Hand-written doctrine for the Doctrinal overview tab: black-letter guides and diagrams.

These are written by hand (not generated) so the core rules are reliable. Each class unit can
have a `guide` (Markdown, shown as the main text) and `diagrams` (Graphviz DOT, drawn in the
browser by st.graphviz_chart). Case citations use [[Case Name]] so the app links them to briefs.
The AI-written unit essays in data/overview.json sit alongside and must not contradict these.
"""

# ---------- diagram helpers ----------

STYLE = ('graph [fontname="Helvetica" fontsize=11 nodesep=0.35 ranksep=0.45 bgcolor="transparent"];\n'
         'node [fontname="Helvetica" fontsize=11 shape=box style="rounded,filled" fillcolor="#f4f4f1" '
         'color="#8a8a85" fontcolor="#1b1a17" margin="0.15,0.07"];\n'
         'edge [fontname="Helvetica" fontsize=10 color="#6b6b66" fontcolor="#3a3a36"];\n')
Q = 'shape=diamond fillcolor="#e8f0fb" color="#2a78d6" style="filled"'      # a question
OUT = 'fillcolor="#e3f2e8" color="#2f8a4f"'                                 # an answer
NO = 'fillcolor="#fbe9e1" color="#d2602a"'                                  # a "no" / loses


def dot(body, rankdir="TB"):
    return f"digraph G {{\nrankdir={rankdir};\n{STYLE}{body}\n}}"


# ---------- 5. The Forms of Ownership ----------

ESTATES_GUIDE = r"""
**In one line:** American law lets owners split ownership over *time* only into a fixed menu of
estates (the *numerus clausus*). Each **present estate** that can end leaves a matching **future
interest** in someone, and the labels matter because different rules (alienability, the Rule
Against Perpetuities, who can sue for waste) attach to each.

#### 1. Present possessory estates

| Estate | Words that create it | Lasts | How it ends | Future interest in grantor (O) | Future interest in a third party (B) |
|---|---|---|---|---|---|
| **Fee simple absolute** | "to A" or "to A and her heirs" | Forever | Never | None | None |
| **Fee tail** (abolished or converted to fee simple in most states) | "to A and the heirs of her body" | Until A's line of descendants runs out | Line ends | Reversion | Remainder |
| **Life estate** | "to A for life" | A's life | A's death | Reversion | Remainder |
| **Life estate *pur autre vie*** | "to A for the life of C" | C's life | C's death | Reversion | Remainder |
| **Fee simple determinable** | "so long as," "while," "during," "until" | Possibly forever | **Automatically** when the event happens | **Possibility of reverter** | (see executory limitation) |
| **Fee simple subject to condition subsequent** | "but if," "provided that," "on condition that" **+** O may re-enter | Possibly forever | Only if **O elects** to re-enter | **Right of entry** (power of termination) | none: only a grantor can hold this |
| **Fee simple subject to executory limitation** | "to A, but if [event], then to B" | Possibly forever | **Automatically**, in favor of B | n/a | **Executory interest** |

*"And her heirs" are **words of limitation**: they describe the estate A gets (a fee simple) and give
A's heirs nothing. Leaseholds (term of years, periodic, at will) are non-freehold estates covered in
the lease units.*

#### 2. Future interests

**Kept by the grantor:** a **reversion** (follows a life estate or other estate that will
certainly end), a **possibility of reverter** (follows a fee simple determinable), and a **right of
entry** (follows a fee simple subject to condition subsequent).

**Created in a third party:**
- A **remainder** waits politely: it can become possessory only when the prior estate ends
  *naturally* (for example, at the life tenant's death). A remainder never follows a fee simple.
  - **Vested** if the taker is born and ascertained **and** there is no condition precedent other
    than the end of the prior estate. Vested remainders may be *indefeasibly vested*, *subject to
    open* (a class like "A's children" that can still grow) or *subject to complete divestment*
    (a condition subsequent can take it away).
  - **Contingent** if the taker is unborn or unascertained, or there is a condition precedent.
- An **executory interest** cuts in: it takes effect by *cutting short* a prior estate or after a
  gap. **Shifting** if it divests a third party, **springing** if it divests the grantor.

**Watch the commas.** "to A for life, then to B **if** B graduates" gives B a *contingent
remainder* (condition precedent). "to A for life, then to B, **but if** B fails to graduate, to C"
gives B a *vested remainder subject to complete divestment* and C a *shifting executory interest*
(condition subsequent).

#### 3. Rules that police the system
- **Rule Against Perpetuities:** "No interest is good unless it must vest, if at all, not later
  than twenty-one years after some life in being at the creation of the interest." It applies to
  contingent remainders, executory interests and class gifts still open; **not** to interests kept
  by the grantor (reversion, possibility of reverter, right of entry) or to vested remainders.
  Classic violation: "to A for life, then to A's children who reach 25" (A could have a child after
  the grant who turns 25 more than 21 years after every life in being). Many states now use
  wait-and-see or the Uniform Statutory Rule (a 90-year period).
- **Destructibility of contingent remainders, the Rule in Shelley's Case, the Doctrine of Worthier
  Title:** feudal-era rules now abolished or narrowed in most states; know them as names.
- **Presumption of fee simple:** modern statutes presume a grantor transfers everything she has
  unless the instrument shows a contrary intent. Clear words of duration ("for life," "until she
  marries") rebut it ([[Williams v. Estate of Williams]]).
- **Interpretation first, then policy:** read the instrument for what the grantor meant, and only
  then ask whether the law allows that interest. Repugnancy is a public-policy limit, not a reading
  tool ([[Charles v. Barzey]]). Courts refuse new, nonstandard estates (*Johnson v. Whiton*).

#### 4. The case in this unit
In [[Williams v. Estate of Williams]] a will left a farm to three daughters "during their lives,"
"not to be sold during their lifetime," with a daughter's interest ending if she married. The
Tennessee Supreme Court held the daughters took **life estates** (each ending at death or
marriage) with survivorship interests in each other's shares, and the testator's **heirs kept a
reversion**, rejecting the lower courts' reading of a fee simple with a void restraint (the
approach of *White v. Brown*).

*Classification note:* an interest that takes effect when a life estate ends naturally is a
remainder; one that cuts the estate short is an executory interest. Whether a sister's interest
is labeled a remainder or an executory interest turns on whether "marriage" ends the estate by
its own terms (limitation) or cuts it short (condition), so explain your label on an exam.

**Exam tip:** Diagram every grant on a timeline: present estate first, then who takes next and
when, then any condition. Name each interest, then run the Rule Against Perpetuities only on
contingent remainders, executory interests and open class gifts.
"""

WASTE_GUIDE = r"""
**In one line:** When ownership is split over time, the present owner must hand the property on
**substantially as received** (waste), and grantors may not cut off the power to sell a fee
simple (restraints on alienation), though they may restrict *use*.

#### 1. Waste: three kinds

| Kind | What it is | Example | Rule |
|---|---|---|---|
| **Affirmative (voluntary)** | An act that permanently injures the future interest | Cutting timber, stripping minerals not already being mined | Liable |
| **Permissive** | Failing to take reasonable care | Letting the roof leak; not paying taxes so the land is lost | Liable |
| **Ameliorative** | A change that *raises* market value but alters the property's character | Tearing down a mansion to build apartments | Traditionally waste ([[Brokaw v. Fairchild]]); allowed where conditions have changed so much the property is useless for its old purpose (*Melms v. Pabst Brewing*); New York and other states now allow it by statute if the remainder isn't harmed |

- In [[Brokaw v. Fairchild]] a life tenant of a Fifth Avenue mansion could not tear it down to
  build a more profitable apartment house: a life tenant gets *use*, not *ownership*, and must
  hand on "my residence," not just valuable land.
- Waste law is a **governance** regime: it steps in because the life tenant and the remainder
  holder can't easily bargain, and each has incentives that hurt the other.

#### 2. Valuing split interests
When property held as a life estate and remainder is sold or condemned, the price is divided by
**present value**: remainder = value ÷ (1 + discount rate)<sup>years of life expectancy</sup>; the
life estate gets the rest. A higher discount rate or a younger life tenant shifts value toward
the life estate.

#### 3. Restraints on alienation
| Type | Form | On a fee simple | On a life estate |
|---|---|---|---|
| **Disabling** | "A may not sell" (any sale is void) | Void | Generally void |
| **Forfeiture** | "If A sells, the land goes to O (or B)" | Generally void | Generally valid |
| **Promissory** | A promises not to sell | Generally void | Generally valid |

- **Partial or reasonable restraints** can survive: limited in time or class of buyer, rights of
  first refusal at market price, restrictions serving a legitimate purpose (common in condos and
  co-ops).
- **Use restrictions are different.** A condition on *how* land is used can create a valid
  defeasible fee even if it makes the land hard to sell. In [[Mountain Brow Lodge No. 82 v. Toscano]]
  the court struck the condition against transfer but kept the condition that the lodge use the
  land, which created a fee simple subject to condition subsequent. The dissent called that a
  distinction without a difference.

**Exam tip:** Ask first whether a clause limits *transfer* (likely void if on a fee) or *use*
(likely a valid defeasible fee), and whether it can be severed from the rest of the grant.
"""

CONCURRENT_GUIDE = r"""
**In one line:** Co-owners each own an undivided share and each may possess the **whole**; the
form of co-ownership decides what happens at death, on transfer and against creditors, and
partition is the exit.

#### 1. The three forms

| | **Tenancy in common** | **Joint tenancy** | **Tenancy by the entirety** |
|---|---|---|---|
| Created by | Default today (presumed) | Clear words: "as joint tenants with right of survivorship" | Married couples only (in states that keep it) |
| Unities required | Possession only | **Time, title, interest, possession** | The four unities **+ marriage** |
| At a co-owner's death | Share passes by will or intestacy | **Survivorship**: the dead tenant's share vanishes; survivors own it all | Survivorship |
| One owner transfers alone? | Yes | Yes, but it **severs** (buyer becomes a tenant in common) | No |
| Creditors of one owner | Can reach that share | Can reach it **before** death; after death it is gone | Generally cannot reach the property (most states) |

**Severance and mortgages.** A conveyance by one joint tenant severs. A **mortgage** by one joint
tenant severs in **title-theory** states but not in **lien-theory** states. In [[Harms v. Sprague]]
(Illinois, lien theory) the mortgage did not sever, so when the mortgaging tenant died the
survivor took the whole property **free of the mortgage**.

#### 2. Rights and duties between co-owners
- Each may use the whole; an occupying co-tenant owes others **no rent** unless there was an
  **ouster**, an agreement, or the occupant collected rent from third parties (which must be shared).
- **Ouster** usually means refusing a co-tenant's demand for access or otherwise excluding them.
  In [[Gillmor v. Gillmor]] a co-tenant out of possession made a clear demand to use land the
  other was using exclusively, and the refusal let her recover for being kept out.
- **Accounting:** co-tenants share carrying costs (taxes, mortgage interest); improvements are
  credited on partition only to the extent they added value.

#### 3. Partition
- Any co-tenant can force partition. **Partition in kind** (physical division) is preferred;
  **partition by sale** only if (1) division in kind is impracticable or inequitable **and**
  (2) a sale would better promote **all** owners' interests ([[Delfino v. Vealencis]], protecting a
  co-tenant who lived and ran a business on the land). Several states now protect inherited
  "heirs property" by statute (Uniform Partition of Heirs Property Act).

#### 4. Marital property
- Common-law states divide property at divorce by **equitable distribution**; community-property
  states treat earnings during marriage as owned equally.
- Professional degrees: most courts say a degree is not property, but the supporting spouse may
  get an **equitable claim** for their contributions ([[Postema v. Postema]], Michigan). New York
  (*O'Brien*) was the outlier treating a license as marital property.

**Exam tip:** Identify the form first (survivorship?), then check for severance (conveyance,
mortgage in a title-theory state), then rights inter se (ouster, accounting), then the exit (partition).
"""

DIAGRAMS = {
    # 5. The Forms of Ownership
    "traditional_forms_of_property": [
        ("Classifying a future interest", dot(f'''
start [label="Who holds the future interest?" {Q}];
o [label="The grantor (O)"]; t [label="A third party (B)"];
start -> o; start -> t;
o1 [label="What present estate\\ndid O give away?" {Q}];
o -> o1;
rev [label="Reversion" {OUT}]; por [label="Possibility of reverter" {OUT}]; roe [label="Right of entry" {OUT}];
o1 -> rev [label="life estate / term"]; o1 -> por [label="fee simple\\ndeterminable"]; o1 -> roe [label="fee simple subject to\\ncondition subsequent"];
t1 [label="Does it wait for the prior estate\\nto end naturally?" {Q}];
t -> t1;
rem [label="Remainder"]; exe [label="Executory interest"];
t1 -> rem [label="yes"]; t1 -> exe [label="no: it cuts the estate\\nshort or follows a gap"];
r1 [label="Taker ascertained AND\\nno condition precedent?" {Q}];
rem -> r1;
vr [label="Vested remainder\\n(indefeasibly / subject to open /\\nsubject to complete divestment)" {OUT}];
cr [label="Contingent remainder" {OUT}];
r1 -> vr [label="yes"]; r1 -> cr [label="no"];
sh [label="Shifting (divests a\\nthird party)" {OUT}]; sp [label="Springing (divests\\nthe grantor)" {OUT}];
exe -> sh; exe -> sp;
'''), "Run every interest through this tree, then apply the Rule Against Perpetuities only to contingent remainders, executory interests and open class gifts."),
        ("Which defeasible fee? Read the words", dot(f'''
q [label="Can the fee end\\nif an event happens?" {Q}];
fsa [label="Fee simple absolute" {OUT}];
q -> fsa [label="no"];
who [label="Who takes if it ends?" {Q}];
q -> who [label="yes"];
auto [label="Ends automatically?\\n\\"so long as / while / until\\"" {Q}];
who -> auto [label="the grantor"];
fsd [label="Fee simple determinable\\n+ possibility of reverter (O)" {OUT}];
fsscs [label="Fee simple subject to\\ncondition subsequent\\n+ right of entry (O must act)" {OUT}];
auto -> fsd [label="yes"]; auto -> fsscs [label="no: \\"but if / provided that\\"\\n+ O may re-enter"];
fsel [label="Fee simple subject to\\nexecutory limitation\\n+ executory interest (B)\\n(always automatic)" {OUT}];
who -> fsel [label="a third party"];
'''), "Ambiguous language is usually read as a fee simple subject to condition subsequent, which avoids automatic forfeiture."),
        ("Williams v. Estate of Williams: who holds what", dot(f'''
o [label="G.A. Williams (will, 1944)"];
d [label="Each daughter: life estate in 1/3\\nends at her death or marriage" {OUT}];
s [label="Surviving unmarried sisters:\\ntake a departing sister's share"];
h [label="G.A.'s heirs: reversion\\n(possession after the last\\nlife estate ends)" {OUT}];
o -> d -> s -> h;
''', "LR"), "The court found a clear intent to give support for life, which rebutted the statutory presumption of a fee simple."),
    ],
    "waste_restraints_on_alienation": [
        ("Is it waste?", dot(f'''
q1 [label="Did the present owner (life tenant,\\ntenant for years) change or neglect\\nthe property?" {Q}];
ok [label="No waste" {OUT}];
q1 -> ok [label="no"];
q2 [label="Act or omission?" {Q}];
q1 -> q2 [label="yes"];
perm [label="Permissive waste\\n(failure of reasonable care)" {NO}];
q2 -> perm [label="omission"];
q3 [label="Did it lower the value of the\\nfuture interest?" {Q}];
q2 -> q3 [label="act"];
aff [label="Affirmative waste" {NO}];
q3 -> aff [label="yes"];
q4 [label="Ameliorative: value went up.\\nHave conditions changed so the property\\nis useless for its old purpose?" {Q}];
q3 -> q4 [label="no"];
brok [label="Brokaw: still waste\\n(must hand on the thing itself)" {NO}];
melms [label="Melms / modern statutes:\\npermitted" {OUT}];
q4 -> brok [label="no"]; q4 -> melms [label="yes"];
'''), None),
        ("Transfer limit or use limit?", dot(f'''
c [label="Clause in a grant of a fee simple" {Q}];
tr [label="Limits WHO can own /\\nforbids sale"]; us [label="Limits HOW the land\\nis used"];
c -> tr; c -> us;
v [label="Restraint on alienation:\\nvoid unless partial and reasonable" {NO}];
d [label="Valid defeasible fee\\n(e.g., FSSCS in Mountain Brow)" {OUT}];
tr -> v; us -> d;
'''), None),
    ],
    "concurrent_owners": [
        ("Joint tenancy: survivorship and severance", dot(f'''
jt [label="A and B: joint tenants"];
q [label="Did A convey or (in a title-theory\\nstate) mortgage her share?" {Q}];
jt -> q;
sev [label="Severed: buyer (or A) and B are\\ntenants in common" {NO}];
q -> sev [label="yes"];
die [label="A dies"];
q -> die [label="no (incl. a mortgage in a\\nlien-theory state: Harms)"];
surv [label="B owns everything;\\nA's lender's lien is gone" {OUT}];
die -> surv;
'''), "Creditors of a joint tenant must act before that tenant dies."),
        ("Ending co-ownership: partition", dot(f'''
p [label="A co-tenant sues to partition"];
q1 [label="Is physical division practicable\\nand fair?" {Q}];
p -> q1;
kind [label="Partition in kind\\n(preferred)" {OUT}];
q1 -> kind [label="yes"];
q2 [label="Would a sale better promote\\nALL owners' interests?" {Q}];
q1 -> q2 [label="no"];
sale [label="Partition by sale" {OUT}];
q2 -> sale [label="yes"]; q2 -> kind [label="no (Delfino)"];
'''), None),
    ],
    # 1. What is Property?
    "nuisance": [
        ("Trespass or nuisance?", dot(f'''
q [label="Did a tangible thing physically\\nenter the land (directly)?" {Q}];
tr [label="Trespass: liability without proof of harm;\\nnominal damages; injunction\\n(Jacque, Adams)" {OUT}];
q -> tr [label="yes"];
q2 [label="Substantial interference with\\nuse and enjoyment?" {Q}];
q -> q2 [label="no: dust, noise, odor,\\nvibration, light"];
none [label="No claim" {NO}];
q2 -> none [label="no"];
q3 [label="Unreasonable? (gravity of harm vs.\\nutility; locality; who came first)" {Q}];
q2 -> q3 [label="yes"];
nu [label="Private nuisance" {OUT}];
q3 -> nu [label="yes"]; q3 -> none [label="no (Hendricks)"];
'''), "Physical damage to property usually counts as substantial harm (Jost)."),
        ("Calabresi & Melamed's four remedies", dot(f'''
r1 [label="Rule 1: plaintiff wins an injunction\\n(property rule for the neighbor)\\nCampbell v. Seaman" {OUT}];
r2 [label="Rule 2: plaintiff wins damages only\\n(liability rule for the neighbor)\\nBoomer v. Atlantic Cement" {OUT}];
r3 [label="Rule 3: no nuisance; defendant may continue\\n(property rule for the polluter)\\nHendricks v. Stalnaker" {OUT}];
r4 [label="Rule 4: injunction, but plaintiff pays\\nthe defendant's costs\\nSpur Industries v. Del Webb" {OUT}];
{{rank=same; r1; r2}} {{rank=same; r3; r4}}
r1 -> r3 [style=invis]; r2 -> r4 [style=invis];
'''), "Who holds the entitlement, and is it protected by a property rule (consent needed) or a liability rule (pay a court-set price)?"),
    ],
    "privilege_first_possession": [
        ("Who owns the wild animal?", dot(f'''
q [label="Has the pursuer taken possession?" {Q}];
yes [label="Owns it (Pierson v. Post):\\ncapture, mortal wounding,\\nor certain control" {OUT}];
q -> yes [label="yes"];
q2 [label="Is there an established industry\\ncustom that fits the hunt?" {Q}];
q -> q2 [label="no: mere pursuit"];
cus [label="Custom can define possession\\n(Ghen v. Rich: first iron)" {OUT}];
q2 -> cus [label="yes"];
nope [label="No property right\\n(but malicious interference\\nmay be actionable: Keeble)" {NO}];
q2 -> nope [label="no"];
'''), "Animals still on the land belong to the landowner (ratione soli), and things embedded in land go with the land (Goddard v. Winchell)."),
    ],
    # 2. Acquisition and Claim Scope
    "prior_possession_finders": [
        ("The ladder of title", dot(f'''
o [label="True owner" {OUT}];
f [label="Prior possessor / first finder\\n(Armory v. Delamirie; Clark v. Maloney)"];
w [label="Later finder or wrongdoer\\n(Anderson v. Gouldberg)" {NO}];
o -> f [label="beats"]; f -> w [label="beats"];
'''), "Title is relative: a defendant can't defeat a prior possessor by pointing to a stranger's better title (no jus tertii defense)."),
        ("Lost, mislaid or abandoned?", dot(f'''
q [label="How did the owner part with it?" {Q}];
lost [label="Lost (accidentally):\\nfinder usually wins,\\nesp. if landowner never\\npossessed the place (Hannah v. Peel)" {OUT}];
mis [label="Mislaid (set down on purpose,\\nthen forgotten): owner of the\\npremises holds it for the true owner" {OUT}];
ab [label="Abandoned (intent to give up):\\nfirst possessor takes" {OUT}];
emb [label="Embedded in the land:\\nlandowner wins" {OUT}];
q -> lost; q -> mis; q -> ab; q -> emb;
'''), None),
    ],
    "accession": [
        ("Combined or transformed goods", dot(f'''
q [label="Can the combination be undone\\nat reasonable cost?" {Q}];
sep [label="Separate; wrongdoer pays\\nthe cost" {OUT}];
q -> sep [label="yes"];
q2 [label="Did the improver act\\nin good faith?" {Q}];
q -> q2 [label="no"];
bad [label="Original owner takes all;\\nno credit for added value" {NO}];
q2 -> bad [label="no"];
rel [label="Relative value: if the improver added\\nmost of the value (Wetherbee: ~28x),\\nimprover keeps it and pays for the raw material" {OUT}];
q2 -> rel [label="yes"];
'''), None),
        ("Is it a fixture?", dot(f'''
a [label="Annexation: how firmly\\nattached? damage on removal?"];
b [label="Adaptation: fitted to this\\nproperty's use?"];
c [label="Intent, judged objectively:\\nwhat would a buyer reasonably\\nexpect? (Strain v. Green)"];
f [label="Fixture: passes with the land" {OUT}];
a -> f; b -> f; c -> f;
'''), "A seller's secret intent to remove doesn't count."),
    ],
    "adverse_possession": [
        ("Adverse possession checklist", dot(f'''
el [label="Actual + open and notorious\\n+ exclusive + continuous\\n+ adverse/hostile\\nfor the statutory period"];
cr [label="Claim of right: which test?" {Q}];
el -> cr;
obj [label="Objective (majority): no permission\\n= adverse; state of mind irrelevant" {OUT}];
gf [label="Good faith: honest mistake required\\n(Carpenter v. Ruperto, Iowa)" {OUT}];
bf [label="Aggressive trespass (minority):\\nmust know it's not yours" {OUT}];
cr -> obj; cr -> gf; cr -> bf;
tk [label="Short on time? Tack predecessors' years\\nif in privity (Howard v. Kunto: deed\\ndescribed the wrong lot, still privity)"];
el -> tk [style=dashed];
'''), "Continuity is judged by how an ordinary owner uses that kind of land (summer use of a summer home counts). Chattels: limitations rules differ (Songbyrd)."),
    ],
    # 3. Values Subject to Ownership
    "communities_customs_public_rights_water": [
        ("Water rights by source", dot(f'''
w [label="What kind of water?" {Q}];
s [label="Stream or lake"]; g [label="Groundwater"]; d [label="Diffuse surface water"];
w -> s; w -> g; w -> d;
rip [label="Riparian (East): reasonable use\\nby owners along the bank\\n(Evans v. Merriweather)" {OUT}];
pa [label="Prior appropriation (West):\\nfirst in time, first in right,\\nfor beneficial use (Coffin)" {OUT}];
s -> rip; s -> pa;
gw [label="Absolute ownership (old English)\\nReasonable use (Higday)\\nCorrelative rights (California)\\nPrior appropriation" {OUT}];
g -> gw;
ce [label="Common enemy rule, moving\\ntoward reasonable use" {OUT}];
d -> ce;
'''), None),
    ],
    # 4. Owner Sovereignty and Its Limits
    "criminal_law_self_help_common_law_defenses": [
        ("Self-help and necessity", dot(f'''
sh [label="Owner using self-help"];
land [label="Retaking leased real property:\\ngo to court unless the tenant\\nabandoned or surrendered (Berg v. Wiley)" {NO}];
car [label="Repossessing collateral:\\nallowed without breach of the peace;\\nstop if the debtor objects\\n(Williams v. Ford Motor Credit)" {OUT}];
sh -> land; sh -> car;
nec [label="Entry by necessity"];
pub [label="Public necessity: complete\\nprivilege, no compensation"];
pri [label="Private necessity: owner can't expel\\n(Ploof), but entrant pays for damage\\n(Vincent v. Lake Erie)"];
nec -> pub; nec -> pri;
'''), None),
    ],
    "equity_abandonment_destruction": [
        ("Encroachment: injunction or damages?", dot(f'''
q [label="Did the builder encroach\\nknowingly?" {Q}];
inj [label="Injunction: tear it down" {NO}];
q -> inj [label="yes"];
q2 [label="Tiny, innocent encroachment and\\nremoval cost wildly out of\\nproportion to the harm?" {Q}];
q -> q2 [label="no"];
dmg [label="Damages only\\n(Golden Press)" {OUT}];
strictview [label="Strict view: injunction anyway\\n(Pile v. Pedrick)" {NO}];
q2 -> dmg [label="yes (balancing)"]; q2 -> strictview [label="no / strict court"];
'''), "eBay: a permanent injunction requires irreparable injury, inadequate legal remedy, balance of hardships, and no disservice to the public interest."),
    ],
    "licenses_bailments": [
        ("License or bailment?", dot(f'''
q [label="Did the owner hand over\\npossession and control?" {Q}];
lic [label="License / space rental:\\nno duty to guard (open lot;\\nWood v. Leadbitter: revocable)" {NO}];
q -> lic [label="no"];
bail [label="Bailment: bailee presumed negligent\\nif it can't return the goods\\n(Allen v. Hyatt: enclosed, attended garage)" {OUT}];
q -> bail [label="yes"];
mis [label="Misdelivery is strict liability\\n(Cowen v. Pressprich)"];
bail -> mis;
'''), "Duty of care (Story): sole benefit of bailor = slight care; sole benefit of bailee = great care; mutual benefit = ordinary care."),
    ],
    # 6. Entity Property
    "leases_traditional_rules": [
        ("Landlord's duties at a glance", dot(f'''
l [label="Landlord's duties"];
del [label="Deliver possession\\n(English rule: actual;\\nAmerican rule: legal right only)"];
qe [label="Covenant of quiet enjoyment"];
ce [label="Constructive eviction: substantial\\ninterference + tenant leaves\\n(Blackett v. Olanoff: landlord-controlled noise)" {OUT}];
l -> del; l -> qe; qe -> ce;
ab [label="Tenant abandons"];
sur [label="Landlord re-lets for its own account:\\nacceptance of surrender ends the lease\\n(Gotlieb v. Taco Bell)" {NO}];
mit [label="Duty to mitigate (modern majority):\\nre-let for the tenant's account" {OUT}];
ab -> sur; ab -> mit;
'''), None),
    ],
    "leases_reforms_transfers": [
        ("Habitability and transfers", dot(f'''
iwh [label="Implied warranty of habitability\\n(Javins): housing code sets the floor;\\nnot waivable; rent obligation is dependent" {OUT}];
t [label="Tenant transfers"];
as [label="Assignment: whole remaining term;\\nassignee in privity of estate with landlord"];
sub [label="Sublease: part of the term;\\nno privity between landlord and subtenant"];
t -> as; t -> sub;
dep [label="Dependent covenants: landlord's breach of\\na covenant going to the whole deal (exclusive\\nuse clause) lets the tenant rescind\\n(Medico-Dental)" {OUT}];
j [label="Label follows substance: a transfer of the\\nwhole term is an assignment even if called\\na sublease (Jaber v. Miller)"];
as -> j [style=dashed];
m [label="A covenant binds later owners only if it\\ntouches and concerns the land (deposit refund\\ndid not: Mullendore Theatres)"];
t -> m [style=dashed];
'''), None),
    ],
    # 8. Title Records and the Transfer of Property
    "title_transfer_land_transactions_good_faith_purchasers_recording": [
        ("Recording acts: does the later buyer win?", dot(f'''
q [label="Is the later buyer a purchaser for value\\nwithout notice of the earlier deed?" {Q}];
lose [label="First in time wins" {NO}];
q -> lose [label="no"];
t [label="Which statute?" {Q}];
q -> t [label="yes"];
n [label="Notice statute:\\nlater buyer wins" {OUT}];
rn [label="Race-notice: later buyer wins\\nonly if she records first" {OUT}];
r [label="Race statute: whoever records\\nfirst wins (notice irrelevant)" {OUT}];
t -> n; t -> rn; t -> r;
'''), "Personal property: a thief passes no title, but a voidable title can pass good title to a good-faith purchaser (UCC 2-403)."),
    ],
    # 9. The Law of Neighbors
    "easements": [
        ("How easements are created", dot(f'''
e [label="Easement created by…"];
ex [label="Express grant or reservation\\n(writing; Statute of Frauds)"];
ip [label="Implication from prior use\\n(quasi-easement, reasonably necessary)"];
ne [label="Necessity\\n(landlocked parcel after severance)"];
pr [label="Prescription\\n(adverse use for the period)"];
es [label="Estoppel / irrevocable license\\n(reliance: Holbrook v. Taylor)"];
e -> ex; e -> ip; e -> ne; e -> pr; e -> es;
no [label="No easement of light and air\\nwithout a grant (Fontainebleau)" {NO}];
'''), "Necessity and implication must exist when a common owner splits the land; owners who landlock themselves get none (Schwab v. Timmons). A prescriptive easement holder owes the servient owner nothing (Warsaw v. Chicago Metallic Ceilings)."),
    ],
    "covenants": [
        ("Will a promise about land bind a later owner?", dot(f'''
q [label="Remedy sought?" {Q}];
rc [label="Damages: real covenant\\nwriting + intent + touch and concern\\n+ horizontal and vertical privity\\n(Neponsit)"];
es [label="Injunction: equitable servitude\\nintent + touch and concern + notice\\n(privity not needed; implied from a\\ncommon scheme: Sanborn v. McLean)"];
q -> rc; q -> es;
sk [label="Never enforceable if it requires\\nillegal discrimination (Shelley v. Kraemer:\\njudicial enforcement is state action)" {NO}];
es -> sk [style=dashed]; rc -> sk [style=dashed];
'''), None),
    ],
    # 10. Government Forbearance and Takings
    "takings_regulatory_judicial": [
        ("Is the regulation a taking?", dot(f'''
q1 [label="Permanent physical occupation or\\nappropriation of a right to invade?" {Q}];
per [label="Per se taking\\n(Loretto; Cedar Point)" {NO}];
q1 -> per [label="yes"];
q2 [label="Deprives the owner of ALL\\neconomically beneficial use?" {Q}];
q1 -> q2 [label="no"];
lu [label="Per se taking unless background\\nprinciples of nuisance/property\\nalready barred the use (Lucas)" {NO}];
q2 -> lu [label="yes"];
pc [label="Penn Central balancing:\\neconomic impact, investment-backed\\nexpectations, character of the action\\n(Pennsylvania Coal: \\"goes too far\\")" {OUT}];
q2 -> pc [label="no"];
'''), "A plurality in Stop the Beach would extend takings to judicial decisions that eliminate established property rights."),
    ],
    "takings_eminent_domain_just_compensation": [
        ("Eminent domain", dot(f'''
pu [label="Public use? Read broadly as public\\npurpose, incl. economic development\\n(Kelo, 5–4)" {Q}];
jc [label="Just compensation = fair market value\\n(not subjective value), ignoring value\\nchanges caused by the project itself\\n(United States v. Miller)" {OUT}];
pu -> jc [label="yes"];
'''), None),
    ],
}

DIAGRAMS.update({
    "trespass_introductory_concepts": [
        ("Trespass to land vs. trespass to chattels", dot(f'''
l [label="Intentional entry onto land\\n(intent to enter, not to trespass)"];
lt [label="Trespass to land: liable without harm;\\nnominal + punitive damages possible\\n(Jacque v. Steenberg Homes)" {OUT}];
l -> lt;
a [label="Overflight"];
at [label="Owner owns only the airspace it can\\nuse or occupy; high flights are not\\ntrespass (Hinman)" {NO}];
a -> at;
c [label="Interference with a chattel"];
ct [label="Trespass to chattels: requires harm or\\nsubstantial deprivation (Intel v. Hamidi)" {NO}];
c -> ct;
'''), "Land gets stronger protection than chattels: the right to exclude is protected by a property rule."),
    ],
    "discovery_creation": [
        ("Original acquisition: discovery and creation", dot(f'''
d [label="Discovery"];
dj [label="The discovering sovereign takes title;\\nNative nations keep a right of occupancy\\nthat only the U.S. can extinguish\\n(Johnson v. M'Intosh)"];
d -> dj;
c [label="Creation (information)"];
ci [label="Hot news: quasi-property against a\\ndirect competitor only (INS v. AP;\\nHolmes and Brandeis dissent)"];
c -> ci;
'''), None),
    ],
    "persons_commodities": [
        ("Body parts and property", dot(f'''
q [label="Claim to human tissue"];
mo [label="Excised cells: no conversion claim;\\nsue for lack of informed consent /\\nfiduciary breach (Moore v. Regents)" {NO}];
fl [label="Statutory sale bans read by their terms:\\npaying for blood-stem-cell (apheresis)\\ndonors is legal (Flynn v. Holder)" {OUT}];
he [label="Sperm left at death: enough of a property\\ninterest for the probate court to decide\\n(Hecht v. Superior Court)" {OUT}];
q -> mo; q -> fl; q -> he;
'''), "Calabresi & Melamed: some entitlements are protected by inalienability rules (no sale at any price)."),
    ],
    "entity_forms_condos_coops_corps_partnerships_trusts": [
        ("How courts review community and fiduciary decisions", dot(f'''
q [label="What is being challenged?" {Q}];
dec [label="A restriction in the recorded\\ndeclaration (CC&Rs)"];
rule [label="A board rule or decision"];
amend [label="A new restriction added later"];
fid [label="A trustee's or executor's\\ndealings with the property"];
q -> dec; q -> rule; q -> amend; q -> fid;
n [label="Presumed valid unless arbitrary, against\\npublic policy, or burdens outweigh benefits\\n(Nahrstedt: pet ban upheld)" {OUT}];
b [label="Business judgment rule: defer to good-faith\\ndecisions within the board's authority\\n(Levandusky; 40 West 67th v. Pullman)" {OUT}];
k [label="Only by the procedure the declaration\\nrequires, not a bylaw shortcut (Kiekel)" {NO}];
r [label="Duty of loyalty: self-dealing executors\\nowe appreciation damages (Rothko)" {NO}];
dec -> n; rule -> b; amend -> k; fid -> r;
'''), None),
    ],
    "liens_mortgages": [
        ("Mortgages and installment contracts", dot(f'''
d [label="Borrower defaults"];
f [label="Mortgage: foreclosure sale (borrower\\nmay redeem until the sale)"];
dd [label="Lender must use good faith and due\\ndiligence to get a fair price\\n(Murphy v. Financial Development)" {OUT}];
ic [label="Installment land contract\\nwith a forfeiture clause"];
sk [label="Buyer paid a substantial amount: forfeiture\\nis an unconscionable penalty; seller must\\nforeclose (Skendzel v. Marshall)" {OUT}];
d -> f -> dd; d -> ic -> sk;
'''), None),
    ],
    "conservation_easements_zoning": [
        ("Zoning challenges", dot(f'''
z [label="Zoning ordinance"];
eu [label="Valid unless clearly arbitrary and\\nunreasonable (Euclid v. Ambler)" {OUT}];
nc [label="An existing nonconforming use may be phased\\nout after a reasonable amortization period\\n(Harbison v. City of Buffalo)" {OUT}];
ml [label="A developing town must allow its fair share\\nof low- and moderate-income housing\\n(Mount Laurel, N.J. constitution)" {NO}];
z -> eu; z -> nc; z -> ml;
'''), None),
    ],
    "contract_clause_government_forbearance": [
        ("Public grants are read narrowly", dot(f'''
c [label="State charter to a private company"];
q [label="Does the charter expressly grant\\nan exclusive privilege?" {Q}];
y [label="The Contract Clause may protect it" {OUT}];
n [label="No implied monopoly: the state may\\nauthorize a competitor\\n(Charles River Bridge)" {NO}];
c -> q; q -> y [label="yes"]; q -> n [label="no"];
'''), None),
    ],
})
DIAGRAMS["title_transfer_land_transactions_good_faith_purchasers_recording"].append(
    ("Good-faith purchasers: void vs. voidable title", dot(f'''
q [label="How did the seller get it?" {Q}];
v [label="Theft, or fraud in the execution\\n(signer didn't know what it was):\\nvoid, passes no title" {NO}];
vd [label="Fraud in the inducement, bad check:\\nvoidable title" {OUT}];
gf [label="Passes good title only to a good-faith\\npurchaser for value (Kotis: buyer not in\\ngood faith, so the jeweler kept the watch)"];
neg [label="A negligent signer may lose to a bona fide\\npurchaser (Hauck v. Crawford)"];
q -> v; q -> vd; vd -> gf; v -> neg [style=dashed];
'''), "Equitable conversion: once a land sale contract is signed, the buyer is the equitable owner (Wood v. Donohue)."))

GUIDES = {
    "traditional_forms_of_property": ESTATES_GUIDE,
    "waste_restraints_on_alienation": WASTE_GUIDE,
    "concurrent_owners": CONCURRENT_GUIDE,
}
