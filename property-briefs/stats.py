"""Statistics tables over the casebook, shared by app.py (Statistics tab) and the command line.

Every table answers the course's main question, "when does the owner win?", against one
factor: where the case sits in the syllabus, when and by which court it was decided, what
competed with ownership, which theory of property the court used, and how it protected the
winner. Rates are shares of all cases in the row (mixed outcomes count against "won").

Usage:
    python stats.py            # writes data/stats/*.csv from data/casebook.json
"""
import json
import re
from pathlib import Path

import pandas as pd

from briefing import DOCTRINE_LABEL, TAXONOMY

HERE = Path(__file__).parent

# Factors a table can be built on: column -> (label, is_list)
FACTORS = {
    "competing_values": ("What competed with ownership", True),
    "justifications": ("Theory of property the court relied on", True),
    "sticks": ("Stick in the bundle at stake", True),
    "resource": ("Kind of resource", False),
    "rule_or_standard": ("Rule or standard", False),
    "entitlement_protection": ("How the entitlement is protected", False),
    "lawmaker": ("Who made the law", False),
    "time_shifts_rights": ("Did time create or end a right?", False),
    "remedy": ("Remedy", False),
    "court_level": ("Court", False),
    "era": ("Era decided", False),
    "owner_role": ("Owner was the…", False),
    "disposition": ("Disposition on appeal", False),
    "has_dissent": ("Dissent?", False),
    "unit_label": ("Class unit", False),
    "chapter": ("Syllabus chapter", False),
}
ERAS = [(0, 1900, "Before 1900"), (1900, 1960, "1900–1959"), (1960, 2000, "1960–1999"), (2000, 9999, "2000 on")]
OUTCOME = {"yes": "Owner won", "no": "Owner lost", "mixed": "Mixed", "not_applicable": "Mixed"}


