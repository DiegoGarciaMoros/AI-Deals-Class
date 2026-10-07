"""Collect a sample of M&A deal announcements from SEC EDGAR.

Searches EDGAR full-text search for 8-K exhibit 99.1 press releases that
announce a "definitive merger agreement", downloads each one, strips the
HTML, and saves plain text to data/documents/.

Usage:
    python fetch_documents.py --n 40 --year 2025
"""
import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

# SEC asks automated clients to identify themselves.
USER_AGENT = "NYU AI Deals class project (contact: student@nyu.edu)"
OUT_DIR = Path(__file__).parent / "data" / "documents"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def search(year, page_from):
    params = {
        "q": '"definitive merger agreement"',
        "forms": "8-K",
        "dateRange": "custom",
        "startdt": f"{year}-01-01",
        "enddt": f"{year}-12-31",
        "from": page_from,
    }
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(params)
    return json.loads(get(url))["hits"]["hits"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="number of documents")
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen_companies, saved, page_from = set(), 0, 0
    while saved < args.n:
        hits = search(args.year, page_from)
        if not hits:
            break
        page_from += len(hits)
        for hit in hits:
            src = hit["_source"]
            # Keep only press releases (EX-99.1), one per company.
            if src.get("file_type") != "EX-99.1":
                continue
            company = src["display_names"][0]
            if company in seen_companies:
                continue
            accession, filename = hit["_id"].split(":")
            cik = src["ciks"][0].lstrip("0")
            url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                   f"{accession.replace('-', '')}/{filename}")
            try:
                text = html_to_text(get(url))
            except Exception as e:  # noqa: BLE001
                print(f"skip {url}: {e}")
                continue
            # Skip tiny exhibits that are not real announcements.
            if len(text) < 1500:
                continue
            seen_companies.add(company)
            saved += 1
            doc_id = f"{saved:03d}_{accession}"
            header = (f"SOURCE: {url}\nFILER: {company}\n"
                      f"FILED: {src.get('file_date')}\n\n")
            (OUT_DIR / f"{doc_id}.txt").write_text(header + text)
            print(f"[{saved}/{args.n}] {company}")
            if saved >= args.n:
                break
            time.sleep(0.2)  # stay well under SEC's 10 requests/sec limit


if __name__ == "__main__":
    main()
