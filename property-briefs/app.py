"""Property Case Briefer: brief any U.S. case in my format and place it in my casebook.

Run locally:   streamlit run app.py   (with OPENROUTER_API_KEY in the environment)
Deploy:        Streamlit Community Cloud, with OPENROUTER_API_KEY in the app's Secrets.
"""
import json
import os
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from briefing import DEFAULT_MODEL, THEMES, brief_opinion
from caselaw import fetch_case

HERE = Path(__file__).parent
CASEBOOK = json.loads((HERE / "data" / "casebook.json").read_text())
SYNTHESIS = HERE / "data" / "course_synthesis.md"
MAX_BRIEFS_PER_VISIT = 8  # every brief is paid for with my OpenRouter key

OUTCOME = {"yes": "Owner won", "no": "Owner lost", "mixed": "Mixed", "not_applicable": "Mixed"}
OUTCOME_COLORS = {"Owner won": "#2a78d6", "Owner lost": "#eb6834", "Mixed": "#a8a7a2"}
THEME_LABELS = {
    "competing_values": "What competed with ownership",
    "justifications": "Theory of property the court relied on",
    "sticks": "Stick in the bundle at stake",
    "resource": "Kind of resource",
    "rule_or_standard": "Rule or standard",
    "entitlement_protection": "How the entitlement is protected",
    "lawmaker": "Who made the law",
    "time_shifts_rights": "Did time create or end a right?",
}
EXAMPLES = {
    "Pierson v. Post (fox hunt, 1805)": ("3 Cai. R. 175", "Pierson v. Post"),
    "Jacque v. Steenberg Homes (trespass, 1997)": ("209 Wis. 2d 605", "Jacque v. Steenberg Homes"),
    "State v. Shack (right to exclude, 1971)": ("58 N.J. 297", "State v. Shack"),
    "Kelo v. City of New London (takings, 2005)": ("545 U.S. 469", "Kelo v. City of New London"),
}

st.set_page_config(page_title="Property Case Briefer", page_icon="⚖️", layout="wide")


# ---------- helpers ----------

def api_key():
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:  # noqa: BLE001 - no secrets file when run locally
        return os.environ.get("OPENROUTER_API_KEY")


def pretty(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).replace("_", " ").capitalize()


def as_list(value):
    return value if isinstance(value, list) else [value]


def takeaway(brief):
    m = re.search(r"\*\*Takeaway:\*\*\s*(.+)", brief or "")
    return m.group(1).strip() if m else ""


def tags(case):
    """The case's theme codes as a set, for comparing cases."""
    out = {f"owner:{case.get('owner_prevailed')}"}
    for name in THEMES:
        for v in as_list(case.get(name)):
            if v is True:
                out.add(f"{name}:time_shifts_rights")
            elif v not in (None, False, "none", "unclear"):
                out.add(f"{name}:{v}")
    return out


def closest(case, k=3):
    mine = tags(case)
    scored = []
    for other in CASEBOOK:
        if other["case_name"] == case.get("case_name"):
            continue
        theirs = tags(other)
        shared = mine & theirs
        scored.append((len(shared) / len(mine | theirs), other, shared))
    return sorted(scored, key=lambda s: -s[0])[:k]


def casebook_index():
    return "\n".join(f"{c['case_name']} | {c['year']} | {c['owner_prevailed']} | {c.get('principle') or takeaway(c['brief'])}"
                     for c in CASEBOOK)


@st.cache_data(show_spinner=False, max_entries=200)
def lookup(citation, name):
    return fetch_case(citation, name)


@st.cache_data(show_spinner=False, max_entries=200)
def run_brief(text, model):
    brief, fields, _ = brief_opinion(api_key(), model, text, index=casebook_index())
    return brief, fields


def verdict_badge(fields):
    label = OUTCOME.get(fields.get("owner_prevailed"), "Mixed")
    color = OUTCOME_COLORS[label]
    st.markdown(f"<span style='background:{color};color:white;padding:3px 10px;border-radius:4px;"
                f"font-weight:600'>{label}</span>", unsafe_allow_html=True)


