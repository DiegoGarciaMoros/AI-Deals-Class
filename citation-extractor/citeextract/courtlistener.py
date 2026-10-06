"""Client for CourtListener's citation lookup API (v4).

Docs: https://www.courtlistener.com/help/api/rest/citation-lookup/

We send only the de-duplicated, normalized citation strings (one per line)
rather than the whole opinion, which keeps requests small and lets one call
cover every case cited in a long opinion.
"""

from __future__ import annotations

import os
import threading
from typing import Any

import requests

API_URL = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
SITE = "https://www.courtlistener.com"
MAX_CITATIONS_PER_REQUEST = 250   # API limit
MAX_CHARS_PER_REQUEST = 60_000    # API limit is 64,000 characters
USER_AGENT = "citation-extractor/1.0 (+https://github.com/diegogarciamoros/ai-deals-class)"

STATUS_LABELS = {
    200: "found",
    300: "ambiguous",
    400: "invalid",
    404: "not_found",
    429: "over_limit",
}

_cache: dict[str, dict[str, Any]] = {}
_cache_lock = threading.Lock()


class LookupError(Exception):
    """Raised when the whole lookup request fails (auth, throttling, network)."""


def default_token() -> str | None:
    return os.environ.get("COURTLISTENER_API_TOKEN") or os.environ.get("COURTLISTENER_TOKEN") or None


def _cluster_summary(cluster: dict[str, Any]) -> dict[str, Any]:
    url = cluster.get("absolute_url") or ""
    cites = []
    for c in cluster.get("citations") or []:
        if isinstance(c, dict) and c.get("volume") and c.get("reporter") and c.get("page"):
            cites.append(f"{c['volume']} {c['reporter']} {c['page']}")
        elif isinstance(c, str):
            cites.append(c)
    return {
        "id": cluster.get("id"),
        "case_name": cluster.get("case_name") or cluster.get("case_name_full") or None,
        "case_name_short": cluster.get("case_name_short") or None,
        "date_filed": cluster.get("date_filed"),
        "url": (SITE + url) if url.startswith("/") else (url or None),
        "citations": cites,
    }


def _chunks(citations: list[str]) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    size = 0
    for cite in citations:
        if current and (len(current) >= MAX_CITATIONS_PER_REQUEST or size + len(cite) + 1 > MAX_CHARS_PER_REQUEST):
            chunks.append(current)
            current, size = [], 0
        current.append(cite)
        size += len(cite) + 1
    if current:
        chunks.append(current)
    return chunks


def _post(text: str, token: str | None, session: requests.Session, timeout: float) -> list[dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    try:
        response = session.post(API_URL, data={"text": text}, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise LookupError(f"Could not reach CourtListener: {exc.__class__.__name__}") from exc

    if response.status_code in (401, 403):
        raise LookupError(
            "CourtListener rejected the request (HTTP %d). Add a valid API token — free at "
            "https://www.courtlistener.com/sign-in/ → Profile → Developer Tools." % response.status_code
        )
    if response.status_code == 429:
        wait = ""
        try:
            wait = response.json().get("wait_until") or ""
        except ValueError:
            pass
        raise LookupError("CourtListener rate limit reached" + (f"; try again after {wait}." if wait else "."))
    if response.status_code >= 400:
        raise LookupError(f"CourtListener returned HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError as exc:
        raise LookupError("CourtListener returned an unreadable response.") from exc
    if not isinstance(data, list):
        raise LookupError(str(data.get("detail") if isinstance(data, dict) else data)[:300])
    return data


def lookup(
    citations: list[str],
    token: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 30.0,
) -> dict[str, dict[str, Any]]:
    """Look up normalized citation strings. Returns {citation: result}.

    Each result is {"status": "found"|"ambiguous"|"not_found"|"invalid"|"over_limit",
    "clusters": [...], "message": str}. Raises LookupError if the API call fails.
    """
    token = token or default_token()
    session = session or requests.Session()
    unique = list(dict.fromkeys(c.strip() for c in citations if c and c.strip()))
    results: dict[str, dict[str, Any]] = {}

    with _cache_lock:
        pending = []
        for cite in unique:
            if cite in _cache:
                results[cite] = _cache[cite]
            else:
                pending.append(cite)

    for chunk in _chunks(pending):
        text = "\n".join(chunk)
        offsets: list[tuple[int, int, str]] = []
        pos = 0
        for cite in chunk:
            offsets.append((pos, pos + len(cite), cite))
            pos += len(cite) + 1

        for item in _post(text, token, session, timeout):
            start = item.get("start_index")
            matched = None
            if isinstance(start, int):
                matched = next((c for s, e, c in offsets if s <= start < e), None)
            if matched is None:
                normalized = set(item.get("normalized_citations") or []) | {item.get("citation")}
                matched = next((c for c in chunk if c in normalized), None)
            if matched is None:
                continue
            status_code = item.get("status")
            result = {
                "status": STATUS_LABELS.get(status_code, str(status_code)),
                "clusters": [_cluster_summary(c) for c in item.get("clusters") or [] if isinstance(c, dict)],
                "message": item.get("error_message") or "",
                "normalized_citations": item.get("normalized_citations") or [],
            }
            # Keep the best result if CourtListener returns the same cite twice.
            if matched in results and results[matched]["status"] == "found":
                continue
            results[matched] = result

        for cite in chunk:
            results.setdefault(cite, {"status": "not_found", "clusters": [], "message": "Not recognized as a citation.",
                                      "normalized_citations": []})
            if results[cite]["status"] in ("found", "not_found", "ambiguous"):
                with _cache_lock:
                    _cache[cite] = results[cite]
    return results


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()
