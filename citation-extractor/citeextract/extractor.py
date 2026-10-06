"""Extract, normalize, and de-duplicate legal citations from the text of a case.

Parsing is done with eyecite (Free Law Project's citation parser). This module
adds the layer on top that turns eyecite's flat list of citation objects into a
clean list of *authorities*: one entry per cited case, statute, or journal
article, with every place it is cited (full cites, short cites, "Id.", "supra")
grouped underneath it along with the surrounding text.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import quote

try:  # eyecite imports this for its annotate() helper, which we never call. It has no
    import fast_diff_match_patch  # noqa: F401  prebuilt wheel for newer Pythons, so we
except ImportError:  # install eyecite without it and stub the module out.
    import sys
    import types

    sys.modules["fast_diff_match_patch"] = types.ModuleType("fast_diff_match_patch")

from eyecite import clean_text, get_citations, resolve_citations
from eyecite.models import (
    FullCaseCitation,
    FullJournalCitation,
    FullLawCitation,
    IdCitation,
    ReferenceCitation,
    ShortCaseCitation,
    SupraCitation,
)

try:  # courts_db ships with eyecite; used only for prettier court names.
    import courts_db

    _COURTS = {c["id"]: c for c in courts_db.courts}
except Exception:  # pragma: no cover - optional nicety
    _COURTS = {}

MAX_TEXT_LENGTH = 2_000_000
CONTEXT_CHARS = 220

KIND_ORDER = {"case": 0, "statute": 1, "journal": 2}
KIND_LABELS = {"case": "Cases", "statute": "Statutes, Rules & Regulations", "journal": "Secondary Sources"}

# Introductory signals (Bluebook rule 1.2), longest first so "See also" wins over "See".
_SIGNALS = [
    "See, e.g.,", "see, e.g.,", "See generally", "see generally", "See also", "see also",
    "But see", "but see", "But cf.", "but cf.", "Compare", "compare", "Contra", "contra",
    "Accord", "accord", "Cf.", "cf.", "E.g.,", "e.g.,", "See", "see",
]
_SIGNAL_RE = re.compile(
    r"(?:^|[\s(;,.])(" + "|".join(re.escape(s) for s in _SIGNALS) + r")\s*$"
)
# Leading words that eyecite occasionally leaves glued to a party name.
_LEADING_JUNK_RE = re.compile(
    r"^(?:(?:see|also|but|cf\.|e\.g\.,|accord|compare|contra|generally|in|the|and|under|as)\s+)+",
    re.I,
)
# Words that may legitimately precede the token eyecite treated as the plaintiff
# (e.g. "United" in "United States v. Lopez", "City of" in "City of New York v. ...").
_NAME_PREFIX_OK = re.compile(r"^(?:[A-Z][\w.'&-]*|of|the|ex|rel\.|&|de|la|du)$")
_NAME_PREFIX_STOP = {
    "In", "See", "Cf.", "But", "The", "And", "Under", "As", "Also", "Accord", "Compare",
    "Contra", "Moreover", "However", "Thus", "Although", "Because", "Since", "While",
    "Here", "There", "This", "That", "Court", "We", "Our", "Id.", "Ibid.", "Further",
    "E.g.,", "Similarly", "Likewise", "Indeed", "Then", "When", "If", "After", "Before",
}
_CORP_SUFFIX_RE = re.compile(
    r"^(?:Inc\.?|Corp\.?|Co\.?|Ltd\.?|LLC|L\.L\.C\.|LLP|L\.P\.|LP|N\.A\.|FSB|P\.C\.|PLC|S\.A\.|AG|GmbH)[,.]?$"
)
# Abbreviations that can sit inside a party name without ending the sentence.
_ABBREV_RE = re.compile(
    r"^(?:Corp|Co|Inc|Bros|Ltd|Ass'n|Dep't|Bd|Univ|Nat'l|Int'l|Mfg|Ins|Sec|Educ|Cnty|Cty|Comm'n|"
    r"Auth|Dist|Sch|Am|Fed|Gen|Mut|Elec|Tel|St|Mt|Ft|Ry|R\.R|Hosp|Med|Ctr|Gov't|Indus|Mgmt|"
    r"Pub|Serv|Servs|Sys|Tech|Transp|Util|Fin|Prods|Dev|Envtl|Hous|Admin|Assocs|Bros|Cal|"
    r"N\.Y|U\.S|Wash|Mass|Pa|Tex|Fla|Ill|Mich|Ohio|Va|Ga|N\.J|Conn|Md|Mo|Minn|Wis|Ind|Ariz)\.$"
)
_GENERIC_PARTIES = {
    "united states", "state", "people", "commonwealth", "in re", "ex parte", "the people",
    "united states of america", "matter of", "estate of",
}
_PARALLEL_GAP_RE = re.compile(r"^[\s,]*(?:\d[\d\s,\-–—n.&]*)?[\s,]*$")
_CODE_RE = re.compile(
    r"\b(\d{1,3})\s+(U\.\s?S\.\s?C\.(?:\s?A\.)?|C\.\s?F\.\s?R\.)\s*§§?\s*"
    r"(\d[0-9A-Za-z]*(?:[.\-–][0-9A-Za-z]+)*)((?:\([0-9A-Za-z]{1,5}\))*)"
)
_RULE_NAMES = {
    "fed.r.civ.p": ("Fed. R. Civ. P.", "Federal Rules of Civil Procedure"),
    "fed.r.crim.p": ("Fed. R. Crim. P.", "Federal Rules of Criminal Procedure"),
    "fed.r.app.p": ("Fed. R. App. P.", "Federal Rules of Appellate Procedure"),
    "fed.r.evid": ("Fed. R. Evid.", "Federal Rules of Evidence"),
    "fed.r.bankr.p": ("Fed. R. Bankr. P.", "Federal Rules of Bankruptcy Procedure"),
}
_LII_RULES = {"Fed. R. Civ. P.": "frcp", "Fed. R. Crim. P.": "frcrmp", "Fed. R. App. P.": "frap",
              "Fed. R. Evid.": "fre", "Fed. R. Bankr. P.": "frbp"}
_RULE_RE = re.compile(
    r"\b(Fed\.\s?R\.\s?(?:Civ\.\s?P|Crim\.\s?P|App\.\s?P|Evid|Bankr\.\s?P)\.?)\s+"
    r"(\d+(?:\.\d+)?)((?:\([0-9A-Za-z]{1,5}\))*)"
)
_HTML_RE = re.compile(r"<\s*(?:p|div|br|span|html|body|a|i|em|b|blockquote|pre|sup)\b", re.I)


# --------------------------------------------------------------------------- #
# Text cleaning
# --------------------------------------------------------------------------- #
def _normalize_characters(text: str) -> str:
    replacements = {
        " ": " ",   # non-breaking space
        "­": "",    # soft hyphen
        " ": " ", " ": " ", " ": " ",
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "﻿": "",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Re-join words hyphenated across line breaks ("Educa-\ntion").
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def clean_case_text(text: str) -> str:
    """Normalize raw opinion text (plain text or HTML) for citation parsing."""
    steps: list[Any] = []
    if _HTML_RE.search(text):
        steps.append("html")
    steps += [_normalize_characters, "underscores", "inline_whitespace"]
    cleaned = clean_text(text, steps)
    # Keep paragraph breaks, but unwrap hard line breaks inside a paragraph so
    # citations split across lines ("Harris v. Forklift Sys., Inc., 510 U.S. 17, 21\n(1993)")
    # parse as one unit.
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    cleaned = re.sub(r"\n{2,}", "\x00", cleaned).replace("\n", " ").replace("\x00", "\n\n")
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _tidy(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" ,;:")
    return value or None


def _clean_party(value: str | None) -> str | None:
    value = _tidy(value)
    if not value:
        return None
    value = _LEADING_JUNK_RE.sub("", value)
    return _tidy(value)


def _extend_plaintiff(text: str, start: int, plaintiff: str | None) -> tuple[str | None, int]:
    """Recover leading words eyecite dropped from a party name — "United" in
    "United States v. Lopez", "Bell Atlantic" in "Bell Atlantic Corp. v. Twombly",
    "Flagg Bros.," in "Flagg Bros., Inc. v. Brooks". Returns (name, new start)."""
    if not plaintiff:
        return plaintiff, start
    prefix = text[max(0, start - 80):start]
    if not prefix.endswith(" "):
        return plaintiff, start  # name does not begin on a word boundary
    prefix = prefix.split("\n")[-1]
    words = prefix.split()
    taken: list[str] = []
    right = plaintiff.split()[0]  # the word immediately to the right of the candidate
    for word in reversed(words[-5:]):
        if word in _NAME_PREFIX_STOP:
            break
        bare = word.rstrip(",")
        if word.endswith(",") and not (_CORP_SUFFIX_RE.match(right) and _NAME_PREFIX_OK.match(bare)):
            break
        if bare.endswith(".") and not _ABBREV_RE.match(bare):
            break
        if word.endswith((";", ":", ")", '"')) or not _NAME_PREFIX_OK.match(bare):
            break
        taken.insert(0, word)
        right = word
    # The extension must start with a capitalized word ("of the" alone is not a name).
    while taken and not taken[0][:1].isupper():
        taken.pop(0)
    if not taken:
        return plaintiff, start
    addition = " ".join(taken) + " "
    return addition + plaintiff, start - len(addition)


def _signal_before(text: str, start: int) -> str | None:
    match = _SIGNAL_RE.search(text[max(0, start - 30):start])
    if not match:
        return None
    signal = match.group(1).rstrip(",")
    return signal[0].upper() + signal[1:]


def _context(text: str, start: int, end: int, width: int = CONTEXT_CHARS) -> dict[str, str]:
    lo = max(0, start - width)
    hi = min(len(text), end + width)
    # Snap to word boundaries so context never begins or ends mid-word.
    if lo > 0:
        space = text.find(" ", lo, start)
        lo = space + 1 if space != -1 else lo
    if hi < len(text):
        space = text.rfind(" ", end, hi)
        hi = space if space != -1 else hi
    before = text[lo:start].replace("\n", " ")
    after = text[end:hi].replace("\n", " ")
    return {
        "before": ("…" if lo > 0 else "") + before,
        "match": text[start:end].replace("\n", " "),
        "after": after + ("…" if hi < len(text) else ""),
    }


def _year(value: Any) -> int | None:
    try:
        year = int(str(value)[:4])
    except (TypeError, ValueError):
        return None
    return year if 1600 <= year <= 2100 else None


def _court_abbrev(court_id: str | None, reporter: str | None) -> str | None:
    if not court_id:
        return None
    # Bluebook omits the court when the reporter makes it obvious (U.S. Reports etc.).
    if court_id == "scotus" or (reporter or "").startswith(("U.S.", "S. Ct.", "L. Ed.")):
        return None
    court = _COURTS.get(court_id)
    return court.get("citation_string") if court else None


def _court_name(court_id: str | None) -> str | None:
    court = _COURTS.get(court_id or "")
    return court.get("name") if court else None


def courtlistener_citation_url(volume: str, reporter: str, page: str) -> str:
    """CourtListener's citation redirector — works without an API token."""
    return "https://www.courtlistener.com/c/{}/{}/{}/".format(
        quote(reporter, safe="."), quote(str(volume)), quote(str(page))
    )


