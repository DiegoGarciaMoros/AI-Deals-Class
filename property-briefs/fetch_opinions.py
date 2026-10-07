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
import re
import time
from pathlib import Path

from caselaw import fetch_case

HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "opinions"


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(HERE / "cases.csv")))
    missing = []
    for row in rows:
        out = OUT_DIR / f"{slugify(row['case_name'])}.txt"
        if out.exists():
            print(f"have  {row['case_name']}")
            continue
        try:
            case, text = fetch_case(row["citation"], row["case_name"])
            header = (f"CASE: {row['case_name']}\nCITATION: {row['citation']} ({row['year']})\n"
                      f"CAP NAME: {case.get('name')}\nCOURT: {case.get('court', {}).get('name')}\n"
                      f"DECIDED: {case.get('decision_date')}\n\n")
            out.write_text(header + text)
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
