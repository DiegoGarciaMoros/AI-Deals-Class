"""Download public acquisition agreements (8-K Exhibit 2.1) from SEC EDGAR.

Usage:
    SEC_USER_AGENT="Your Name your@email.com" python -m tracker.fetch_edgar --limit 20 --out data/edgar

SEC requires a descriptive User-Agent with contact details and a rate below
10 requests/second: https://www.sec.gov/os/accessing-edgar-data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{adsh}/{filename}"

# Phrases that select agreements with meaningful post-closing mechanics.
DEFAULT_QUERY = '"earn-out" "escrow" "survival"'
WANTED_EXHIBITS = {"EX-2.1", "EX-2.2", "EX-10.1"}


def _get(url: str, user_agent: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def search(query: str, start: str, end: str, user_agent: str, page_from: int = 0) -> list[dict]:
    params = urllib.parse.urlencode(
        {"q": query, "forms": "8-K", "dateRange": "custom", "startdt": start, "enddt": end, "from": page_from}
    )
    payload = json.loads(_get(f"{SEARCH_URL}?{params}", user_agent))
    return payload.get("hits", {}).get("hits", [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2026-09-01")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path("data/edgar"))
    args = parser.parse_args(argv)

    user_agent = os.environ.get("SEC_USER_AGENT")
    if not user_agent:
        print("Set SEC_USER_AGENT to 'Your Name your@email.com' (SEC requirement).", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []
    seen_filings: set[str] = set()
    page_from = 0

    while len(manifest) < args.limit:
        hits = search(args.query, args.start, args.end, user_agent, page_from)
        if not hits:
            break
        page_from += len(hits)
        for hit in hits:
            src = hit.get("_source", {})
            adsh, _, filename = hit["_id"].partition(":")
            if src.get("file_type") not in WANTED_EXHIBITS or adsh in seen_filings:
                continue
            cik = (src.get("ciks") or [""])[0].lstrip("0")
            url = ARCHIVE_URL.format(cik=cik, adsh=adsh.replace("-", ""), filename=filename)
            dest = args.out / f"{adsh}_{filename}"
            try:
                dest.write_bytes(_get(url, user_agent))
            except Exception as exc:  # noqa: BLE001 - keep going on individual failures
                print(f"skip {url}: {exc}", file=sys.stderr)
                continue
            seen_filings.add(adsh)
            manifest.append(
                {
                    "file": dest.name,
                    "url": url,
                    "companies": src.get("display_names"),
                    "filed": src.get("file_date"),
                    "exhibit": src.get("file_type"),
                }
            )
            print(f"[{len(manifest)}/{args.limit}] {src.get('display_names')} {src.get('file_date')}")
            time.sleep(0.2)
            if len(manifest) >= args.limit:
                break
        time.sleep(0.2)

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(manifest)} agreements to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
