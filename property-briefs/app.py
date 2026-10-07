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

from briefing import DEFAULT_MODEL, DOCTRINE_LABEL, TAXONOMY, THEMES, brief_opinion, normalize_topics
from casebook_store import Store, case_key
from caselaw import fetch_case

HERE = Path(__file__).parent
ORIGINAL = json.loads((HERE / "data" / "casebook.json").read_text())
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


# ---------- the casebook: my original 34, plus cases added through the app ----------

def secrets():
    try:
        return dict(st.secrets)
    except Exception:  # noqa: BLE001 - no secrets file when run locally
        return {}


STORE = Store(secrets())


@st.cache_data(ttl=60, show_spinner=False)
def load_added():
    try:
        return STORE.load(), None
    except Exception as e:  # noqa: BLE001 - still show the original casebook
        return [], str(e)


ADDED, ADDED_ERROR = load_added()
for c in ORIGINAL:
    c["source"] = "Original 34"
for c in ADDED:
    c["source"] = "Added"
    normalize_topics(c)
CASEBOOK = ORIGINAL + ADDED
CASEBOOK_KEYS = {case_key(c["case_name"]) for c in CASEBOOK}


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
    out |= {f"doctrine:{d}" for d in case.get("doctrine_tags") or []}
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


def filed_under(case):
    docs = " · ".join(DOCTRINE_LABEL[d] for d in case.get("doctrine_tags") or [])
    return f"{case.get('area', 'Other')}" + (f" › {docs}" if docs else "")


def theme_card(fields):
    st.markdown(f"**Filed under:** {filed_under(fields)}")
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
        common = ", ".join(DOCTRINE_LABEL.get(t.split(":")[1]) if t.startswith("doctrine:") else pretty(t.split(":")[1])
                           for t in sorted(shared) if not t.startswith("owner:"))
        st.markdown(f"- **{other['case_name']}** ({other['year']}, {other['class_topic']}) "
                    f"— {OUTCOME.get(other['owner_prevailed'], 'Mixed').lower()}. "
                    f"Shares: {common or 'outcome only'}")


def add_to_casebook(brief, fields, citation):
    st.divider()
    st.markdown("**Add this case to the casebook**")
    name = (fields.get("case_name") or "").strip()
    if not name:
        st.caption("The model didn't return a case name, so this brief can't be added. Try briefing it again.")
        return
    if case_key(name) in CASEBOOK_KEYS:
        if st.session_state.get("just_added") == name:
            st.success(f"Added {name}. It's in the Casebook map and Browse tabs now.")
        else:
            st.caption(f"{name} is already in the casebook.")
        return
    st.caption(f"It's filed under {filed_under(fields)} and joins the charts, the table and the case "
               "comparisons for everyone who uses this site.")
    if st.button("Add to casebook", key=f"add-{case_key(name)}"):
        entry = dict(fields, case_name=name, citation=citation, class_topic="Not in syllabus", brief=brief,
                     slug=re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), model=DEFAULT_MODEL)
        year = re.search(r"\d{4}", str(fields.get("year", "")))
        entry["year"] = int(year.group()) if year else None
        try:
            with st.spinner("Saving…"):
                added = STORE.add(entry, CASEBOOK_KEYS)
        except Exception as e:  # noqa: BLE001 - show the user what went wrong
            st.error(f"Couldn't save it: {e}")
            return
        if added:
            load_added.clear()
            st.session_state.just_added = name
            st.rerun()
        else:
            st.info(f"{name} is already in the casebook.")


# ---------- page ----------

st.title("Property Case Briefer")
st.caption("Brief any published U.S. case in my Property-notes format, code it on the course's themes, "
           f"and see where it fits among the {len(CASEBOOK)} cases in my casebook. AI-drafted study aid: "
           "check every brief against the opinion.")
