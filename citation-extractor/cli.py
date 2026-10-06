"""Command-line version: extract citations from a file and write export files.

    python cli.py samples/sample_opinion.txt --out exports/ [--lookup] [--token TOKEN]
"""

from __future__ import annotations

import argparse
import os
import sys

from citeextract import analyze
from citeextract.exporters import EXPORTS, export


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Text or HTML file containing the opinion ('-' for stdin)")
    parser.add_argument("--out", default="exports", help="Directory for export files (default: exports/)")
    parser.add_argument("--lookup", action="store_true", help="Link cases via the CourtListener citation lookup API")
    parser.add_argument("--token", help="CourtListener API token (or set COURTLISTENER_API_TOKEN)")
    parser.add_argument("--formats", default=",".join(EXPORTS), help="Comma-separated: " + ", ".join([*EXPORTS, "zip"]))
    args = parser.parse_args(argv)

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, encoding="utf-8", errors="replace") as fh:
            text = fh.read()

    result = analyze(text, lookup=args.lookup, token=args.token)
    stats = result["stats"]
    print(f"{stats['total_citations']} citations → {stats['unique_authorities']} authorities "
          f"({stats['cases']} cases, {stats['statutes']} statutes, {stats['journals']} secondary); "
          f"{stats['unresolved']} unresolved short forms")
    if result["lookup"].get("performed"):
        lk = result["lookup"]
        summary = lk.get("error") or "{found} linked, {ambiguous} ambiguous, {not_found} not found".format(**lk)
        print(f"CourtListener: {summary}")
    for a in result["authorities"]:
        link = a["links"].get("courtlistener") or ""
        print(f"  {a['id']:>4}  {a['occurrence_count']:>2}×  {a['full_citation']}  {link}")

    os.makedirs(args.out, exist_ok=True)
    for fmt in [f.strip() for f in args.formats.split(",") if f.strip()]:
        filename, _, content = export(result, fmt)
        path = os.path.join(args.out, filename)
        with open(path, "wb") as fh:
            fh.write(content)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
