"""Chart data/case_data.csv -> data/owner_sovereignty.png

Question: across the cases in my property course, how often does the court side
with the owner, and in which units does the owner lose to necessity, custom,
public rights, or equity?

Usage:
    python visualize.py [--csv data/case_data.csv] [--out data/owner_sovereignty.png]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).parent
COLORS = {"yes": "#2a78d6", "no": "#eb6834", "mixed": "#a8a7a2"}
LABELS = {"yes": "Owner won", "no": "Owner lost", "mixed": "Mixed / n.a."}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def short_name(case_name):
    """'State ex rel. Thornton v. Hay' -> 'Thornton'; 'Intel Corp. v. Hamidi' -> 'Intel'"""
    first, _, second = str(case_name).partition(" v. ")
    if "ex rel." in first:
        first = first.split("ex rel.")[1]
    elif first in ("United States", "State", "People") and second:
        first = second
    return first.strip().split(" ")[0].rstrip(",")


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12, fontweight="bold")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_axisbelow(True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=HERE / "data" / "case_data.csv")
    ap.add_argument("--out", default=HERE / "data" / "owner_sovereignty.png")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df["outcome"] = df["owner_prevailed"].where(df["owner_prevailed"].isin(["yes", "no"]), "mixed")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    topic_order = list(dict.fromkeys(pd.read_csv(HERE / "cases.csv")["class_topic"]))
    topics = [t for t in topic_order if t in set(df["class_topic"])][::-1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 9.5), gridspec_kw={"width_ratios": [1, 1.5]})

    # Left: stacked bars, one per course unit.
    counts = df.groupby(["class_topic", "outcome"]).size().unstack(fill_value=0)
    counts = counts.reindex(index=topics, columns=["yes", "no", "mixed"], fill_value=0)
    left = pd.Series(0, index=topics)
    for outcome in ["yes", "no", "mixed"]:
        ax1.barh(topics, counts[outcome], left=left, color=COLORS[outcome], height=0.65,
                 edgecolor="white", linewidth=2, label=LABELS[outcome])
        left += counts[outcome]
    for y, total in enumerate(left):
        ax1.text(total + 0.08, y, str(int(total)), va="center", fontsize=9, color=MUTED)
    style(ax1, "Did the court side with the owner? (by course unit)")
    ax1.grid(axis="x", color=GRID, linewidth=0.8)
    ax1.set_xlabel("Number of cases", color=MUTED, fontsize=9)
    ax1.xaxis.get_major_locator().set_params(integer=True)

    # Right: every case on a timeline, same rows, colored by outcome.
    y_of = {t: i for i, t in enumerate(topics)}
    for outcome in ["yes", "no", "mixed"]:
        sub = df[df["outcome"] == outcome]
        ax2.scatter(sub["year"], sub["class_topic"].map(y_of), s=90, color=COLORS[outcome],
                    edgecolor="white", linewidth=2, zorder=3)
    # Alternate labels above/below the dots so neighbors in a row don't collide.
    for _, row in df.groupby("class_topic"):
        for k, (_, r) in enumerate(row.sort_values("year").iterrows()):
            above = k % 2 == 0
            ax2.annotate(short_name(r["case_name"]), (r["year"], y_of[r["class_topic"]]),
                         xytext=(0, 8 if above else -10), textcoords="offset points",
                         ha="center", va="bottom" if above else "top", fontsize=7.5, color=MUTED)
    ax2.set_yticks(range(len(topics)), topics)
    style(ax2, "Every case by year decided")
    ax2.grid(axis="y", color=GRID, linewidth=0.8)
    ax2.set_xlabel("Year decided", color=MUTED, fontsize=9)

    won = (df["outcome"] == "yes").sum()
    fig.suptitle(f"Owner sovereignty in my Property casebook: the owner won {won} of {len(df)} cases",
                 x=0.01, ha="left", fontsize=15, color=INK, fontweight="bold")
    fig.legend(*ax1.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.01, 0.95),
               ncol=3, frameon=False, fontsize=10, labelcolor=MUTED)
    model = df["model"].dropna().iloc[0] if df["model"].notna().any() else "an LLM"
    fig.text(0.01, 0.01, f"Outcomes coded by {model} via OpenRouter from the full opinion text.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.91), w_pad=4)
    fig.savefig(args.out, dpi=150)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