def _statute_url(groups: dict[str, str]) -> str | None:
    reporter = groups.get("reporter", "")
    if reporter in _LII_RULES and groups.get("section"):
        return f"https://www.law.cornell.edu/rules/{_LII_RULES[reporter]}/rule_{quote(groups['section'])}"
    title = groups.get("title") or groups.get("chapter") or groups.get("volume")
    section = (groups.get("section") or "").strip()
    section = re.split(r"[\s(]", section)[0] if section else ""
    if not title or not section:
        return None
    if reporter.startswith("U.S.C"):
        return f"https://www.law.cornell.edu/uscode/text/{quote(title)}/{quote(section)}"
    if reporter.startswith("C.F.R"):
        return f"https://www.law.cornell.edu/cfr/text/{quote(title)}/{quote(section)}"
    return None


# --------------------------------------------------------------------------- #
# Core extraction
# --------------------------------------------------------------------------- #
def _occurrence(text: str, cite: Any, kind: str, signal: str | None = None,
                full_start: int | None = None) -> dict[str, Any]:
    start, end = cite.span()
    eyecite_start, full_end = cite.full_span()
    full_start = eyecite_start if full_start is None else min(full_start, eyecite_start)
    meta = cite.metadata
    pin = _tidy(getattr(meta, "pin_cite", None))
    if pin and pin.lower().startswith("at "):
        pin = pin[3:]
    return {
        "type": kind,
        "text": text[start:end],
        "full_text": _tidy(text[full_start:full_end]),
        "pin_cite": pin,
        "parenthetical": _tidy(getattr(meta, "parenthetical", None)),
        "signal": signal,
        "start": start,
        "end": end,
        "context": _context(text, start, end),
    }


