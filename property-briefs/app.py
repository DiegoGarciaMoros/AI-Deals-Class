"""Foundations of Property Law: brief any U.S. case in my format and place it in my casebook.

Run locally:   streamlit run app.py   (with OPENROUTER_API_KEY in the environment)
Deploy:        Streamlit Community Cloud, with OPENROUTER_API_KEY in the app's Secrets.
"""
import json
import os
import random
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from briefing import DEFAULT_MODEL, DOCTRINE_LABEL, TAXONOMY, THEMES, brief_opinion, normalize_topics
from casebook_store import Store, case_key, setting
import doctrine
import practice
import search
import stats
import treatises
from caselaw import fetch_case

HERE = Path(__file__).parent
ORIGINAL = json.loads((HERE / "data" / "casebook.json").read_text())
SYNTHESIS = HERE / "data" / "course_synthesis.md"
MAX_BRIEFS_PER_VISIT = 8  # every brief is paid for with my OpenRouter key
MAX_AI_PER_VISIT = 40  # practice: new questions, grading, freestyle answers (cheap model)
BANK_PATH = HERE / "data" / "question_bank.json"
OVERVIEW_PATH = HERE / "data" / "overview.json"

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
    "State v. Shack (right to exclude, 1971)": ("58 N.J. 297", "State v. Shack"),
    "Boomer v. Atlantic Cement (nuisance remedies, 1970)": ("26 N.Y.2d 219", "Boomer v. Atlantic Cement Co."),
    "Van Valkenburgh v. Lutz (adverse possession, 1952)": ("304 N.Y. 95", "Van Valkenburgh v. Lutz"),
    "Hadacheck v. Sebastian (land use, 1915)": ("239 U.S. 394", "Hadacheck v. Sebastian"),
}

st.set_page_config(page_title="Foundations of Property Law", page_icon="⚖️", layout="wide")


# ---------- the casebook: my syllabus cases, plus cases added through the app ----------

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
    c["source"] = "Syllabus"
for c in ADDED:
    c["source"] = "Added"
    normalize_topics(c)
