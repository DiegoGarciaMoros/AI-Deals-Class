"""Find cases by name or Westlaw-style filters, using CourtListener's case-law search
(https://www.courtlistener.com/help/api/rest/search/), and get a found case's full text.

Search works without an account at low volume; for more, or to download text CourtListener
doesn't let anonymous users read, set COURTLISTENER_TOKEN (free account -> Profile -> API).
Full text comes from the Caselaw Access Project by citation when possible (no key needed),
otherwise from CourtListener.
"""
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from caselaw import fetch_case

API = "https://www.courtlistener.com/api/rest/v4"
SITE = "https://www.courtlistener.com"

# CourtListener court IDs by jurisdiction and level. "trial" lists only the trial courts
# CourtListener indexes as courts of record (few states publish trial opinions).
FEDERAL_DISTRICTS = (
    "almd alnd alsd akd azd ared arwd cacd caed cand casd cod ctd ded dcd flmd flnd flsd gamd gand gasd "
    "hid idd ilcd ilnd ilsd innd insd iand iasd ksd kyed kywd laed lamd lawd med mdd mad mied miwd mnd "
    "msnd mssd moed mowd mtd ned nvd nhd njd nmd nyed nynd nysd nywd nced ncmd ncwd ndd ohnd ohsd oked "
    "oknd okwd ord paed pamd pawd rid scd sdd tned tnmd tnwd txed txnd txsd txwd utd vtd vaed vawd waed "
    "wawd wvnd wvsd wied wiwd wyd gud nmid prd vid").split()
COURTS = {
    "Federal": {"highest": ["scotus"],
                "appellate": [f"ca{i}" for i in range(1, 12)] + ["cadc", "cafc"],
                "trial": FEDERAL_DISTRICTS},
    "Alabama": {"highest": ["ala"], "appellate": ["alacivapp", "alacrimapp"]},
    "Alaska": {"highest": ["alaska"], "appellate": ["alaskactapp"]},
    "Arizona": {"highest": ["ariz"], "appellate": ["arizctapp"]},
    "Arkansas": {"highest": ["ark"], "appellate": ["arkctapp"]},
    "California": {"highest": ["cal"], "appellate": ["calctapp"]},
    "Colorado": {"highest": ["colo"], "appellate": ["coloctapp"]},
    "Connecticut": {"highest": ["conn"], "appellate": ["connappct"]},
    "Delaware": {"highest": ["del"], "trial": ["delch", "delsuperct"]},
    "District of Columbia": {"highest": ["dc"]},
    "Florida": {"highest": ["fla"], "appellate": ["fladistctapp"]},
    "Georgia": {"highest": ["ga"], "appellate": ["gactapp"]},
    "Hawaii": {"highest": ["haw"], "appellate": ["hawapp"]},
    "Idaho": {"highest": ["idaho"], "appellate": ["idahoctapp"]},
    "Illinois": {"highest": ["ill"], "appellate": ["illappct"]},
    "Indiana": {"highest": ["ind"], "appellate": ["indctapp"]},
    "Iowa": {"highest": ["iowa"], "appellate": ["iowactapp"]},
    "Kansas": {"highest": ["kan"], "appellate": ["kanctapp"]},
    "Kentucky": {"highest": ["ky"], "appellate": ["kyctapp"]},
    "Louisiana": {"highest": ["la"], "appellate": ["lactapp"]},
    "Maine": {"highest": ["me"]},
    "Maryland": {"highest": ["md"], "appellate": ["mdctspecapp"]},
    "Massachusetts": {"highest": ["mass"], "appellate": ["massappct"]},
    "Michigan": {"highest": ["mich"], "appellate": ["michctapp"]},
    "Minnesota": {"highest": ["minn"], "appellate": ["minnctapp"]},
    "Mississippi": {"highest": ["miss"], "appellate": ["missctapp"]},
    "Missouri": {"highest": ["mo"], "appellate": ["moctapp"]},
    "Montana": {"highest": ["mont"]},
    "Nebraska": {"highest": ["neb"], "appellate": ["nebctapp"]},
    "Nevada": {"highest": ["nev"], "appellate": ["nevapp"]},
    "New Hampshire": {"highest": ["nh"]},
    "New Jersey": {"highest": ["nj"], "appellate": ["njsuperctappdiv"]},
    "New Mexico": {"highest": ["nm"], "appellate": ["nmctapp"]},
    "New York": {"highest": ["ny"], "appellate": ["nyappdiv", "nyappterm"], "trial": ["nysupct"]},
    "North Carolina": {"highest": ["nc"], "appellate": ["ncctapp"]},
    "North Dakota": {"highest": ["nd"], "appellate": ["ndctapp"]},
    "Ohio": {"highest": ["ohio"], "appellate": ["ohioctapp"]},
    "Oklahoma": {"highest": ["okla", "oklacrimapp"], "appellate": ["oklacivapp"]},
    "Oregon": {"highest": ["or"], "appellate": ["orctapp"]},
    "Pennsylvania": {"highest": ["pa"], "appellate": ["pasuperct", "pacommwct"]},
    "Rhode Island": {"highest": ["ri"]},
    "South Carolina": {"highest": ["sc"], "appellate": ["scctapp"]},
    "South Dakota": {"highest": ["sd"]},
    "Tennessee": {"highest": ["tenn"], "appellate": ["tennctapp", "tenncrimapp"]},
    "Texas": {"highest": ["tex", "texcrimapp"], "appellate": ["texapp"]},
    "Utah": {"highest": ["utah"], "appellate": ["utahctapp"]},
    "Vermont": {"highest": ["vt"]},
    "Virginia": {"highest": ["va"], "appellate": ["vactapp"]},
    "Washington": {"highest": ["wash"], "appellate": ["washctapp"]},
    "West Virginia": {"highest": ["wva"]},
    "Wisconsin": {"highest": ["wis"], "appellate": ["wisctapp"]},
    "Wyoming": {"highest": ["wyo"]},
}
LEVELS = {"highest": "Highest court (e.g. state supreme court, U.S. Supreme Court)",
          "appellate": "Intermediate appellate court",
          "trial": "Trial court"}