def theme_card(fields):
    verdict_badge(fields)
    st.markdown(f"**Property holder:** {fields.get('property_holder', '')}  \n"
                f"**Challenger:** {fields.get('challenger', '')}  \n"
                f"*{fields.get('owner_prevailed_why', '')}*")
    rows = [(THEME_LABELS[name], ", ".join(pretty(v) for v in as_list(fields.get(name))))
            for name in THEMES]
    st.table(pd.DataFrame(rows, columns=["Theme", "Coded as"]).set_index("Theme"))


def similar_cases(fields):
    st.markdown("**Closest cases in my casebook** (by shared themes)")
    for score, other, shared in closest(fields):
        common = ", ".join(pretty(t.split(":")[1]) for t in sorted(shared) if not t.startswith("owner:"))
        st.markdown(f"- **{other['case_name']}** ({other['year']}, {other['class_topic']}) "
                    f"— {OUTCOME.get(other['owner_prevailed'], 'Mixed').lower()}. "
                    f"Shares: {common or 'outcome only'}")


# ---------- page ----------

st.title("Property Case Briefer")
st.caption("Brief any published U.S. case in my Property-notes format, code it on the course's themes, "
           "and see where it fits among the 34 cases in my casebook. AI-drafted study aid: check every "
           "brief against the opinion.")

tab_brief, tab_map, tab_browse = st.tabs(["Brief a case", "Casebook map", "Browse my briefs"])

with tab_brief:
    if not api_key():
        st.error("This app has no OpenRouter key configured.")
    mode = st.radio("Source", ["Look up a citation", "Paste the opinion text"], horizontal=True,
                    label_visibility="collapsed")
    text, citation, name = "", "", ""
    if mode == "Look up a citation":
        example = st.selectbox("Try a case that isn't in my casebook, or type your own below",
                               ["(type a citation)", *EXAMPLES])
        default_cite, default_name = EXAMPLES.get(example, ("", ""))
        c1, c2 = st.columns([1, 1])
        citation = c1.text_input("Citation", value=default_cite, placeholder="81 Vt. 471")
        name = c2.text_input("Case name (optional, helps pick the right opinion)",
                             value=default_name, placeholder="Ploof v. Putnam")
        st.caption("Opinions come from Harvard's Caselaw Access Project, which covers published "
                   "U.S. cases through about 2020.")
    else:
        text = st.text_area("Opinion text", height=220, placeholder="Paste the full opinion…")

    used = st.session_state.setdefault("briefs_used", 0)
    go = st.button("Brief it", type="primary", disabled=used >= MAX_BRIEFS_PER_VISIT or not api_key())
    if used >= MAX_BRIEFS_PER_VISIT:
        st.info(f"That's the {MAX_BRIEFS_PER_VISIT}-brief limit for one visit. Reload later for more.")

    if go:
        try:
            if mode == "Look up a citation":
                if not citation.strip():
                    raise ValueError("enter a citation first")
                with st.spinner("Finding the opinion…"):
                    case, text = lookup(citation.strip(), name.strip())
                st.caption(f"Found: {case.get('name_abbreviation') or case.get('name')} — "
                           f"{case.get('court', {}).get('name')}, {case.get('decision_date')}")
            if len(text.strip()) < 500:
                raise ValueError("that's too short to be an opinion")
            with st.spinner("Reading and briefing the opinion (about 20–60 seconds)…"):
                brief, fields = run_brief(text, DEFAULT_MODEL)
            st.session_state.briefs_used += 1
            st.session_state.last = (brief, fields)
        except Exception as e:  # noqa: BLE001 - show the user what went wrong
            st.error(f"Couldn't brief that case: {e}")

    if "last" in st.session_state:
        brief, fields = st.session_state.last
        st.divider()
        if fields.get("principle"):
            st.markdown(f"> **Principle:** {fields['principle']}")
        left, right = st.columns([3, 2], gap="large")
        with left:
            st.markdown(brief)
            st.download_button("Download brief (.md)", brief + "\n",
                               file_name=re.sub(r"\W+", "_", fields.get("case_name", "brief")) + ".md")
        with right:
            theme_card(fields)
            similar_cases(fields)