CASEBOOK = ORIGINAL + ADDED
CASEBOOK_KEYS = {case_key(c["case_name"]) for c in CASEBOOK}
CASE_BY_SLUG = {c["slug"]: c for c in CASEBOOK}
CASE_BY_KEY = {case_key(c["case_name"]): c for c in CASEBOOK}


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
        entry = dict(fields, case_name=name, citation=citation, class_topic="Not in syllabus", chapter=fields.get("area", "Other"), brief=brief,
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




# ---------- links to briefs, question bank, overview ----------

ALIASES = {"insvap": case_key("International News Service v. Associated Press")}


def find_case(name):
    """The casebook case a cited name refers to: exact name, then a looser match."""
    key = ALIASES.get(case_key(name), case_key(name))
    if key in CASE_BY_KEY:
        return CASE_BY_KEY[key]
    loose = [c for k, c in CASE_BY_KEY.items() if key and (key in k or k in key)]
    starts = [c for k, c in CASE_BY_KEY.items() if key and k.startswith(key)]
    for found in (loose, starts):
        if len(found) == 1:
            return found[0]
    # Short forms ("Gillmor v. Gillmor" vs. a longer caption): both parties must match.
    parts = str(name).split(" v. ")
    if len(parts) != 2:
        return None
    first, second = case_key(parts[0]), case_key(parts[1])
    matches = [c for k, c in CASE_BY_KEY.items()
               if len(first) > 3 and k.startswith(first) and len(second) > 3 and second[:6] in k]
    return matches[0] if len(matches) == 1 else None


def case_link(name):
    """Markdown link that opens the case's brief in this app (?case=slug), or plain italics."""
    c = find_case(name)
    return f"[*{c['case_name']}*](?case={c['slug']})" if c else f"*{name}*"


def linkify(text):
    """Turn [[Case Name]] citations into links to the briefs."""
    return re.sub(r"\[\[(.+?)\]\]", lambda m: case_link(m.group(1)), text or "")


@st.cache_data(show_spinner=False)
def load_json(path, mtime):
    return json.loads(path.read_text()) if path.exists() else ([] if path == BANK_PATH else {})


def mtime(path):
    return path.stat().st_mtime if path.exists() else 0


def ai_budget_left():
    return MAX_AI_PER_VISIT - st.session_state.setdefault("ai_used", 0)


def spend_ai():
    st.session_state.ai_used = st.session_state.get("ai_used", 0) + 1


def cl_token():
    return setting("COURTLISTENER_TOKEN", secrets())


@st.cache_data(ttl=3600, show_spinner=False)
def cl_search(filters, page_url=None):
    return search.search(token=cl_token(), page_url=page_url, **filters)


def do_brief(text, citation=""):
    """Brief an opinion's text and keep it as the current brief."""
    if len(text.strip()) < 500:
        raise ValueError("that's too short to be an opinion")
    with st.spinner("Reading and briefing the opinion (about 20–60 seconds)…"):
        brief, fields = run_brief(text, DEFAULT_MODEL)
    st.session_state.briefs_used = st.session_state.get("briefs_used", 0) + 1
    st.session_state.last = (brief, fields, citation.strip())


def search_panel():
    with st.form("case-search"):
        name = st.text_input("Case name", placeholder="e.g. State v. Shack, Boomer v. Atlantic Cement, Kelo")
        with st.expander("Advanced search: jurisdiction, court level, dates, terms & connectors"):
            terms = st.text_input("Terms & connectors", placeholder='"right to exclude" AND (migrant OR farmworker)')
            st.caption(search.SYNTAX_HELP)
            a1, a2 = st.columns(2)
            juris = a1.multiselect("Jurisdiction", list(search.COURTS), placeholder="All jurisdictions")
            levels = a2.multiselect("Court level", list(search.LEVELS), format_func=search.LEVELS.get,
                                    placeholder="All levels")
            b1, b2, b3 = st.columns(3)
            year_from = b1.number_input("Decided from (year)", 1600, 2100, value=None, step=1, placeholder="any")
            year_to = b2.number_input("Decided through (year)", 1600, 2100, value=None, step=1, placeholder="any")
            cited = b3.number_input("Cited by at least", 0, 100_000, 0, step=5)
            c1, c2, c3 = st.columns(3)
            citation = c1.text_input("Citation", placeholder="58 N.J. 297")
            judge = c2.text_input("Judge", placeholder="Cardozo")
            docket = c3.text_input("Docket number")
            d1, d2 = st.columns(2)
            sort = d1.selectbox("Sort by", list(search.SORTS))
            published = d2.checkbox("Published (precedential) opinions only", value=True)
            extra = st.text_input("CourtListener court IDs (optional)", placeholder="e.g. nyappdiv calctapp",
                                  help="For courts not in the lists above; see courtlistener.com/help/api/jurisdictions/")
        submitted = st.form_submit_button("Search", type="primary")
    if submitted:
        filters = dict(name=name, terms=terms, citation=citation, jurisdictions=tuple(juris), levels=tuple(levels),
                       extra_courts=extra, year_from=year_from, year_to=year_to, judge=judge,
                       cited_at_least=cited, docket=docket, published_only=published, sort=sort)
        if not any([name.strip(), terms.strip(), citation.strip(), judge.strip(), docket.strip(), juris, extra.strip()]):
            st.warning("Type a case name, or set at least one advanced filter.")
        else:
            try:
                with st.spinner("Searching CourtListener…"):
                    results, count, nxt = cl_search(filters)
                st.session_state.search = {"filters": filters, "results": results, "count": count, "next": nxt}
            except Exception as e:  # noqa: BLE001 - show the user what went wrong
                st.session_state.pop("search", None)
                st.error(f"Search failed: {e}")
    found = st.session_state.get("search")
    if not found:
        st.caption("Searches every published U.S. opinion in CourtListener (Free Law Project).")
        return
    results = found["results"]
    st.markdown(f"**{found['count'] or 0:,} result{'s' if found['count'] != 1 else ''}**"
                + (f", showing {len(results)}" if found["count"] and found["count"] > len(results) else ""))
    if not results:
        st.info("No cases matched. Loosen a filter, or check the spelling of the case name.")
    for i, r in enumerate(results):
        with st.container(border=True):
            in_book = find_case(r["name"])
            title = f"**{r['name']}**" + (f" · [in my casebook](?case={in_book['slug']})" if in_book else "")
            st.markdown(title)
            meta = " · ".join(x for x in [r["court"], r["date"], ", ".join(r["citations"][:2]),
                                          f"cited by {r['cited_by']:,}" if r["cited_by"] else ""] if x)
            st.caption(meta)
            if r["snippet"]:
                st.markdown(f"> {r['snippet']}")
            c1, c2 = st.columns([1, 3])
            if c1.button("Brief this case", key=f"brief-result-{i}-{r['cluster_id']}",
                         disabled=st.session_state.get("briefs_used", 0) >= MAX_BRIEFS_PER_VISIT or not api_key()):
                try:
                    with st.spinner("Getting the full opinion…"):
                        text, source = search.full_text(r, cl_token())
                    st.caption(f"Opinion text from {source}.")
                    do_brief(text, r["citations"][0] if r["citations"] else "")
                except Exception as e:  # noqa: BLE001 - show the user what went wrong
                    st.error(f"Couldn't brief that case: {e}")
            if r["url"]:
                c2.markdown(f"[Read it on CourtListener]({r['url']})")
    if found.get("next") and st.button("Load more results"):
        try:
            more, _, nxt = cl_search(found["filters"], page_url=found["next"])
            found["results"] = results + more
            found["next"] = nxt
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Couldn't load more: {e}")

# ---------- page ----------

st.title("Foundations of Property Law")
st.caption("Brief any published U.S. case in my Property-notes format, code it on the course's themes, "
           f"and see where it fits among the {len(CASEBOOK)} cases in my casebook. AI-drafted study aid: "
           "check every brief against the opinion.")
if ADDED_ERROR:
    st.warning(f"Couldn't load the cases added through the app, so only the syllabus cases are shown. ({ADDED_ERROR})")

TARGET = st.query_params.get("case")
TARGET = TARGET if TARGET in CASE_BY_SLUG else None
tab_brief, tab_overview, tab_treatises, tab_practice, tab_map, tab_stats, tab_browse = st.tabs(
    ["Brief a case", "Doctrinal overview", "Treatises on Property Law", "Practice", "Casebook map", "Statistics",
     "Browse my briefs"],
    default="Browse my briefs" if TARGET else None)

with tab_brief:
    if not api_key():
        st.error("This app has no OpenRouter key configured.")
    mode = st.radio("Source", ["Search for a case", "Look up a citation", "Paste the opinion text"], horizontal=True,
                    label_visibility="collapsed")
    text, citation, name = "", "", ""
    if mode == "Search for a case":
        search_panel()
    elif mode == "Look up a citation":
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
    go = mode != "Search for a case" and st.button(
        "Brief it", type="primary", disabled=used >= MAX_BRIEFS_PER_VISIT or not api_key())
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
            do_brief(text, citation)
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

def render_unit(unit, label, u):
    """One class unit: hand-written guide or AI rules, diagrams, case table, tensions, traps, tip."""
    cases = sorted((c for c in CASEBOOK if (c.get("doctrine_tags") or [None])[0] == unit),
                   key=lambda c: c.get("year") or 0)
    won = sum(c["owner_prevailed"] == "yes" for c in cases)
    st.subheader(label)
    if cases:
        st.caption(f"Class {cases[0].get('class_no', '')} · owner won {won} of {len(cases)} · "
                   + ", ".join(case_link(c["case_name"]) for c in cases))
    u = u if isinstance(u, dict) else {}
    guide = doctrine.GUIDES.get(unit)
    if guide:
        st.markdown(linkify(guide))
    else:
        if u.get("summary"):
            st.info(linkify(u["summary"]))
        if u.get("rules"):
            st.markdown("#### Black-letter rules")
            st.markdown("\n".join(
                f"{i}. {linkify(r.get('rule', ''))}"
                + (f" ({', '.join(linkify(c) for c in r.get('cases', []) if c not in r.get('rule', ''))})"
                   if [c for c in r.get("cases", []) if c not in r.get("rule", "")] else "")
                for i, r in enumerate(u["rules"], 1)))
    for title, chart, caption in doctrine.DIAGRAMS.get(unit, []):
        st.markdown(f"#### {title}")
        st.graphviz_chart(chart)
        if caption:
            st.caption(caption)
    rows = u.get("cases") or []
    if rows:
        st.markdown("#### The cases")
        cell = lambda t: str(t or "").replace("|", "/").replace("\n", " ")  # noqa: E731
        table = ["| Case | Question | Holding | Why it matters |", "|---|---|---|---|"]
        table += [f"| {linkify(cell(r.get('case')))} ({r.get('year', '')}) | {cell(r.get('question'))} | "
                  f"{linkify(cell(r.get('answer')))} | {linkify(cell(r.get('why')))} |" for r in rows]
        st.markdown("\n".join(table))
    t1, t2 = st.columns(2)
    with t1:
        if u.get("tensions"):
            st.markdown("#### Tensions and policy")
            st.markdown("\n".join(f"- {linkify(t)}" for t in u["tensions"]))
    with t2:
        if u.get("traps"):
            st.markdown("#### Exam traps")
            st.markdown("\n".join(f"- {linkify(t)}" for t in u["traps"]))
    if u.get("exam_tip") and not guide:
        st.success(f"**Exam tip:** {linkify(u['exam_tip'])}")
    if not u and not guide:
        st.caption("The study guide for this unit hasn't been written yet.")


with tab_overview:
    OVERVIEW = load_json(OVERVIEW_PATH, mtime(OVERVIEW_PATH))
    st.caption("A study guide to each part of the syllabus: the rules, diagrams, how the cases fit, and exam "
               "traps. Case names link to their briefs. The estates units are hand-written; the rest is "
               "AI-written from my briefs and reviewed, so check it against the cases and your class notes.")
    chapter = st.selectbox("Syllabus chapter", list(TAXONOMY), key="ov-chapter")
    entry = OVERVIEW.get(chapter) or {}
    st.header(chapter)
    if entry.get("intro"):
        st.markdown(linkify(entry["intro"]))
    unit_labels = TAXONOMY[chapter]
    picked_unit = st.pills("Class unit", list(unit_labels), format_func=unit_labels.get,
                           default=list(unit_labels)[0], key=f"ov-unit-{chapter}") or list(unit_labels)[0]
    st.divider()
    render_unit(picked_unit, unit_labels[picked_unit], (entry.get("units") or {}).get(picked_unit))

with tab_treatises:
    st.caption("Briefs of the academic readings: first the articles the syllabus assigns (with class and pages), "
               "then the theorists excerpted in the casebook. Case names link to their briefs.")
    st.subheader("Assigned on the syllabus")
    for i, t in enumerate(treatises.ASSIGNED):
        with st.expander(f"**{t['author']}**, *{t['title']}*", expanded=i == 0):
            st.caption(f"{t['cite']} · Assigned: {t['assigned']}")
            st.info(t["one_line"])
            st.markdown("**The argument**\n" + "\n".join(f"- {linkify(x)}" for x in t["argument"]))
            st.markdown(f"**Key terms:** {t['terms']}")
            st.markdown(f"**Connects to:** {linkify(t['cases'])}")
            st.success(f"**On the exam:** {t['exam']}")
            st.markdown(f"**Limits:** {linkify(t['critique'])}")
    st.subheader("Also in the casebook readings")
    st.markdown("\n".join(
        f"- **{t['author']}**, *{t['title']}*, {t['cite']}. {t['one_line']} Connects to: {linkify(t['cases'])}"
        for t in treatises.CASEBOOK))

with tab_practice:
    BANK = load_json(BANK_PATH, mtime(BANK_PATH))
    st.caption("Exam-style questions from my briefs. Multiple-choice answer keys in the question bank were "
               "checked by a second AI model answering blind; short answers are graded by AI against a rubric. "
               "Treat both as practice, not gospel.")
    pmode = st.radio("Practice", ["By topic", "By case", "Ask anything"], horizontal=True, label_visibility="collapsed")
    qtype = None
    if pmode != "Ask anything":
        qtype = st.radio("Question type", ["Multiple choice", "Short answer", "Both"], horizontal=True)
    want = {"Multiple choice": {"mc"}, "Short answer": {"sa"}, "Both": {"mc", "sa"}}.get(qtype, {"mc", "sa"})
    levels = st.pills("Difficulty", ["easy", "medium", "hard"], selection_mode="multi",
                      default=["easy", "medium", "hard"], format_func=str.capitalize, key="pq-level") \
        or ["easy", "medium", "hard"]
    level_for_new = levels[0] if len(levels) == 1 else None  # one level picked: new questions match it

    pool, scope_cases, scope_label = [], [], ""
    if pmode == "By topic":
        p1, p2 = st.columns(2)
        pchapter = p1.selectbox("Syllabus chapter", list(TAXONOMY), key="pq-chapter")
        units = list(TAXONOMY[pchapter])
        punit = p2.selectbox("Class unit", ["All units in this chapter", *units],
                             format_func=lambda u: DOCTRINE_LABEL.get(u, u), key="pq-unit")
        chosen = units if punit == "All units in this chapter" else [punit]
        pool = [q for q in BANK if q["unit"] in chosen and q["type"] in want and q.get("difficulty", "medium") in levels]
        scope_cases = [c for u in chosen for c in practice.unit_cases(CASEBOOK, u)]
        scope_label = (f"the class unit '{DOCTRINE_LABEL[punit]}'" if punit in DOCTRINE_LABEL
                       else f"the syllabus chapter '{pchapter}'")
    elif pmode == "By case":
        ordered = sorted(CASEBOOK, key=lambda c: (c.get("class_no") or 99, c.get("year") or 0))
        pcase = st.selectbox("Case", ordered, format_func=lambda c: (f"Class {c['class_no']} · " if c.get("class_no") else "")
                             + f"{c['case_name']} ({c.get('year')})", key="pq-case")
        pool = [q for q in BANK if q["type"] in want and q.get("difficulty", "medium") in levels
                and (q.get("case_slug") == pcase["slug"] or
                (q["kind"] == "unit" and any(find_case(n) is pcase for n in q.get("cases", []))))]
        scope_cases = [pcase]
        scope_label = f"the case {pcase['case_name']} ({pcase.get('year')})"
    else:
        query = st.text_area("Ask about any property topic, or name one to be quizzed on",
                             placeholder="e.g. When does a finder beat the landowner? · How do Penn Central and Lucas fit together? "
                                         "· Quiz me on the implied warranty of habitability", key="pq-query")
        scope_cases = practice.retrieve(CASEBOOK, query) if query.strip() else []
        scope_label = f"this topic: {query.strip()}"
        f1, f2, f3 = st.columns(3)
        out_of_ai = ai_budget_left() <= 0
        ask = f1.button("Answer my question", type="primary", disabled=out_of_ai)
        quiz_mc = f2.button("Quiz me: multiple choice", disabled=out_of_ai)
        quiz_sa = f3.button("Quiz me: short answer", disabled=out_of_ai)
        if (ask or quiz_mc or quiz_sa) and not query.strip():
            st.warning("Type a question or a topic first.")
            ask = quiz_mc = quiz_sa = False
        if ask:
            try:
                with st.spinner("Thinking it through…"):
                    spend_ai()
                    st.session_state.tutor = (query, practice.tutor(api_key(), query, practice.brief_context(scope_cases)))
            except Exception as e:  # noqa: BLE001
                st.error(f"Couldn't answer that: {e}")
        if st.session_state.get("tutor") and st.session_state.tutor[0] == query:
            with st.container(border=True):
                st.markdown(st.session_state.tutor[1])
                st.caption("Drawn from: " + ", ".join(case_link(c["case_name"]) for c in scope_cases))
        if quiz_mc or quiz_sa:
            want = {"mc"} if quiz_mc else {"sa"}
            st.session_state.make_new = True

    # pick or write the current question
    seen = st.session_state.setdefault("seen_q", set())
    n1, n2, n3 = st.columns([1, 1, 2])
    if pmode != "Ask anything":
        if n1.button("Next question", type="primary", disabled=not pool):
            fresh = [q for q in pool if q["id"] not in seen] or pool
            st.session_state.current_q = random.choice(fresh)
            st.session_state.current_ctx = [c["slug"] for c in scope_cases]
        if n2.button("Write me a new one (AI)", disabled=ai_budget_left() <= 0 or not scope_cases):
            st.session_state.make_new = True
        n3.caption(f"{len(pool)} question{'s' if len(pool) != 1 else ''} in the bank for this selection."
                   if pool else "No bank questions match these filters yet. Use \"Write me a new one\" to make one at "
                   "the chosen difficulty.")
    if st.session_state.pop("make_new", False):
        try:
            with st.spinner("Writing a question…"):
                spend_ai()
                ctx = practice.brief_context(scope_cases)
                kind = "mc" if want == {"mc"} else "sa" if want == {"sa"} else random.choice(["mc", "sa"])
                made = practice.generate(api_key(), scope_label, ctx, n_mc=int(kind == "mc"), n_sa=int(kind == "sa"),
                                         difficulty=level_for_new or random.choice(levels))
            if not made:
                raise ValueError("the model didn't return a usable question; try again")
            q = made[0]
            q.update(id=f"live-{random.randint(0, 10**9)}", kind="live", unit=(scope_cases[0].get("doctrine_tags") or ["other"])[0],
                     scope=scope_label, live=True)
            st.session_state.current_q = q
            st.session_state.current_ctx = [c["slug"] for c in scope_cases]
        except Exception as e:  # noqa: BLE001
            st.error(f"Couldn't write a question: {e}")

    q = st.session_state.get("current_q")
    if q:
        seen.add(q["id"])
        ctx_cases = [CASE_BY_SLUG[s] for s in st.session_state.get("current_ctx", []) if s in CASE_BY_SLUG]
        ctx_cases += [c for c in (find_case(n) for n in q.get("cases", [])) if c and c not in ctx_cases]
        context = practice.brief_context(ctx_cases)
        with st.container(border=True):
            label = "Multiple choice" if q["type"] == "mc" else "Short answer"
            origin = "freshly written by AI (key not double-checked)" if q.get("live") else "question bank"
            st.caption(f"{label} · {q.get('difficulty', '')} · {DOCTRINE_LABEL.get(q.get('unit'), '')} · {origin}")
            st.markdown(q["stem"])
            answers = st.session_state.setdefault("answers", {})
            if q["type"] == "mc":
                pick = st.radio("Your answer", list(q["options"]), index=None, key=f"mc-{q['id']}",
                                format_func=lambda k: f"{k}. {q['options'][k]}")
                if st.button("Check answer", disabled=pick is None, key=f"check-{q['id']}"):
                    answers[q["id"]] = {"type": "mc", "pick": pick, "right": pick == q["answer"]}
                result = answers.get(q["id"])
                if result:
                    if result["right"]:
                        st.success(f"Correct: {q['answer']}.")
                    else:
                        st.error(f"Not quite. You chose {result['pick']}; the best answer is {q['answer']}.")
                    st.markdown(f"**Why:** {q.get('explanation', '')}")
                    for k in q["options"]:
                        mark = "✅" if k == q["answer"] else ("❌" if k == result["pick"] else "▫️")
                        st.markdown(f"{mark} **{k}.** {q['why'].get(k, '')}")
            else:
                text = st.text_area("Your answer (aim for IRAC: issue, rule, application, conclusion)", height=220,
                                    key=f"sa-{q['id']}")
                grade_it = st.button("Grade my answer", type="primary", key=f"grade-{q['id']}",
                                     disabled=ai_budget_left() <= 0)
                if grade_it and len(text.strip()) < 40:
                    st.warning("Write a fuller answer first (a few sentences at least).")
                elif grade_it:
                    try:
                        with st.spinner("Grading…"):
                            spend_ai()
                            answers[q["id"]] = {"type": "sa", "grade": practice.grade(api_key(), q, text, context)}
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Couldn't grade that: {e}")
                result = answers.get(q["id"])
                if result:
                    g = result["grade"]
                    g1, g2 = st.columns([1, 4])
                    g1.metric("Score", f"{g['score']:g} / 10")
                    g2.markdown(f"**{g.get('verdict', '')}**")
                    if g.get("rubric_scores"):
                        st.dataframe(pd.DataFrame(g["rubric_scores"]).rename(columns={
                            "point": "Rubric point", "earned": "Earned", "max": "Out of", "comment": "Comment"}),
                            hide_index=True, width="stretch")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**What worked**")
                        for x in g.get("strengths", []):
                            st.markdown(f"- {x}")
                    with c2:
                        st.markdown("**What to fix**")
                        for x in g.get("gaps", []):
                            st.markdown(f"- {x}")
                    if g.get("cases_to_cite"):
                        st.markdown("**Cases you could cite**")
                        for x in g["cases_to_cite"]:
                            st.markdown(f"- {case_link(x.get('case', ''))}: {x.get('why', '')}")
                    if g.get("doctrines_to_use"):
                        st.markdown("**Doctrine to bring in**")
                        for x in g["doctrines_to_use"]:
                            st.markdown(f"- **{x.get('doctrine', '')}**: {x.get('why', '')}")
                    with st.expander("Your answer, improved"):
                        st.markdown(g.get("improved_answer", ""))
                    with st.expander("Model answer and rubric"):
                        st.markdown(q.get("model_answer", ""))
                        for r in q.get("rubric", []):
                            st.markdown(f"- ({r.get('points', '?')} pts) {r['point']}")
                    if g.get("next_step"):
                        st.info(f"Next: {g['next_step']}")
            if q.get("cases") or q.get("doctrines"):
                st.caption("Cases: " + ", ".join(case_link(n) for n in q.get("cases", []))
                           + (" · Doctrine: " + ", ".join(q.get("doctrines", [])) if q.get("doctrines") else ""))

    answers = st.session_state.get("answers", {})
    mc = [a for a in answers.values() if a["type"] == "mc"]
    sa = [a["grade"]["score"] for a in answers.values() if a["type"] == "sa"]
    if mc or sa:
        s1, s2, s3 = st.columns(3)
        s1.metric("Multiple choice this visit", f"{sum(a['right'] for a in mc)} / {len(mc)}")
        s2.metric("Short-answer average", f"{sum(sa) / len(sa):.1f} / 10" if sa else "—")
        s3.metric("AI requests left this visit", ai_budget_left())

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
    area = f1.selectbox("Syllabus chapter", ["All chapters", *areas])
    if area != "All chapters":
        df = df[df["Area"] == area]
    doctrines = [d for d in DOCTRINE_LABEL if any(d in tags for tags in df["doctrine_tags"])]
    picked = f2.multiselect("Class units", doctrines, format_func=DOCTRINE_LABEL.get,
                            placeholder="All units in this chapter")
    if picked:
        df = df[df["doctrine_tags"].apply(lambda tags: bool(set(tags) & set(picked)))]
    scope = ", ".join(DOCTRINE_LABEL[d] for d in picked) if picked else (area if area != "All chapters" else "")
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
    st.markdown("**By class unit: how often the owner won** (a case counts in its own unit and one more it speaks to)")
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
        shape=alt.Shape("source:N", scale=alt.Scale(domain=["Syllabus", "Added"], range=["circle", "diamond"]),
                        legend=alt.Legend(orient="top", title=None) if ADDED else None),
        tooltip=["Case", alt.Tooltip("year:Q", format="d", title="Year"), "Area", "Outcome",
                 alt.Tooltip("principle:N", title="Principle")])
    st.altair_chart(dots.properties(height=alt.Step(34)), width="stretch", key=f"dots-{view}-{theme}")

    with st.expander("Table view"):
        cols = ["case_name", "year", "Area", "Units", "class_topic", "source", "Outcome", "property_holder", "challenger",
                *THEMES, "principle"]
        df["Units"] = df["doctrine_tags"].apply(lambda t: ", ".join(DOCTRINE_LABEL[d] for d in t))
        st.dataframe(df[cols].map(lambda v: ", ".join(map(pretty, v)) if isinstance(v, list) else v),
                     hide_index=True, width="stretch")

    if SYNTHESIS.exists():
        st.divider()
        if ADDED:
            st.caption("The written synthesis below was written from the casebook before the added cases; the charts and table above "
                       "include the added ones.")
        st.markdown(SYNTHESIS.read_text())