SORTS = {"Relevance": "score desc", "Most cited": "citeCount desc",
         "Newest first": "dateFiled desc", "Oldest first": "dateFiled asc"}
SYNTAX_HELP = ("Terms & connectors: `AND`, `OR`, `NOT` (or `-word`), \"exact phrase\", "
               "`\"adverse possession\"~10` (words within 10 of each other), `possess*` (wildcard), "
               "and fields such as `caseName:(Kelo)`.")


def court_ids(jurisdictions=(), levels=(), extra=""):
    """CourtListener court IDs for the chosen jurisdictions and levels, plus any typed IDs."""
    ids = []
    for j in jurisdictions or []:
        for level in levels or LEVELS:
            ids += COURTS.get(j, {}).get(level, [])
    if levels and not jurisdictions:  # a level across every jurisdiction
        for courts in COURTS.values():
            for level in levels:
                ids += courts.get(level, [])
    ids += re.findall(r"[a-z0-9]+", extra.lower())
    return list(dict.fromkeys(ids))


def _get(url, token=None):
    headers = {"User-Agent": "Foundations of Property Law (NYU Law study tool)", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise PermissionError("CourtListener wants an API token for this. Add COURTLISTENER_TOKEN "
                                  "to the app's secrets (free: courtlistener.com > Profile > API).") from e
        if e.code == 429:
            raise RuntimeError("CourtListener's rate limit was hit. Wait a minute, or add a "
                               "COURTLISTENER_TOKEN for a higher limit.") from e
        raise RuntimeError(f"CourtListener returned HTTP {e.code}.") from e
    except urllib.error.URLError as e:
        raise RuntimeError("Couldn't reach CourtListener. Try again in a moment; if it keeps failing, "
                           "search by citation instead.") from e


def build_params(name="", terms="", citation="", jurisdictions=(), levels=(), extra_courts="",
                 year_from=None, year_to=None, judge="", cited_at_least=0, docket="",
                 published_only=True, sort="Relevance"):
    params = {"type": "o", "order_by": SORTS.get(sort, "score desc")}
    for key, value in (("q", terms), ("case_name", name), ("citation", citation),
                       ("judge", judge), ("docket_number", docket)):
        if value and value.strip():
            params[key] = value.strip()
    courts = court_ids(jurisdictions, levels, extra_courts)
    if courts:
        params["court"] = " ".join(courts)
    if year_from:
        params["filed_after"] = f"{int(year_from)}-01-01"
    if year_to:
        params["filed_before"] = f"{int(year_to)}-12-31"
    if cited_at_least:
        params["cited_gt"] = int(cited_at_least) - 1
    if published_only:
        params["stat_Published"] = "on"
    return params


def parse_result(r):
    opinions = r.get("opinions") or []
    snippet = next((o.get("snippet") for o in opinions if o.get("snippet")), r.get("snippet") or "")
    snippet = re.sub(r"<[^>]+>", "", html.unescape(snippet or "")).strip()
    return {
        "name": r.get("caseName") or r.get("caseNameFull") or "(untitled)",
        "court": r.get("court") or r.get("court_citation_string") or r.get("court_id", ""),
        "court_id": r.get("court_id", ""),
        "date": (r.get("dateFiled") or "")[:10],
        "citations": [c for c in (r.get("citation") or []) if isinstance(c, str)],
        "cited_by": r.get("citeCount") or 0,
        "docket": r.get("docketNumber") or "",
        "judge": r.get("judge") or "",
        "status": r.get("status") or "",
        "cluster_id": r.get("cluster_id") or r.get("id"),
        "opinion_ids": [o["id"] for o in opinions if o.get("id")],
        "url": SITE + r["absolute_url"] if r.get("absolute_url") else "",
        "snippet": snippet[:400],
    }


def search(token=None, page_url=None, **filters):
    """One page of results: (results, total_count, next_page_url)."""
    url = page_url or f"{API}/search/?" + urllib.parse.urlencode(build_params(**filters))
    data = _get(url, token)
    return [parse_result(r) for r in data.get("results", [])], data.get("count"), data.get("next")


def _strip_html(text):
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>", "\n", text)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def _courtlistener_text(result, token):
    ids = list(result.get("opinion_ids") or [])
    if not ids and result.get("cluster_id"):
        cluster = _get(f"{API}/clusters/{result['cluster_id']}/", token)
        ids = [int(re.search(r"/(\d+)/?$", u).group(1)) for u in cluster.get("sub_opinions", []) if re.search(r"/(\d+)/?$", u)]
    parts = []
    for oid in ids:
        op = _get(f"{API}/opinions/{oid}/", token)
        text = op.get("plain_text") or ""
        if not text.strip():
            for field in ("html_with_citations", "html_lawbox", "html_columbia", "html", "xml_harvard"):
                if (op.get(field) or "").strip():
                    text = _strip_html(op[field])
                    break
        if text.strip():
            parts.append(f"=== {str(op.get('type', 'opinion')).upper()} ===\n{text.strip()}")
    return "\n\n".join(parts)


def full_text(result, token=None):
    """(text, source) for a search result: the Caselaw Access Project by citation if it has the
    case (no key needed), otherwise CourtListener."""
    for cite in result.get("citations") or []:
        try:
            case, text = fetch_case(cite, result.get("name", ""))
            if len(text) > 500:
                return text, f"Caselaw Access Project ({cite})"
        except Exception:  # noqa: BLE001 - try the next citation, then CourtListener
            continue
    text = _courtlistener_text(result, token)
    if len(text) < 500:
        raise LookupError("Couldn't get this opinion's full text. Open it on CourtListener and paste it "
                          "into 'Paste the opinion text' instead.")
    return text, "CourtListener"