if ADDED_ERROR:
    st.warning(f"Couldn't load the cases added through the app, so only the original 34 are shown. ({ADDED_ERROR})")

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
            st.session_state.last = (brief, fields, citation.strip())
        except Exception as e:  # noqa: BLE001 - show the user what went wrong
            st.error(f"Couldn't brief that case: {e}")

    if "last" in st.session_state:
        brief, fields, last_cite = st.session_state.last
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
            add_to_casebook(brief, fields, last_cite)

with tab_map:
    include = True
    if ADDED:
        include = st.toggle(f"Include the {len(ADDED)} case{'s' if len(ADDED) > 1 else ''} added through the app",
                            value=True)
    df = pd.DataFrame(CASEBOOK if include else ORIGINAL)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["Area"] = df["area"].fillna("Other")
    df["doctrine_tags"] = df["doctrine_tags"].apply(lambda v: v if isinstance(v, list) else [])

    f1, f2 = st.columns(2)
    areas = [a for a in [*TAXONOMY, "Other"] if a in set(df["Area"])]
    area = f1.selectbox("Area of property law", ["All areas", *areas])
    if area != "All areas":
        df = df[df["Area"] == area]
    doctrines = [d for d in DOCTRINE_LABEL if any(d in tags for tags in df["doctrine_tags"])]
    picked = f2.multiselect("Doctrines", doctrines, format_func=DOCTRINE_LABEL.get,
                            placeholder="All doctrines in this area")
    if picked:
        df = df[df["doctrine_tags"].apply(lambda tags: bool(set(tags) & set(picked)))]
    scope = ", ".join(DOCTRINE_LABEL[d] for d in picked) if picked else (area if area != "All areas" else "")
    # Charts size by row (alt.Step) and get a fresh key per filter; otherwise Streamlit keeps
    # the old chart height when a filter changes the number of rows.
    view = f"{include}-{area}-{'-'.join(picked)}"
    if scope:
        st.caption(f"Showing the {len(df)} case{'s' if len(df) != 1 else ''} filed under {scope}. "
                   "Every count and chart below covers only these cases.")
    df["Outcome"] = df["owner_prevailed"].map(OUTCOME).fillna("Mixed")
    won = (df["Outcome"] == "Owner won").sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Owner won", f"{won} of {len(df)}")
    m2.metric("Owner won before 1960", f"{(df[df.year < 1960].Outcome == 'Owner won').sum()} of {(df.year < 1960).sum()}")
    m3.metric("Owner won 1960 on", f"{(df[df.year >= 1960].Outcome == 'Owner won').sum()} of {(df.year >= 1960).sum()}")
    m4.metric("Flexible standards", f"{(df.rule_or_standard == 'flexible_standard').sum()} of {len(df)}")

    order = list(OUTCOME_COLORS)
    color = alt.Color("Outcome:N", scale=alt.Scale(domain=order, range=[OUTCOME_COLORS[o] for o in order]),
                      legend=alt.Legend(orient="top", title=None))

    by_doc = df.assign(Doctrine=df["doctrine_tags"].apply(lambda t: [DOCTRINE_LABEL[d] for d in t] or ["Unfiled"]),
                       Case=df["case_name"]).explode("Doctrine")
    doc_counts = by_doc.groupby(["Doctrine", "Outcome"]).agg(
        Cases=("Case", "count"), Names=("Case", lambda s: "; ".join(s))).reset_index()
    doc_sort = doc_counts.groupby("Doctrine")["Cases"].sum().sort_values(ascending=False).index.tolist()
    st.markdown("**By doctrine: how often the owner won**")
    doc_bars = alt.Chart(doc_counts).mark_bar(cornerRadiusEnd=4, stroke="white", strokeWidth=2).encode(
        y=alt.Y("Doctrine:N", sort=doc_sort, title=None, axis=alt.Axis(labelLimit=240)),
        x=alt.X("Cases:Q", title="Cases", axis=alt.Axis(tickMinStep=1)),
        color=color, order=alt.Order("Outcome:N", sort="descending"),
        tooltip=["Doctrine", "Outcome", "Cases", alt.Tooltip("Names:N", title="Cases")])
    st.altair_chart(doc_bars.properties(height=alt.Step(30)), width="stretch", key=f"doc-{view}")

    theme = st.selectbox("Compare the cases by", list(THEMES), format_func=THEME_LABELS.get)
    long = df.assign(value=df[theme].apply(as_list)).explode("value")
    long["Value"] = long["value"].map(pretty)
    long["Case"] = long["case_name"]

    st.markdown(f"**{THEME_LABELS[theme]}: how often the owner won**")
    counts = long.groupby(["Value", "Outcome"]).agg(
        Cases=("Case", "count"), Names=("Case", lambda s: "; ".join(s))).reset_index()
    sort = counts.groupby("Value")["Cases"].sum().sort_values(ascending=False).index.tolist()
    bars = alt.Chart(counts).mark_bar(cornerRadiusEnd=4, stroke="white", strokeWidth=2).encode(
        y=alt.Y("Value:N", sort=sort, title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("Cases:Q", title="Cases", axis=alt.Axis(tickMinStep=1)),
        color=color, order=alt.Order("Outcome:N", sort="descending"),
        tooltip=["Value", "Outcome", "Cases", alt.Tooltip("Names:N", title="Cases")])
    st.altair_chart(bars.properties(height=alt.Step(34)), width="stretch", key=f"bars-{view}-{theme}")

    st.markdown(f"**Every case by year, grouped by {THEME_LABELS[theme].lower()}**")
    dots = alt.Chart(long).mark_point(filled=True, stroke="white", strokeWidth=2, opacity=1).encode(
        x=alt.X("year:Q", title="Year decided", scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
        y=alt.Y("Value:N", sort=sort, title=None, axis=alt.Axis(labelLimit=220)),
        color=color,
        size=alt.condition(alt.datum.source == "Added", alt.value(320), alt.value(140)),
        shape=alt.Shape("source:N", scale=alt.Scale(domain=["Original 34", "Added"], range=["circle", "diamond"]),
                        legend=alt.Legend(orient="top", title=None) if ADDED else None),
        tooltip=["Case", alt.Tooltip("year:Q", format="d", title="Year"), "Area", "Outcome",
                 alt.Tooltip("principle:N", title="Principle")])
    st.altair_chart(dots.properties(height=alt.Step(34)), width="stretch", key=f"dots-{view}-{theme}")

    with st.expander("Table view"):
        cols = ["case_name", "year", "Area", "Doctrines", "class_topic", "source", "Outcome", "property_holder", "challenger",
                *THEMES, "principle"]
        df["Doctrines"] = df["doctrine_tags"].apply(lambda t: ", ".join(DOCTRINE_LABEL[d] for d in t))
        st.dataframe(df[cols].map(lambda v: ", ".join(map(pretty, v)) if isinstance(v, list) else v),
                     hide_index=True, width="stretch")

    if SYNTHESIS.exists():
        st.divider()
        if ADDED:
            st.caption("The written synthesis below covers the original 34 cases; the charts and table above "
                       "include the added ones.")
        st.markdown(SYNTHESIS.read_text())

with tab_browse:
    b1, b2 = st.columns([1, 2])
    browse_area = b1.selectbox("Area", ["All areas", *[a for a in [*TAXONOMY, "Other"]
                                                      if any(c.get("area", "Other") == a for c in CASEBOOK)]])
    shown = sorted((c for c in CASEBOOK if browse_area in ("All areas", c.get("area", "Other"))),
                   key=lambda c: (list(TAXONOMY).index(c["area"]) if c.get("area") in TAXONOMY else 99,
                                  filed_under(c), c.get("year") or 0))
    names = [f"{c['case_name']} ({c['year']}) — {filed_under(c)}" + (" · added" if c["source"] == "Added" else "")
             for c in shown]
    pick = b2.selectbox("Case", range(len(shown)), format_func=names.__getitem__)
    case = shown[pick]
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(case["brief"])
    with right:
        if case.get("principle"):
            st.markdown(f"> **Principle:** {case['principle']}")
        theme_card(case)
        similar_cases(case)