def _mix(hex_a, hex_b, t):
    a, b = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in (hex_a, hex_b))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def shaded(table, kind, counts=None):
    """Shade a cross-table in the outcome colors. kind="count": white to blue by count;
    kind="rate": orange (0%) through white (50%) to blue (100%). Empty cells stay blank."""
    top = max(1, table.max().max()) if kind == "count" else 100

    def css(v):
        if pd.isna(v) or (kind == "count" and v == 0):
            return "color: #9a9a9a"
        if kind == "count":
            return f"background-color: {_mix('#ffffff', '#7fb0eb', v / top)}"
        return f"background-color: {_mix('#f6b493', '#ffffff', v / 50) if v < 50 else _mix('#ffffff', '#8db8ee', (v - 50) / 50)}"

    display = table.map(lambda v: "" if pd.isna(v) else (f"{v:.0f}%" if kind == "rate" else f"{v:.0f}"))
    if counts is not None:  # "40% (5)": the rate and how many cases it rests on
        display = display.where(table.isna(), display + counts.reindex_like(table).map(lambda n: f" ({n:.0f})"))
    styles = table.map(css)
    return display.style.apply(lambda _: styles, axis=None)


def outcome_chart(long, col, order, key):
    """100% bars per category: share of cases the owner won / mixed / lost, n in the label."""
    data = long.assign(Category=long[col].astype(str), Case=long["case_name"])
    n = data.groupby("Category")["Case"].count()
    order = [o for o in order if o in n.index]
    labels = {o: f"{o}  ({n[o]})" for o in order}
    data["Row"] = data["Category"].map(labels)
    counts = data.groupby(["Row", "Outcome"]).agg(Cases=("Case", "count"),
                                                 Names=("Case", lambda s: "; ".join(s))).reset_index()
    stack = ["Owner won", "Mixed", "Owner lost"]
    counts["o"] = counts["Outcome"].map(stack.index)
    chart = alt.Chart(counts).mark_bar(stroke="white", strokeWidth=2).encode(
        y=alt.Y("Row:N", sort=[labels[o] for o in order], title=None, axis=alt.Axis(labelLimit=320)),
        x=alt.X("Cases:Q", stack="normalize", title="Share of cases", axis=alt.Axis(format="%", tickCount=5)),
        color=alt.Color("Outcome:N", scale=alt.Scale(domain=stack, range=[OUTCOME_COLORS[o] for o in stack]),
                        legend=alt.Legend(orient="top", title=None)),
        order=alt.Order("o:Q"),
        tooltip=[alt.Tooltip("Row:N", title=col.replace("_", " ").capitalize()), "Outcome", "Cases",
                 alt.Tooltip("Names:N", title="Cases")])
    st.altair_chart(chart.properties(height=alt.Step(26)), width="stretch", key=key)