def _new_case_authority(text: str, cite: FullCaseCitation) -> dict[str, Any]:
    meta = cite.metadata
    edition = cite.edition_guess
    full_start = cite.full_span()[0]
    plaintiff, _ = _extend_plaintiff(text, full_start, _clean_party(meta.plaintiff))
    defendant = _clean_party(meta.defendant)
    groups = cite.groups
    return {
        "kind": "case",
        "citation": cite.corrected_citation(),
        "parallel_citations": [],
        "_cites": [cite],
        "_names": [(plaintiff, defendant)] if plaintiff or defendant else [],
        "_years": [meta.year] if meta.year else [],
        "_courts": [meta.court] if meta.court else [],
        "reporter": edition.short_name if edition else groups.get("reporter"),
        "reporter_name": edition.reporter.name if edition else None,
        "jurisdiction_type": edition.reporter.cite_type if edition else None,
        "volume": groups.get("volume"),
        "page": groups.get("page"),
        "occurrences": [],
        "links": {
            "courtlistener": None,
            "courtlistener_citation": courtlistener_citation_url(
                groups.get("volume", ""),
                edition.short_name if edition else groups.get("reporter", ""),
                groups.get("page", ""),
            )
            if groups.get("page")
            else None,
        },
    }


def _new_other_authority(cite: Any, kind: str) -> dict[str, Any]:
    edition = getattr(cite, "edition_guess", None)
    meta = cite.metadata
    groups = cite.groups
    authority = {
        "kind": kind,
        "citation": cite.corrected_citation(),
        "parallel_citations": [],
        "_cites": [cite],
        "_names": [],
        "_years": [meta.year] if getattr(meta, "year", None) else [],
        "_courts": [],
        "reporter": edition.short_name if edition else groups.get("reporter"),
        "reporter_name": edition.reporter.name if edition else None,
        "jurisdiction_type": edition.reporter.cite_type if edition else None,
        "volume": groups.get("volume") or groups.get("title") or groups.get("chapter"),
        "page": groups.get("page") or groups.get("section"),
        "occurrences": [],
        "links": {},
    }
    if kind == "statute":
        authority["links"]["source"] = _statute_url(groups)
    return authority


