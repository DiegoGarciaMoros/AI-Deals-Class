"""Download the full text of each opinion in cases.csv.

Source: Harvard's Caselaw Access Project (static.case.law), which has every
published U.S. opinion through about 2020, free and with no API key.

Each opinion is saved to data/opinions/<slug>.txt. If a case can't be found
(or isn't a U.S. case, like Wood v. Leadbitter), paste its text into a .txt
file in data/opinions/ yourself and add a row for it in cases.csv.

Usage:
    python fetch_opinions.py
"""
import csv
import json
import re
import time
import urllib.request
from pathlib import Path

BASE = "https://static.case.law"
HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "opinions"


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NYU Law property class project"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def norm(s):
    return re.sub(r"[\s.]", "", s).lower()


def parse_cite(cite):
    """'25 Wash. 2d 692' -> (25, 'Wash. 2d', 692)"""
    m = re.match(r"^(\d+)\s+(.+?)\s+(\d+)$", cite.strip())
    if not m:
        raise ValueError(f"can't parse citation {cite!r}")
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reporters = get_json(f"{BASE}/ReportersMetadata.json")
    by_short_name = {}
    for r in reporters:
        by_short_name.setdefault(norm(r["short_name"]), r["slug"])

    rows = list(csv.DictReader(open(HERE / "cases.csv")))
    missing = []
    for row in rows:
        out = OUT_DIR / f"{slugify(row['case_name'])}.txt"
        if out.exists():
            print(f"have  {row['case_name']}")
            continue
        try:
            vol, reporter, page = parse_cite(row["citation"])
            slug = by_short_name.get(norm(reporter))
            if not slug:
                raise LookupError(f"reporter {reporter!r} not in CAP")
            cases = get_json(f"{BASE}/{slug}/{vol}/CasesMetadata.json")
            match = [c for c in cases if str(c.get("first_page")) == str(page)]
            if not match:
                raise LookupError(f"no case starting at page {page}")
            # Short opinions can share a first page; pick the one naming a party.
            parties = [w for w in re.split(r"\W+", row["case_name"].lower())
                       if len(w) > 3 and w not in ("united", "states", "state", "estate", "inc")]
            match.sort(key=lambda c: not any(p in c.get("name", "").lower() for p in parties))
            case = get_json(f"{BASE}/{slug}/{vol}/cases/{match[0]['file_name']}.json")
            header = (f"CASE: {row['case_name']}\nCITATION: {row['citation']} ({row['year']})\n"
                      f"CAP NAME: {case.get('name')}\nCOURT: {case.get('court', {}).get('name')}\n"
                      f"DECIDED: {case.get('decision_date')}\n\n")
            out.write_text(header + opinion_text(case))
            print(f"saved {row['case_name']}  ({out.stat().st_size // 1000} KB)")
        except Exception as e:  # noqa: BLE001 - report and keep going
            print(f"MISS  {row['case_name']}: {e}")
            missing.append(row["case_name"])
        time.sleep(0.3)

    if missing:
        print(f"\n{len(missing)} not found. Paste their text into data/opinions/<name>.txt:")
        for name in missing:
            print(f"  data/opinions/{slugify(name)}.txt")


if __name__ == "__main__":
    main()