with tab_stats:
    st.markdown("Every table asks one question, **when does the owner win?**, against a different factor. "
                "Win % counts mixed outcomes as not won. Click a column header to sort; hover a table to "
                "download it as CSV.")
    include_s = st.toggle("Include cases added through the app", value=True, key="stats-include") if ADDED else True
    sdf = stats.frame(CASEBOOK if include_s else ORIGINAL)
    pct = lambda label: st.column_config.ProgressColumn(label, format="%d%%", min_value=0, max_value=100)  # noqa: E731
    pct_cols = ["Owner win %", "Flexible standard %", "Property rule %", "Court made new law %", "Dissent %"]
    pct_config = {c: pct(c) for c in pct_cols}
    fit = lambda table: 38 + 35 * len(table)  # noqa: E731 - tall enough to show every row

    era_order = [e for _, _, e in stats.ERAS]
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("**The owner over time**")
        outcome_chart(sdf, "era", era_order, "chart-era")
    with e2:
        st.markdown("**Owner suing vs. being sued**")
        outcome_chart(sdf.assign(owner_role=sdf["owner_role"].map(
            {"plaintiff": "Owner was plaintiff", "defendant": "Owner was defendant", "unclear": "Unclear"})),
            "owner_role", ["Owner was plaintiff", "Owner was defendant", "Unclear"], "chart-role")

    st.subheader("1. By syllabus chapter")
    outcome_chart(sdf, "chapter", [*TAXONOMY, "Other"], "chart-chapter")
    chapters = stats.by_chapter(sdf)
    st.dataframe(chapters, hide_index=True, width="stretch", height=fit(chapters), column_config=pct_config)

    st.subheader("2. By class unit")
    st.caption("Each case counted once, in its own syllabus unit.")
    unit_order = [label for docs in TAXONOMY.values() for label in docs.values()] + ["Other"]
    with st.expander("Chart: every class unit", expanded=False):
        outcome_chart(sdf, "unit_label", unit_order, "chart-unit")
    units = stats.by_unit(sdf)
    st.dataframe(units, hide_index=True, width="stretch", height=fit(units), column_config=pct_config)

    st.subheader("3. By factor")
    factor = st.selectbox("Factor", [f for f in stats.FACTORS if f not in ("chapter", "unit_label")],
                          format_func=lambda f: stats.FACTORS[f][0], key="stats-factor")
    if stats.FACTORS[factor][1]:
        st.caption("Cases can have several values here, so rows add up to more than the number of cases.")
    factor_table = stats.by_factor(sdf, factor)
    outcome_chart(stats.explode(sdf, factor), "Value", list(factor_table["Value"]), f"chart-factor-{factor}")
    st.dataframe(factor_table, hide_index=True, width="stretch", height=min(fit(factor_table), 500),
                 column_config={"Owner win %": pct("Owner win %"),
                                "Cases (by year)": st.column_config.TextColumn("Cases (by year)", width="large")})

    st.markdown(f"**{stats.FACTORS[factor][0]} × syllabus chapter** (number of cases)")
    ct = stats.crosstab(sdf, factor)
    ct.columns = [c.split(". ", 1)[0] for c in ct.columns]  # chapter numbers keep it narrow
    st.dataframe(shaded(ct, "count"), width="stretch", height=fit(ct))
    st.caption("Columns are syllabus chapters: " + "; ".join(f"{n}. {name}" for n, name in
               (c.split(". ", 1) for c in TAXONOMY)))

    st.markdown(f"**{stats.FACTORS[factor][0]} × era** (owner win %, with the number of cases in brackets; "
                "blue = owner usually won, orange = usually lost, blank = no cases)")
    wr = stats.win_rate_crosstab(sdf, factor)
    st.dataframe(shaded(wr, "rate", stats.count_crosstab(sdf, factor)), width="stretch", height=fit(wr))

with tab_browse:
    b1, b2 = st.columns([1, 2])
    browse_area = b1.selectbox("Chapter", ["All chapters", *[a for a in [*TAXONOMY, "Other"]
                                                         if any(c.get("area", "Other") == a for c in CASEBOOK)]])
    shown = sorted((c for c in CASEBOOK if browse_area in ("All chapters", c.get("area", "Other"))),
                   key=lambda c: (c.get("class_no") or 99,
                                  list(TAXONOMY).index(c["area"]) if c.get("area") in TAXONOMY else 99,
                                  filed_under(c), c.get("year") or 0))
    names = [(f"Class {c['class_no']} · " if c.get("class_no") else "") + f"{c['case_name']} ({c['year']}) — {filed_under(c)}" + (" · added" if c["source"] == "Added" else "")
             for c in shown]
    start = next((i for i, c in enumerate(shown) if c["slug"] == TARGET), 0)
    pick = b2.selectbox("Case", range(len(shown)), index=start, format_func=names.__getitem__)
    case = shown[pick]
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(case["brief"])
    with right:
        if case.get("principle"):
            st.markdown(f"> **Principle:** {case['principle']}")
        theme_card(case)
        similar_cases(case)