with tab_map:
    df = pd.DataFrame(CASEBOOK)
    df["Outcome"] = df["owner_prevailed"].map(OUTCOME).fillna("Mixed")
    won = (df["Outcome"] == "Owner won").sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Owner won", f"{won} of {len(df)}")
    m2.metric("Owner won before 1960", f"{(df[df.year < 1960].Outcome == 'Owner won').sum()} of {(df.year < 1960).sum()}")
    m3.metric("Owner won 1960 on", f"{(df[df.year >= 1960].Outcome == 'Owner won').sum()} of {(df.year >= 1960).sum()}")
    m4.metric("Flexible standards", f"{(df.rule_or_standard == 'flexible_standard').sum()} of {len(df)}")

    theme = st.selectbox("Compare the cases by", list(THEMES), format_func=THEME_LABELS.get)
    long = df.assign(value=df[theme].apply(as_list)).explode("value")
    long["Value"] = long["value"].map(pretty)
    long["Case"] = long["case_name"]
    order = list(OUTCOME_COLORS)
    color = alt.Color("Outcome:N", scale=alt.Scale(domain=order, range=[OUTCOME_COLORS[o] for o in order]),
                      legend=alt.Legend(orient="top", title=None))

    st.markdown(f"**{THEME_LABELS[theme]}: how often the owner won**")
    counts = long.groupby(["Value", "Outcome"]).agg(
        Cases=("Case", "count"), Names=("Case", lambda s: "; ".join(s))).reset_index()
    sort = counts.groupby("Value")["Cases"].sum().sort_values(ascending=False).index.tolist()
    bars = alt.Chart(counts).mark_bar(cornerRadiusEnd=4, stroke="white", strokeWidth=2).encode(
        y=alt.Y("Value:N", sort=sort, title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("Cases:Q", title="Cases", axis=alt.Axis(tickMinStep=1)),
        color=color, order=alt.Order("Outcome:N", sort="descending"),
        tooltip=["Value", "Outcome", "Cases", alt.Tooltip("Names:N", title="Cases")])
    st.altair_chart(bars.properties(height=max(160, 34 * len(sort))), width="stretch")

    st.markdown(f"**Every case by year, grouped by {THEME_LABELS[theme].lower()}**")
    dots = alt.Chart(long).mark_circle(size=140, stroke="white", strokeWidth=2, opacity=1).encode(
        x=alt.X("year:Q", title="Year decided", scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
        y=alt.Y("Value:N", sort=sort, title=None, axis=alt.Axis(labelLimit=220)),
        color=color,
        tooltip=["Case", alt.Tooltip("year:Q", format="d", title="Year"), "class_topic", "Outcome",
                 alt.Tooltip("principle:N", title="Principle")])
    st.altair_chart(dots.properties(height=max(160, 34 * len(sort))), width="stretch")

    with st.expander("Table view"):
        cols = ["case_name", "year", "class_topic", "Outcome", "property_holder", "challenger",
                *THEMES, "principle"]
        st.dataframe(df[cols].map(lambda v: ", ".join(map(pretty, v)) if isinstance(v, list) else v),
                     hide_index=True, width="stretch")

    if SYNTHESIS.exists():
        st.divider()
        st.markdown(SYNTHESIS.read_text())

with tab_browse:
    names = [f"{c['case_name']} ({c['year']}) — {c['class_topic']}" for c in CASEBOOK]
    pick = st.selectbox("Case", range(len(CASEBOOK)), format_func=names.__getitem__)
    case = CASEBOOK[pick]
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(case["brief"])
    with right:
        if case.get("principle"):
            st.markdown(f"> **Principle:** {case['principle']}")
        theme_card(case)
        similar_cases(case)
