"""Hand-written briefs of the academic readings for the "Treatises on Property Law" tab.

ASSIGNED: the articles the Fall 2026 syllabus assigns as additional readings (with classes and
pages). CASEBOOK: theorists excerpted or discussed in the casebook readings. Case citations use
[[Case Name]] so the app links them to the briefs. Written by hand, not generated; where a full
citation could not be confirmed, the entry gives the reading as the syllabus lists it.
"""

ASSIGNED = [
    {
        "title": "Property Rules, Liability Rules, and Inalienability: One View of the Cathedral",
        "author": "Guido Calabresi & A. Douglas Melamed",
        "cite": "85 Harv. L. Rev. 1089 (1972)",
        "assigned": "Class 2 (Nuisance): pp. 1105–1111 · Class 8 (Persons & Commodities): pp. 1111–1115 · "
                    "Class 10 (Self-Help & Defenses): pp. 1124–1127",
        "one_line": "Law first decides who gets an entitlement, then how to protect it: by a property rule "
                    "(no taking without the holder's consent), a liability rule (taking allowed if you pay a "
                    "court-set price), or an inalienability rule (no transfer at all).",
        "argument": [
            "**Two questions, kept separate.** (1) Who holds the entitlement (to pollute, or to be free of "
            "pollution)? (2) How is it protected? Mixing them up hides the real choices.",
            "**Property rules** work when bargaining is cheap: the holder sets the price, so a transfer "
            "happens only if the buyer values the thing more.",
            "**Liability rules** work when bargaining breaks down: many owners create **holdouts**, many "
            "beneficiaries create **free riders**, and accidents can't be negotiated in advance. A court or "
            "agency sets the price instead (eminent domain, tort damages). The cost: an objective price "
            "can under- or over-pay a holder who values the thing idiosyncratically.",
            "**Inalienability rules** ban the sale itself, for reasons of efficiency or justice: "
            "externalities to many third parties, **moralisms** (others are harmed just knowing the sale "
            "happens), **self-paternalism** (binding your future self), **true paternalism**, and "
            "**distributional** goals.",
            "**Four rules for nuisance** (pp. 1115–1124): (1) neighbor wins an injunction; (2) neighbor wins "
            "damages only; (3) polluter wins outright; (4) the neighbor can stop the polluter only by "
            "paying it. Rule 4 was the novel one; the Arizona Supreme Court reached the same remedy that "
            "year in [[Spur Industries Inc. v. Del E. Webb Development Co.]].",
            "**Why criminal sanctions for theft** (pp. 1124–1127): a thief could have bargained but chose to "
            "\"take now, pay later,\" turning a property rule into a liability rule. Punishment beyond the "
            "item's value deters that conversion and protects the system of property rules, not just the "
            "victim.",
        ],
        "terms": "Entitlement · property rule · liability rule · inalienability · holdout · free rider · "
                 "moralisms · self-paternalism · cheapest cost avoider",
        "cases": "[[Jacque v. Steenberg Homes]] (punitive damages protect a property rule) · "
                 "[[Campbell v. Seaman]] (rule 1) · *Boomer v. Atlantic Cement* (rule 2) · "
                 "[[Hendricks v. Stalnaker]] (rule 3) · [[Spur Industries Inc. v. Del E. Webb Development Co.]] (rule 4) · "
                 "[[Moore v. Regents of the University of California]] and [[Flynn v. Holder]] (inalienability) · "
                 "[[Kelo v. City of New London]] (eminent domain as a liability rule) · "
                 "[[Golden Press Inc. v. Rylands]] vs. [[Pile v. Pedrick]] (damages vs. injunction for encroachments)",
        "exam": "For any remedy question, name the entitlement holder and the protecting rule, then justify "
                "the choice by transaction costs (few parties: property rule; many parties or no chance to "
                "bargain: liability rule) and by fairness or distribution.",
        "critique": "Critics (e.g., Bertrand, below) say treating moral objections as just another hard-to-price "
                    "cost blurs two different reasons to ban a market: it's too costly, or it's wrong.",
    },
    {
        "title": "Law and Economics",
        "author": "John R. Commons",
        "cite": "34 Yale L.J. 371 (1925)",
        "assigned": "Class 3 (Privilege & First Possession): pp. 371–376",
        "one_line": "Law and economics share their roots in scarcity and property, and property is best "
                    "understood as customs that courts choose to enforce, not as a natural right or a pure "
                    "creation of the state.",
        "argument": [
            "**A common origin.** Both fields deal with scarcity, property and value over time, but English "
            "economics (after Ricardo and Bentham) split off into a quasi-science of wealth, cut loose from "
            "law's grounding in custom and precedent.",
            "**Against Bentham's individualism.** Bentham dismissed precedent as blind deference to "
            "ancestors and built on individual pleasure and pain; Commons doubts that summing selfish "
            "choices tells us what is good for society.",
            "**Courts select customs.** Judges act like referees: they watch how business people, workers "
            "and landlords actually behave and choose which practices get legal protection. Contract and "
            "property rights grew this way, case by case, from below.",
            "**A middle path.** Property is neither an untouchable natural right nor whatever the state "
            "says; it emerges from practice, and custom checks state power.",
        ],
        "terms": "Institutional economics · custom · selection of practices by courts · going concern",
        "cases": "[[Ghen v. Rich]] (court enforces the whalers' custom) · [[State ex rel. Thornton v. Hay]] "
                 "(custom as a source of public rights) · [[Fisher v. Steward]] (court refuses a local custom) · "
                 "[[Pierson v. Post]] (majority vs. dissent on whether hunters' practice should set the rule)",
        "exam": "Use Commons when a fact pattern involves an industry or community practice: argue whether "
                "the court should \"select\" it as law, and why.",
        "critique": "Courts can entrench the customs of the powerful (compare Hahn, below); \"custom\" is not "
                    "neutral about whose practices count.",
    },
    {
        "title": "Hunting, Fishing, and Foraging: Common Rights and Class Relations in the Postbellum South",
        "author": "Steven Hahn",
        "cite": "Radical History Review, no. 26 (1982)",
        "assigned": "Class 3 (Privilege & First Possession): pp. 38–43",
        "one_line": "After emancipation, Southern planters used trespass, game and fencing (\"stock\") laws to "
                    "close the customary open range, cutting off the subsistence that let freedpeople and "
                    "poor whites avoid dependent labor.",
        "argument": [
            "**The open range was custom.** Before the war, anyone could hunt, fish and graze livestock on "
            "unfenced land; farmers fenced crops in rather than animals out. Poor whites relied on this.",
            "**Emancipation made it a labor question.** Hunting, fishing and foraging let freedpeople "
            "support themselves without signing plantation labor contracts, so planters pushed new trespass, "
            "game and stock laws to force them back into wage work and sharecropping.",
            "**A class conflict, not only a racial one.** Small farmers and tenants, Black and white, "
            "resisted at the ballot box and sometimes by force; stock laws were repeatedly voted down.",
            "**From custom to absolute private property.** With Redemption, the laws spread and the commons "
            "closed, marking a shift from reciprocal, customary land use to market individualism.",
        ],
        "terms": "Open range · common rights · stock laws · game laws · enclosure",
        "cases": "[[Pierson v. Post]] and [[Ghen v. Rich]] (who gets to take wild animals) · "
                 "[[Baker v. Howard County Hunt]] (hunters vs. landowner's right to exclude) · "
                 "[[Fisher v. Steward]] (landowner beats finder of wild honey) · "
                 "[[Jacque v. Steenberg Homes]] (the right to exclude)",
        "exam": "Use Hahn to challenge \"neutral\" first-possession or trespass rules: ask who gains from "
                "closing a commons, and whether the right to exclude was being used to control labor.",
        "critique": "A regional history: it shows that property rules have distributive effects, not that "
                    "private property is always oppressive.",
    },
    {
        "title": "Legal Constraints on Slave Masters",
        "author": "Jenny (Bourne) Wahl",
        "cite": "Am. J. Legal Hist. (1997) (as assigned)",
        "assigned": "Class 8 (Persons & Commodities): pp. 1–18",
        "one_line": "Southern courts limited what masters could do with enslaved people mainly when a master's "
                    "choices imposed costs on third parties with legal standing (creditors, the community, "
                    "the state), not out of concern for the enslaved.",
        "argument": [
            "**The sample.** About 200 appellate cases on masters' treatment of slaves, out of roughly "
            "11,000 slave-related cases.",
            "**\"Positive good\" ideology vs. the record.** Pro-slavery writers claimed slavery gave lifelong "
            "care; some masters did act kindly. But courts allowed that kindness only until it shifted "
            "costs onto others.",
            "**Social-cost logic.** Manumission bonds and limits on freeing slaves guarded against freed "
            "people becoming public charges; a will's provision for an elderly slave could be protected "
            "against creditors when it saved the community money.",
            "**Why no parallel for animals.** There is no body of law regulating kindness to livestock: "
            "enslaved people's humanity created externalities ordinary property never did, yet their own "
            "welfare was protected only as a by-product.",
        ],
        "terms": "Externality · social cost · manumission · Coasean analysis",
        "cases": "Calabresi & Melamed's \"moralisms\" and externalities (above) · "
                 "[[Moore v. Regents of the University of California]] and [[Flynn v. Holder]] (limits on "
                 "treating persons as property)",
        "exam": "Use Wahl to show how efficiency (externality) reasoning can explain legal limits on owners "
                "while leaving the people affected without rights of their own.",
        "critique": "An economic lens can make a moral catastrophe look like a cost-allocation problem; Wahl's "
                    "point is descriptive, not a defense.",
    },
    {
        "title": "Contemporary Anti-Commodification Arguments (externalities)",
        "author": "Elodie Bertrand",
        "cite": "As listed on the syllabus",
        "assigned": "Class 8 (Persons & Commodities): pp. 55–65",
        "one_line": "\"Externality\" arguments for banning markets (in organs, sex, etc.) mix three different "
                    "reasons: transaction costs, moral objections, and the lack of any workable model for "
                    "pricing externalities at all.",
        "argument": [
            "**Economists narrowed \"externality.\"** Only *technological* (physical) spillovers count, not "
            "*pecuniary* ones (price effects) or *moral/psychological* ones (offense, envy). Bertrand says "
            "excluding them hides value judgments.",
            "**Three responses to an externality:** ban the market (market-inalienability), regulate it "
            "(incomplete commodification), or create a market in the externality itself (Coase: "
            "cap-and-trade or bargaining).",
            "**Calabresi & Melamed conflate** \"too costly to commodify\" with \"wrong to commodify\" in their "
            "slavery example, treating values as if they were just hard-to-price tastes.",
            "**A third reason to ban markets:** even with zero transaction costs, there is no proven model "
            "for efficiently pricing externalities, so a ban can reflect a real theoretical gap.",
            "**How anti-commodification writers use each type:** technological (harm to neighbors), "
            "pecuniary (Basu on coercion, Satz on organ markets), moral (Roth on repugnance), with no clear "
            "line for which externalities should matter.",
        ],
        "terms": "Technological / pecuniary / moral externality · market-inalienability · incomplete "
                 "commodification · repugnance",
        "cases": "[[Flynn v. Holder]] (statute bans paying marrow donors but not blood donors) · "
                 "[[Moore v. Regents of the University of California]] · [[United States v. Corrow]] (inalienable "
                 "cultural patrimony)",
        "exam": "When asked whether a market should be banned, separate the three reasons Bertrand names and "
                "say which one actually does the work.",
        "critique": "If almost every market offends someone or moves some price, Bertrand's own framework needs "
                    "a principle for which externalities count.",
    },
]

