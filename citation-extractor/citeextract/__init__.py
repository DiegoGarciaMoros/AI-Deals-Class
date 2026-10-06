"""Citation extraction pipeline: parse → (optionally) link via CourtListener → finalize."""

from __future__ import annotations

from typing import Any

from . import courtlistener
from .extractor import extract_citations, finalize, merge_authorities

__all__ = ["analyze"]


def _enrich(result: dict[str, Any], token: str | None, session=None) -> dict[str, Any]:
    cases = [a for a in result["authorities"] if a["kind"] == "case"]
    wanted = [c for a in cases for c in [a["citation"], *a["parallel_citations"]]]
    summary = {"performed": True, "error": None, "requested": len(set(wanted)), "found": 0,
               "ambiguous": 0, "not_found": 0}
    if not wanted:
        return summary
    try:
        found = courtlistener.lookup(wanted, token=token, session=session)
    except courtlistener.LookupError as exc:
        summary["error"] = str(exc)
        return summary

    by_cluster: dict[Any, dict[str, Any]] = {}
    merged: set[int] = set()
    for authority in cases:
        best = None
        for cite in [authority["citation"], *authority["parallel_citations"]]:
            res = found.get(cite)
            if not res:
                continue
            if res["status"] == "found" and res["clusters"]:
                best = res
                break
            if best is None or (res["status"] == "ambiguous" and best["status"] != "ambiguous"):
                best = res
        if best is None:
            continue

        info: dict[str, Any] = {"status": best["status"], "message": best["message"], "candidates": []}
        if best["status"] == "found" and best["clusters"]:
            cluster = best["clusters"][0]
            info.update(cluster_id=cluster["id"], case_name=cluster["case_name"],
                        date_filed=cluster["date_filed"], url=cluster["url"],
                        citations=cluster["citations"])
            authority["links"]["courtlistener"] = cluster["url"]
            summary["found"] += 1
        elif best["status"] == "ambiguous":
            info["candidates"] = best["clusters"]
            summary["ambiguous"] += 1
        else:
            summary["not_found"] += 1
        authority["courtlistener"] = info

        # Fill gaps the opinion text didn't supply.
        if info.get("case_name") and not authority["_names"]:
            parts = info["case_name"].split(" v. ", 1)
            authority["_names"].append((parts[0], parts[1] if len(parts) > 1 else None))
        if info.get("date_filed") and not authority["_years"]:
            authority["_years"].append(str(info["date_filed"])[:4])

        # Two authorities that resolve to the same opinion are parallel cites — merge them.
        cluster_id = info.get("cluster_id")
        if cluster_id is not None:
            if cluster_id in by_cluster:
                merge_authorities(by_cluster[cluster_id], authority)
                merged.add(id(authority))
                summary["found"] -= 1
            else:
                by_cluster[cluster_id] = authority

    result["authorities"] = [a for a in result["authorities"] if id(a) not in merged]
    summary["merged_parallel"] = len(merged)
    return summary


def analyze(text: str, lookup: bool = False, token: str | None = None, session=None) -> dict[str, Any]:
    """Full pipeline. Returns JSON-serializable results."""
    result = extract_citations(text)
    result["lookup"] = _enrich(result, token, session) if lookup else {"performed": False}
    return finalize(result)