def _is_parallel(text: str, prev: FullCaseCitation, cur: FullCaseCitation) -> bool:
    """True when `cur` is a parallel cite to `prev` ("410 U.S. 113, 93 S. Ct. 705")."""
    if prev.full_span()[0] == cur.full_span()[0]:
        return True
    gap = text[prev.span()[1]:cur.span()[0]]
    return len(gap) <= 25 and bool(_PARALLEL_GAP_RE.match(gap)) and not cur.metadata.plaintiff


def _find_statutes(text: str) -> list[dict[str, Any]]:
    """Regex pass for U.S.C./C.F.R. sections and federal rules.

    eyecite misses or truncates alphanumeric sections ("42 U.S.C. § 2000e-2",
    "17 C.F.R. § 240.10b-5", "15 U.S.C. § 78j(b)"), which are everywhere in
    securities and employment opinions, so we parse these ourselves.
    """
    found = []
    for m in _CODE_RE.finditer(text):
        title, reporter, section, subsections = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        reporter = "C.F.R." if "F" in reporter else "U.S.C."
        groups = {"title": title, "reporter": reporter, "section": section}
        found.append({
            "start": m.start(), "end": m.end(), "key": f"{title} {reporter} § {section}",
            "groups": groups, "pin": subsections or None, "reporter": reporter,
            "reporter_name": "United States Code" if reporter == "U.S.C." else "Code of Federal Regulations",
        })
    for m in _RULE_RE.finditer(text):
        body, number, subsections = m.group(1), m.group(2), m.group(3) or ""
        name = _RULE_NAMES[body.replace(" ", "").rstrip(".").lower()]
        found.append({
            "start": m.start(), "end": m.end(), "key": f"{name[0]} {number}",
            "groups": {"reporter": name[0], "section": number}, "pin": subsections or None,
            "reporter": name[0], "reporter_name": name[1],
        })
    return sorted(found, key=lambda f: f["start"])