CASEBOOK = [
    {
        "title": "Toward a Theory of Property Rights", "author": "Harold Demsetz",
        "cite": "57 Am. Econ. Rev. 347 (1967)",
        "one_line": "Property rights emerge when the gains from internalizing externalities exceed the cost "
                    "of creating and enforcing the rights (Montagnais beaver territories after the fur trade).",
        "cases": "[[Ghen v. Rich]] · [[Pierson v. Post]] · [[Coffin v. Left Hand Ditch Co.]] (water rights where water is scarce)",
    },
    {
        "title": "Property and Personhood", "author": "Margaret Jane Radin",
        "cite": "34 Stan. L. Rev. 957 (1982)",
        "one_line": "Property bound up with a person's identity (a wedding ring, a home) deserves stronger "
                    "protection than fungible property held only for its exchange value.",
        "cases": "[[Moore v. Regents of the University of California]] · [[Delfino v. Vealencis]] · [[Kelo v. City of New London]]",
    },
    {
        "title": "Market-Inalienability", "author": "Margaret Jane Radin",
        "cite": "100 Harv. L. Rev. 1849 (1987)",
        "one_line": "Bans on selling personal things rest on prophylaxis, prohibition or the \"domino\" effect, "
                    "but create a double bind for poor sellers; decide case by case and address inequality.",
        "cases": "[[Flynn v. Holder]] · [[Moore v. Regents of the University of California]]",
    },
    {
        "title": "The Tragedy of the Commons", "author": "Garrett Hardin",
        "cite": "162 Science 1243 (1968)",
        "one_line": "Open-access resources get overused because each user gains fully but bears only part of "
                    "the cost; the usual cures are private property or regulation.",
        "cases": "[[Pierson v. Post]] · [[Higday v. Nickolaus]]",
    },
    {
        "title": "Governing the Commons", "author": "Elinor Ostrom", "cite": "(1990)",
        "one_line": "Communities often manage common resources well through their own rules (e.g., the Alanya "
                    "fishery), a third option between privatization and state control.",
        "cases": "[[Ghen v. Rich]] · [[State ex rel. Thornton v. Hay]]",
    },
    {
        "title": "The Tragedy of the Anticommons", "author": "Michael Heller",
        "cite": "111 Harv. L. Rev. 621 (1998)",
        "one_line": "When too many people can exclude (post-Soviet Moscow storefronts), resources sit idle: "
                    "the mirror image of the commons.",
        "cases": "[[Delfino v. Vealencis]] (partition) · [[Kelo v. City of New London]] (assembly and holdouts)",
    },
    {
        "title": "The Comedy of the Commons: Custom, Commerce, and Inherently Public Property",
        "author": "Carol M. Rose", "cite": "53 U. Chi. L. Rev. 711 (1986)",
        "one_line": "Some property (roads, waterways, beaches) is \"inherently public\" because open access "
                    "prevents holdouts and gains value with more users; custom and the public trust protect it.",
        "cases": "[[Illinois Central Railroad Co. v. Illinois]] · [[State ex rel. Thornton v. Hay]]",
    },
    {
        "title": "The Public Trust Doctrine in Natural Resource Law", "author": "Joseph L. Sax",
        "cite": "68 Mich. L. Rev. 471 (1970)",
        "one_line": "Revived the public trust doctrine as a tool for environmental protection and a check on "
                    "legislatures captured by developers.",
        "cases": "[[Illinois Central Railroad Co. v. Illinois]]",
    },
    {
        "title": "The Problem of Social Cost", "author": "Ronald H. Coase",
        "cite": "3 J.L. & Econ. 1 (1960)",
        "one_line": "With zero transaction costs, parties bargain to the efficient use whoever holds the "
                    "right; the initial allocation matters only for wealth, and transaction costs make law matter.",
        "cases": "[[Hendricks v. Stalnaker]] · [[Spur Industries Inc. v. Del E. Webb Development Co.]] · [[Pile v. Pedrick]]",
    },
    {
        "title": "The Idea of Property in Law", "author": "J.E. Penner", "cite": "(1997)",
        "one_line": "Property is a right in rem organized around exclusion, which protects our interest in using "
                    "things; only things \"separable\" from their owners can be property (the separability thesis).",
        "cases": "[[Jacque v. Steenberg Homes]] · [[Moore v. Regents of the University of California]]",
    },
    {
        "title": "The Disintegration of Property", "author": "Thomas C. Grey", "cite": "Nomos XXII (1980)",
        "one_line": "Treating property as a divisible \"bundle of rights\" detached from things has left the "
                    "concept without a core, weakening its special legal and political protection.",
        "cases": "[[Hinman v. Pacific Air Transport]] · [[Penn Central Transportation Co. v. New York City]]",
    },
]
