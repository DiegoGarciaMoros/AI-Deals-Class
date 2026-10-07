"""Look up an opinion by citation in Harvard's Caselaw Access Project (static.case.law).

Free, no API key, and it has every published U.S. opinion through about 2020.
"""
import functools
import json
import re
import urllib.request

BASE = "https://static.case.law"
# How people often write a reporter -> how CAP abbreviates it (both normalized).
ALIASES = {"cair": "cai", "caines": "cai"}


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NYU Law property class project"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def norm(s):
    return re.sub(r"[\s.]", "", s).lower()


@functools.lru_cache(maxsize=1)
def reporter_slugs():
    slugs = {}
    for r in get_json(f"{BASE}/ReportersMetadata.json"):
        slugs.setdefault(norm(r["short_name"]), r["slug"])
    return slugs


def parse_cite(cite):
    """'25 Wash. 2d 692' -> (25, 'Wash. 2d', 692). Ignores a trailing '(1946)'."""
    cite = re.sub(r"\(.*?\)", "", cite).strip().rstrip(",")
    m = re.match(r"^(\d+)\s+(.+?)\s+(\d+)$", cite)
    if not m:
        raise ValueError(f"can't read citation {cite!r}; use the form '81 Vt. 471'")
    return int(m.group(1)), m.group(2), int(m.group(3))


def opinion_text(case):
    body = case.get("casebody", {})
    parts = []
    if body.get("head_matter"):
        parts.append(body["head_matter"])
    for op in body.get("opinions", []):
        label = op.get("type", "opinion").upper()
        author = op.get("author") or ""
        parts.append(f"=== {label} {author} ===\n{op.get('text', '')}")
    return "\n\n".join(parts)


def fetch_case(citation, case_name=""):
    """Return (case_metadata, full_text) for a citation like '81 Vt. 471'."""
    vol, reporter, page = parse_cite(citation)
    slug = reporter_slugs().get(ALIASES.get(norm(reporter), norm(reporter)))
    if not slug:
        raise LookupError(f"reporter {reporter!r} isn't in the Caselaw Access Project")
    cases = get_json(f"{BASE}/{slug}/{vol}/CasesMetadata.json")
    match = [c for c in cases if str(c.get("first_page")) == str(page)]
    if not match:
        raise LookupError(f"no case starts at page {page} of {vol} {reporter}")
    # Short opinions can share a first page: prefer one naming a party, then the longest.
    parties = [w for w in re.split(r"\W+", case_name.lower())
               if len(w) > 3 and w not in ("united", "states", "state", "estate", "inc")]
    match.sort(key=lambda c: (not any(p in c.get("name", "").lower() for p in parties),
                              -(int(c.get("last_page") or 0) - int(c.get("first_page") or 0))))
    case = get_json(f"{BASE}/{slug}/{vol}/cases/{match[0]['file_name']}.json")
    return case, opinion_text(case)