def _statute_authority(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "statute",
        "citation": match["key"],
        "parallel_citations": [],
        "_cites": [],
        "_names": [],
        "_years": [],
        "_courts": [],
        "reporter": match["reporter"],
        "reporter_name": match["reporter_name"],
        "jurisdiction_type": "federal",
        "volume": match["groups"].get("title"),
        "page": match["groups"].get("section"),
        "occurrences": [],
        "links": {"source": _statute_url(match["groups"])},
    }


def extract_citations(raw_text: str) -> dict[str, Any]:
    """Parse `raw_text` and return cleaned text plus de-duplicated authorities."""
    if len(raw_text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text is too long ({len(raw_text):,} characters; limit {MAX_TEXT_LENGTH:,}).")
    text = clean_case_text(raw_text)
    citations = get_citations(text)
    resolutions = resolve_citations(citations)

    authority_for: dict[int, dict[str, Any]] = {}   # id(eyecite cite) -> authority
    name_start: dict[int, int] = {}                 # id(full case cite) -> start of case name
    by_key: dict[str, dict[str, Any]] = {}          # normalized citation -> authority
    authorities: list[dict[str, Any]] = []
    prev_full_case: FullCaseCitation | None = None

    # Statutes and rules from our own regex pass take precedence over eyecite's
    # (often truncated) parse of the same span.
    statutes = _find_statutes(text)
    statute_occurrences: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for match in statutes:
        key = f"statute:{match['key']}"
        authority = by_key.get(key)
        if authority is None:
            authority = by_key[key] = _statute_authority(match)
            authorities.append(authority)
        statute_occurrences.append((match, authority))

    def statute_at(span: tuple[int, int]) -> dict[str, Any] | None:
        for match, authority in statute_occurrences:
            if match["start"] < span[1] and span[0] < match["end"]:
                return authority
        return None

    for cite in citations:
        if isinstance(cite, FullCaseCitation):
            key = cite.corrected_citation()
            plaintiff, start = _extend_plaintiff(text, cite.full_span()[0], _clean_party(cite.metadata.plaintiff))
            name_start[id(cite)] = start
            authority = by_key.get(key)
            if authority is None and prev_full_case is not None and _is_parallel(text, prev_full_case, cite):
                authority = authority_for[id(prev_full_case)]
                if key not in authority["parallel_citations"] and key != authority["citation"]:
                    authority["parallel_citations"].append(key)
                authority["_cites"].append(cite)
                by_key[key] = authority
            elif authority is None:
                authority = _new_case_authority(text, cite)
                by_key[key] = authority
                authorities.append(authority)
            else:
                authority["_cites"].append(cite)
                defendant = _clean_party(cite.metadata.defendant)
                if plaintiff or defendant:
                    authority["_names"].append((plaintiff, defendant))
                if cite.metadata.year:
                    authority["_years"].append(cite.metadata.year)
                if cite.metadata.court:
                    authority["_courts"].append(cite.metadata.court)
            authority_for[id(cite)] = authority
            prev_full_case = cite
        elif isinstance(cite, (FullLawCitation, FullJournalCitation)):
            prev_full_case = None
            if isinstance(cite, FullLawCitation):
                existing = statute_at(cite.span())
                if existing is not None:
                    authority_for[id(cite)] = existing
                    continue
            kind = "statute" if isinstance(cite, FullLawCitation) else "journal"
            key = f"{kind}:{cite.corrected_citation()}"
            authority = by_key.get(key)
            if authority is None:
                authority = _new_other_authority(cite, kind)
                by_key[key] = authority
                authorities.append(authority)
            else:
                authority["_cites"].append(cite)
            authority_for[id(cite)] = authority
        elif not isinstance(cite, (ShortCaseCitation, IdCitation, SupraCitation, ReferenceCitation)):
            prev_full_case = None  # unknown citation types break parallel chains

    # Attach short-form citations (short cites, Id., supra) via eyecite's resolver.
    resolved_ids: dict[int, dict[str, Any]] = {}
    for resource, cites in resolutions.items():
        anchor = getattr(resource, "citation", None)
        authority = authority_for.get(id(anchor)) if anchor is not None else None
        if authority is None:
            continue
        for cite in cites:
            resolved_ids[id(cite)] = authority

    # Occurrences: statutes from the regex pass, then everything eyecite found.
    for match, authority in statute_occurrences:
        start, end = match["start"], match["end"]
        authority["occurrences"].append({
            "type": "full", "text": text[start:end], "full_text": text[start:end], "pin_cite": match["pin"],
            "parenthetical": None, "signal": _signal_before(text, start), "start": start, "end": end,
            "context": _context(text, start, end),
        })
    statute_spans = [(m["start"], m["end"]) for m in statutes]

    unresolved: list[dict[str, Any]] = []
    for cite in citations:
        if isinstance(cite, (FullCaseCitation, FullLawCitation, FullJournalCitation)):
            kind = "full"
        elif isinstance(cite, ShortCaseCitation):
            kind = "short"
        elif isinstance(cite, IdCitation):
            kind = "id"
        elif isinstance(cite, SupraCitation):
            kind = "supra"
        elif isinstance(cite, ReferenceCitation):
            kind = "reference"
        else:
            continue
        span = cite.span()
        if kind == "full" and any(s < span[1] and span[0] < e for s, e in statute_spans):
            continue  # already recorded from the regex pass
        authority = authority_for.get(id(cite)) or resolved_ids.get(id(cite))
        anchor_start = name_start.get(id(cite), cite.full_span()[0])
        occurrence = _occurrence(text, cite, kind, _signal_before(text, anchor_start), anchor_start)
        if authority is None and kind == "id":
            authority = _id_after_statute(statute_occurrences, authorities, span[0])
        if authority is None:
            occurrence["antecedent_guess"] = _tidy(getattr(cite.metadata, "antecedent_guess", None))
            unresolved.append(occurrence)
            continue
        last = authority["occurrences"][-1] if authority["occurrences"] else None
        # Parallel cites print in the same string — record them once.
        if (
            kind == "full"
            and last is not None
            and last["type"] == "full"
            and cite.corrected_citation() in authority["parallel_citations"]
            and anchor_start <= last["end"] + 30
        ):
            last["end"] = occurrence["end"]
            last["text"] = text[last["start"]:occurrence["end"]]
            last["context"] = _context(text, last["start"], occurrence["end"])
            continue
        authority["occurrences"].append(occurrence)

    return {
        "text": text,
        "authorities": authorities,
        "unresolved": unresolved,
    }


def _id_after_statute(statute_occurrences, authorities, position: int) -> dict[str, Any] | None:
    """eyecite can't resolve "Id." after a statute it didn't parse. Attach it to
    that statute when the statute is the closest preceding citation."""
    best_statute = max(
        ((m["end"], a) for m, a in statute_occurrences if m["end"] <= position), default=None, key=lambda t: t[0]
    )
    if best_statute is None:
        return None
    for authority in authorities:
        if authority["kind"] == "statute":
            continue
        for occ in authority["occurrences"]:
            if best_statute[0] <= occ["start"] < position:
                return None  # some other citation sits in between
    return best_statute[1]


# --------------------------------------------------------------------------- #
# Finalization (after optional CourtListener enrichment)
# --------------------------------------------------------------------------- #
def merge_authorities(target: dict[str, Any], other: dict[str, Any]) -> None:
    """Fold `other` into `target` (used for parallel citations found via lookup)."""
    for cite in [other["citation"], *other["parallel_citations"]]:
        if cite != target["citation"] and cite not in target["parallel_citations"]:
            target["parallel_citations"].append(cite)
    target["_cites"] += other["_cites"]
    target["_names"] += other["_names"]
    target["_years"] += other["_years"]
    target["_courts"] += other["_courts"]
    target["occurrences"] = sorted(target["occurrences"] + other["occurrences"], key=lambda o: o["start"])
    for key, value in other.get("links", {}).items():
        target["links"].setdefault(key, value)
        if not target["links"].get(key):
            target["links"][key] = value


def _best_name(names: list[tuple[str | None, str | None]]) -> tuple[str | None, str | None]:
    complete = [n for n in names if n[0] and n[1]]
    if complete:
        # Prefer the most common full name, then the longest (least truncated).
        counts = Counter(complete)
        return max(complete, key=lambda n: (counts[n], len(n[0]) + len(n[1])))
    return names[0] if names else (None, None)


def _short_name(plaintiff: str | None, defendant: str | None) -> str | None:
    if plaintiff and plaintiff.lower() not in _GENERIC_PARTIES:
        return plaintiff.split(",")[0]
    return defendant.split(",")[0] if defendant else plaintiff


def _sort_key(authority: dict[str, Any]) -> tuple:
    name = (authority.get("case_name") or authority["citation"]).lower()
    name = re.sub(r"^(?:in re|ex parte|the)\s+", "", name)
    return (KIND_ORDER.get(authority["kind"], 9), name, authority["citation"])


def finalize(result: dict[str, Any]) -> dict[str, Any]:
    """Compute display fields, sort, assign ids, and strip internal state."""
    authorities = []
    for authority in result["authorities"]:
        authority["occurrences"].sort(key=lambda o: o["start"])
        years = [y for y in (_year(v) for v in authority.pop("_years")) if y]
        year = Counter(years).most_common(1)[0][0] if years else None
        courts = authority.pop("_courts")
        court = Counter(courts).most_common(1)[0][0] if courts else None
        plaintiff, defendant = _best_name(authority.pop("_names"))
        authority.pop("_cites", None)
        authority.setdefault("courtlistener", None)

        if authority["kind"] == "case":
            case_name = f"{plaintiff} v. {defendant}" if plaintiff and defendant else (plaintiff or defendant)
            authority["case_name"] = authority.get("case_name") or case_name
            authority["short_name"] = authority.get("short_name") or _short_name(plaintiff, defendant)
            authority["court"] = court
            authority["court_name"] = _court_name(court)
        else:
            authority["case_name"] = None
            authority["short_name"] = None
            authority["court"] = None
            authority["court_name"] = None
        authority["year"] = authority.get("year") or year

        # Bluebook-style display string: Name, 347 U.S. 483, 74 S. Ct. 686 (Court Year).
        cites = ", ".join([authority["citation"], *authority["parallel_citations"]])
        paren = " ".join(p for p in [_court_abbrev(court, authority.get("reporter")), str(authority["year"] or "")] if p)
        pieces = [authority["case_name"], cites] if authority.get("case_name") else [cites]
        authority["full_citation"] = ", ".join(pieces) + (f" ({paren})" if paren else "")

        occ = authority["occurrences"]
        authority["occurrence_count"] = len(occ)
        authority["first_position"] = occ[0]["start"] if occ else 0
        authority["pin_cites"] = list(dict.fromkeys(o["pin_cite"] for o in occ if o.get("pin_cite")))
        authority["parentheticals"] = list(dict.fromkeys(o["parenthetical"] for o in occ if o.get("parenthetical")))
        authority["signals"] = list(dict.fromkeys(o["signal"] for o in occ if o.get("signal")))
        authority["counts"] = dict(Counter(o["type"] for o in occ))
        authorities.append(authority)

    authorities.sort(key=_sort_key)
    for index, authority in enumerate(authorities, 1):
        authority["id"] = f"A{index}"
        for occurrence in authority["occurrences"]:
            occurrence["authority_id"] = authority["id"]

    kinds = Counter(a["kind"] for a in authorities)
    result["authorities"] = authorities
    result["stats"] = {
        "total_citations": sum(a["occurrence_count"] for a in authorities) + len(result["unresolved"]),
        "unique_authorities": len(authorities),
        "cases": kinds.get("case", 0),
        "statutes": kinds.get("statute", 0),
        "journals": kinds.get("journal", 0),
        "short_form": sum(
            a["counts"].get(k, 0) for a in authorities for k in ("short", "id", "supra", "reference")
        ),
        "unresolved": len(result["unresolved"]),
        "linked": sum(1 for a in authorities if a["links"].get("courtlistener")),
        "characters": len(result["text"]),
    }
    return result


def parse(raw_text: str) -> dict[str, Any]:
    """Extract and finalize without any network lookups."""
    return finalize(extract_citations(raw_text))