def pretty(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Unknown"
    return str(value).replace("_", " ").capitalize()


def era(year):
    for lo, hi, label in ERAS:
        if lo <= (year or 0) < hi:
            return label
    return "Unknown"


NAME_STOP = {"of", "the", "in", "and", "et", "al", "inc", "co", "corp", "llc", "his", "her", "its", "their", "a", "an"}


def _words(text):
    words = (w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.split(r"[^a-z0-9]+", str(text).lower()))
    return {w for w in words if w and w not in NAME_STOP}


def owner_role(case):
    """Was the owner suing (plaintiff) or being sued (defendant)? The party sharing more words
    with the property holder's name (the coded holder before its first comma, then the whole
    description); a tie is "unclear"."""
    plaintiff, defendant = _words(case.get("plaintiff", "")), _words(case.get("defendant", ""))
    holder = str(case.get("property_holder", ""))
    for text in (holder.split(",")[0], holder):
        words = _words(text)
        p, d = len(words & plaintiff), len(words & defendant)
        if p != d:
            return "plaintiff" if p > d else "defendant"
    return "unclear"


def frame(casebook):
    """One row per case with the columns the tables use."""
    df = pd.DataFrame(casebook).copy()
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    df["Outcome"] = df["owner_prevailed"].map(OUTCOME).fillna("Mixed")
    df["won"] = df["owner_prevailed"].eq("yes")
    df["lost"] = df["owner_prevailed"].eq("no")
    df["era"] = df["year"].map(era)
    df["owner_role"] = [owner_role(c) for c in casebook]
    df["chapter"] = df.get("chapter", pd.Series(index=df.index, dtype=object)).fillna(df.get("area")).fillna("Other")
    df["doctrine_tags"] = df["doctrine_tags"].apply(lambda v: v if isinstance(v, list) else [])
    df["unit_label"] = df["doctrine_tags"].apply(lambda t: DOCTRINE_LABEL.get(t[0], "Other") if t else "Other")
    for name in ("has_dissent", "time_shifts_rights"):
        df[name] = df.get(name, False).fillna(False).astype(bool)
    return df


def _summary(group):
    n = len(group)
    rate = lambda mask: round(100 * mask.sum() / n) if n else 0  # noqa: E731
    return pd.Series({
        "Cases": n,
        "Owner won": int(group["won"].sum()),
        "Owner lost": int(group["lost"].sum()),
        "Mixed": int(n - group["won"].sum() - group["lost"].sum()),
        "Owner win %": rate(group["won"]),
        "Flexible standard %": rate(group["rule_or_standard"].eq("flexible_standard")),
        "Property rule %": rate(group["entitlement_protection"].eq("property_rule")),
        "Court made new law %": rate(group["lawmaker"].eq("court_made_new_law")),
        "Dissent %": rate(group["has_dissent"]),
        "Median year": int(group["year"].median()) if group["year"].notna().any() else None,
    })


def by_chapter(df):
    order = [*TAXONOMY, "Other"]
    out = df.groupby("chapter").apply(_summary, include_groups=False)
    out = out.reindex([c for c in order if c in out.index] + [c for c in out.index if c not in order])
    return out.reset_index().rename(columns={"chapter": "Chapter"})


def by_unit(df):
    units = {label: (ch, key) for ch, docs in TAXONOMY.items() for key, label in docs.items()}
    out = df.groupby("unit_label").apply(_summary, include_groups=False).reset_index()
    out.insert(0, "Chapter", out["unit_label"].map(lambda u: units.get(u, ("Other",))[0]))
    order = list(units)
    out["_o"] = out["unit_label"].map(lambda u: order.index(u) if u in order else 999)
    return out.sort_values("_o").drop(columns="_o").rename(columns={"unit_label": "Class unit"})


def explode(df, factor):
    long = df.assign(value=df[factor].apply(lambda v: v if isinstance(v, list) else [v])).explode("value").reset_index(drop=True)
    long = long[~long["value"].isin([None, "none", "unclear"])] if FACTORS[factor][1] else long
    long["Value"] = long["value"].map(pretty)
    return long


def by_factor(df, factor):
    """Rows = the factor's values. How often each appears, how often the owner wins with it,
    and where in the syllabus it shows up."""
    long = explode(df, factor)
    rows = []
    for value, g in long.groupby("Value"):
        s = _summary(g)
        rows.append({
            "Value": value, "Cases": s["Cases"], "Owner win %": s["Owner win %"],
            "Owner won": s["Owner won"], "Owner lost": s["Owner lost"], "Mixed": s["Mixed"],
            "Chapters": g["chapter"].nunique(),
            "Most common unit": g["unit_label"].mode().iat[0] if len(g) else "",
            "Median year": s["Median year"],
            "Cases (by year)": "; ".join(g.sort_values("year")["case_name"]),
        })
    return pd.DataFrame(rows).sort_values(["Cases", "Owner win %"], ascending=False)


def crosstab(df, factor, by="chapter"):
    """Cases per factor value (rows) in each chapter or unit (columns)."""
    long = explode(df, factor)
    table = pd.crosstab(long["Value"], long[by])
    order = [*TAXONOMY, "Other"] if by == "chapter" else [l for d in TAXONOMY.values() for l in d.values()] + ["Other"]
    table = table[[c for c in order if c in table.columns]]
    return table.loc[table.sum(axis=1).sort_values(ascending=False).index]


def win_rate_crosstab(df, factor, by="era"):
    """Owner win % for each factor value (rows) within each era/chapter (columns); blank = no cases."""
    long = explode(df, factor)
    table = long.pivot_table(index="Value", columns=by, values="won", aggfunc="mean")
    if by == "era":
        table = table[[e for _, _, e in ERAS if e in table.columns]]
    return (100 * table).round(0)


def count_crosstab(df, factor, by="era"):
    """Number of cases behind each cell of win_rate_crosstab."""
    long = explode(df, factor)
    return long.pivot_table(index="Value", columns=by, values="won", aggfunc="count")


def main():
    out = HERE / "data" / "stats"
    out.mkdir(exist_ok=True)
    df = frame(json.loads((HERE / "data" / "casebook.json").read_text()))
    by_chapter(df).to_csv(out / "by_chapter.csv", index=False)
    by_unit(df).to_csv(out / "by_unit.csv", index=False)
    for factor in FACTORS:
        if factor in ("chapter", "unit_label"):
            continue
        by_factor(df, factor).to_csv(out / f"by_{factor}.csv", index=False)
        crosstab(df, factor).to_csv(out / f"{factor}_by_chapter.csv")
    print(f"wrote {len(list(out.glob('*.csv')))} tables to {out}")


if __name__ == "__main__":
    main()
