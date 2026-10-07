"""Chart the LLM annotations in data/annotations.csv -> data/deal_dashboard.png

Usage:
    python visualize.py [--csv data/annotations.csv] [--out data/deal_dashboard.png]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).parent
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=10, fontweight="bold")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def hbar(ax, counts, title, color=BLUE):
    counts = counts.sort_values()
    labels = [str(i).replace("_", " ") for i in counts.index]
    ax.barh(labels, counts.values, color=color, height=0.7)
    for y, v in enumerate(counts.values):
        ax.text(v + 0.15, y, str(v), va="center", fontsize=9, color=MUTED)
    style(ax, title)
    ax.set_xlabel("Number of deals", color=MUTED, fontsize=9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=HERE / "data" / "annotations.csv")
    ap.add_argument("--out", default=HERE / "data" / "deal_dashboard.png")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    for col in ("deal_value_usd_millions", "premium_pct", "hype_score"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.patch.set_facecolor("white")

    hbar(axes[0, 0], df["target_industry"].value_counts(), "Deals by target industry")
    hbar(axes[0, 1], df["consideration"].value_counts(), "How buyers paid")

    # Deal size vs. premium: do bigger deals pay bigger premiums?
    ax = axes[1, 0]
    sub = df.dropna(subset=["deal_value_usd_millions", "premium_pct"])
    sub = sub[sub["deal_value_usd_millions"] > 0]
    ax.scatter(sub["deal_value_usd_millions"], sub["premium_pct"], s=60, color=BLUE,
               edgecolor="white", linewidth=1.5, zorder=3)
    for _, r in sub.nlargest(3, "premium_pct").iterrows():
        ax.annotate(str(r["target"])[:28], (r["deal_value_usd_millions"], r["premium_pct"]),
                    xytext=(6, 4), textcoords="offset points", fontsize=8, color=MUTED)
    ax.set_xscale("log")
    style(ax, f"Deal value vs. premium paid (n={len(sub)})")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_xlabel("Deal value, US$ millions (log scale)", color=MUTED, fontsize=9)
    ax.set_ylabel("Premium to unaffected price (%)", color=MUTED, fontsize=9)

    # Hype score: how promotional is each press release?
    ax = axes[1, 1]
    hype = df["hype_score"].dropna().astype(int).value_counts().reindex(range(1, 6), fill_value=0)
    ax.bar(hype.index, hype.values, color=ORANGE, width=0.7)
    for x, v in hype.items():
        ax.text(x, v + 0.15, str(v), ha="center", fontsize=9, color=MUTED)
    style(ax, f"Press-release hype score (mean {df['hype_score'].mean():.1f})")
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_xticks(range(1, 6), ["1\ndry", "2", "3", "4", "5\npure hype"])
    ax.set_ylabel("Number of deals", color=MUTED, fontsize=9)

    model = df["model"].dropna().iloc[0] if "model" in df and df["model"].notna().any() else "LLM"
    fig.suptitle(f"{len(df)} M&A announcements from SEC 8-K filings, annotated by {model}",
                 x=0.01, ha="left", fontsize=14, color=INK, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=3, w_pad=3)
    fig.savefig(args.out, dpi=150)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
