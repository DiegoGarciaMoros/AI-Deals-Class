"""Exam practice: generate law-school exam questions from my briefs, check MC answer keys,
grade short answers, and answer freestyle questions. Used by make_questions.py (the
pre-built question bank) and app.py (the Practice tab).

Every prompt is grounded in the briefs passed as context: questions and feedback may only
cite cases from my casebook, and the model is told not to invent holdings.
"""
import json
import os
import re

import json_repair

from briefing import DOCTRINE_LABEL, call_openrouter

# Cheap, long-context default; override with PRACTICE_MODEL.
PRACTICE_MODEL = os.environ.get("PRACTICE_MODEL", "google/gemini-2.5-flash")
# A different model answers each MC question blind to check the key.
CHECK_MODEL = os.environ.get("CHECK_MODEL", "openai/gpt-4.1-mini")
LETTERS = "ABCD"
JSON_MODE = {"response_format": {"type": "json_object"}}

COURSE = ("first-year Property at NYU Law (Brooks, Fall 2026; Merrill, Smith & Brady, Property: "
          "Principles and Policies). The final is a four-hour open-book multiple-choice exam.")

GUARDRAILS = """GUARDRAILS
- Base every rule, holding and fact about a real case ONLY on the briefs below. Do not add
  holdings from memory. Cite only cases that appear in the briefs below.
- Hypothetical parties and facts are fine (and expected) in fact patterns; make clear they're hypothetical.
- Where the law is unsettled or the briefs don't decide a point, say so instead of guessing."""


def extract_json(reply):
    """The last ```json block (or the outermost {...}/[...]) in a model reply."""
    blocks = re.findall(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", reply, re.S)
    text = blocks[-1] if blocks else reply[min([i for i in (reply.find("{"), reply.find("[")) if i >= 0] or [0]):]
    try:
        return json.loads(text)
    except json.JSONDecodeError:  # models sometimes drop a brace or leave a trailing comma
        repaired = json_repair.loads(text)
        if not repaired:
            raise
        return repaired


def unit_cases(casebook, unit):
    """Cases filed in a unit: its own cases first, then cases that also speak to it."""
    own = [c for c in casebook if (c.get("doctrine_tags") or [None])[0] == unit]
    also = [c for c in casebook if unit in (c.get("doctrine_tags") or [])[1:]]
    return own + also


def brief_context(cases, max_chars=60_000):
    parts, used = [], 0
    for c in cases:
        text = f"### {c['case_name']} ({c.get('year')}) [unit: {DOCTRINE_LABEL.get((c.get('doctrine_tags') or [''])[0], 'Other')}]\n{c['brief']}"
        if used + len(text) > max_chars:
            break
        parts.append(text)
        used += len(text)
    return "\n\n".join(parts)


STOP = {"the", "and", "for", "what", "when", "how", "does", "case", "cases", "law", "with", "that",
        "property", "who", "which", "can", "will", "would", "about", "quiz", "explain", "between", "fit", "together"}


def _stems(text):
    """Crude stems so 'finder', 'finders' and 'finding' match: lowercase words cut to 5 letters."""
    return [w[:5] for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP]


def retrieve(casebook, query, k=6):
    """The k casebook cases that best match a free-text query: case names count most, then the
    case's class unit, then its principle and doctrines, then the brief text."""
    words = set(_stems(query))
    if not words:
        return casebook[:k]
    scored = []
    for c in casebook:
        name = set(_stems(c["case_name"]))
        unit = set(_stems(" ".join(DOCTRINE_LABEL.get(t, "") for t in c.get("doctrine_tags") or [])))
        meta = _stems(" ".join([c.get("principle") or "", " ".join(c.get("doctrines") or [])]))
        body = _stems(c.get("brief", ""))
        score = sum(12 * (w in name) + 8 * (w in unit) + 3 * meta.count(w) + min(body.count(w), 6) for w in words)
        scored.append((score, c))
    return [c for s, c in sorted(scored, key=lambda x: -x[0]) if s > 0][:k] or casebook[:k]


QUESTION_PROMPT = """You write exam questions for {course}

Write {n_mc} multiple-choice question(s) and {n_sa} short-answer question(s) on: {scope}.
{difficulty_line}

MULTIPLE CHOICE (like a law school final):
- A short hypothetical fact pattern (2-6 sentences), then a call of the question.
- Exactly four options A-D with ONE best answer. Wrong options should be tempting: a rejected
  rule, the dissent's view, a rule from a neighboring doctrine, or the right rule misapplied.
- Test applying rules to new facts, not trivia about case names or dates.
- For EVERY option say in one sentence why it is right or wrong.

SHORT ANSWER:
- A hypothetical fact pattern (4-8 sentences) and a specific call of the question.
- A model answer in IRAC form, 150-250 words, citing cases from the briefs.
- A rubric of 4-6 points worth 10 in total.

{guardrails}

Output only JSON:
{{"questions": [
  {{"type": "mc", "difficulty": "easy|medium|hard", "stem": "facts + call of the question",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "answer": "B",
    "why": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "explanation": "2-3 sentences: the rule and how it decides these facts",
    "cases": ["case names from the briefs"], "doctrines": ["short doctrine names"]}},
  {{"type": "sa", "difficulty": "...", "stem": "facts + call of the question",
    "model_answer": "...", "rubric": [{{"point": "what a full answer must do", "points": 2}}],
    "cases": ["..."], "doctrines": ["..."]}}
]}}

BRIEFS:
{context}
"""

CHECK_PROMPT = """Answer this Property exam question. Use the briefs as your source of law.
Reply with only the letter of the best answer (A, B, C or D).

{stem}

{options}

BRIEFS:
{context}
"""

GRADE_PROMPT = """You are grading a short-answer response on a {course}
Grade like a fair, demanding law professor. Be specific: quote the student's own words when
praising or criticizing. Reward correct rules applied to the facts; don't reward reciting
rules without application.

{guardrails}

QUESTION:
{stem}

RUBRIC (10 points):
{rubric}

MODEL ANSWER (for your reference; other well-supported answers can earn full credit):
{model_answer}

STUDENT ANSWER:
{answer}

Output only JSON:
{{"score": 0-10, "verdict": "one sentence overall",
  "rubric_scores": [{{"point": "...", "earned": 0, "max": 2, "comment": "..."}}],
  "strengths": ["..."], "gaps": ["what is missing or wrong, specifically"],
  "cases_to_cite": [{{"case": "name from the briefs", "why": "how it would strengthen this answer"}}],
  "doctrines_to_use": [{{"doctrine": "...", "why": "..."}}],
  "improved_answer": "a revised version of the student's answer, 150-250 words, keeping their structure where it works",
  "next_step": "one concrete thing to practice next"}}

BRIEFS:
{context}
"""

TUTOR_PROMPT = """You are a Property tutor for {course}
Answer the student's question clearly, in Markdown: the rule(s), how the cases in the briefs
apply or develop them (cite case names in *italics*), where courts or the casebook disagree,
and one exam tip. 200-450 words.

{guardrails}

QUESTION:
{query}

BRIEFS:
{context}
"""


def _fmt_options(q):
    return "\n".join(f"{k}. {v}" for k, v in q["options"].items())


def clean_question(q):
    """Validate one generated question; return it normalized, or None if malformed."""
    if q.get("type") == "mc":
        opts = q.get("options") or {}
        if sorted(opts) != list(LETTERS) or q.get("answer") not in LETTERS:
            return None
        q["why"] = {k: (q.get("why") or {}).get(k, "") for k in LETTERS}
    elif q.get("type") == "sa":
        rubric = [r for r in q.get("rubric") or [] if r.get("point")]
        if not rubric or not q.get("model_answer"):
            return None
        q["rubric"] = rubric
    else:
        return None
    q["cases"] = [c for c in q.get("cases") or [] if isinstance(c, str)]
    q["doctrines"] = [d for d in q.get("doctrines") or [] if isinstance(d, str)]
    return q if q.get("stem") else None


def ask_json(api_key, model, prompt, tries=3):
    """A call that must return JSON: JSON mode, retrying if the reply is empty or won't parse."""
    for attempt in range(tries):
        reply, _ = call_openrouter(api_key, model, prompt, title="Property exam practice", extra=JSON_MODE)
        try:
            if not reply:
                raise ValueError("empty reply")
            return extract_json(reply)
        except (json.JSONDecodeError, ValueError):
            if attempt == tries - 1:
                raise


DIFFICULTY = {
    "easy": "one rule applied to clear facts; the answer follows directly from a case's holding",
    "medium": "a rule applied to new facts with a twist, or two issues; distractors use rejected or neighboring rules",
    "hard": "several interacting doctrines, a close call, or a majority/minority split; subtle distractors that a well-prepared student might pick",
}


def generate(api_key, scope, context, n_mc=2, n_sa=1, model=PRACTICE_MODEL, difficulty=None):
    """Write questions; `difficulty` ("easy" / "medium" / "hard") pins the level of every question."""
    line = (f'Make every question "{difficulty}": {DIFFICULTY[difficulty]}. Set "difficulty" to "{difficulty}".'
            if difficulty in DIFFICULTY else
            "Mix difficulties (easy: " + DIFFICULTY["easy"] + "; medium: " + DIFFICULTY["medium"]
            + "; hard: " + DIFFICULTY["hard"] + ").")
    prompt = QUESTION_PROMPT.format(course=COURSE, n_mc=n_mc, n_sa=n_sa, scope=scope, difficulty_line=line,
                                    guardrails=GUARDRAILS, context=context)
    data = ask_json(api_key, model, prompt)
    items = data.get("questions", data) if isinstance(data, dict) else data
    made = [q for q in (clean_question(dict(x)) for x in items if isinstance(x, dict)) if q]
    for q in made:
        if difficulty in DIFFICULTY:
            q["difficulty"] = difficulty
        elif q.get("difficulty") not in DIFFICULTY:
            q["difficulty"] = "medium"
    return made


def check_mc(api_key, q, context, model=CHECK_MODEL):
    """Have a second model answer blind. Returns its letter."""
    reply, _ = call_openrouter(api_key, model, CHECK_PROMPT.format(
        stem=q["stem"], options=_fmt_options(q), context=context[:20_000]), title="Property exam practice")
    m = re.search(r"\b([ABCD])\b", reply.strip().upper())
    return m.group(1) if m else "?"


def grade(api_key, q, answer, context, model=PRACTICE_MODEL):
    rubric = "\n".join(f"- ({r.get('points', '?')} pts) {r['point']}" for r in q["rubric"])
    result = ask_json(api_key, model, GRADE_PROMPT.format(
        course=COURSE, guardrails=GUARDRAILS, stem=q["stem"], rubric=rubric,
        model_answer=q.get("model_answer", ""), answer=answer[:8000], context=context))
    try:
        result["score"] = max(0.0, min(10.0, float(result.get("score", 0))))
    except (TypeError, ValueError):
        result["score"] = 0.0
    return result


def tutor(api_key, query, context, model=PRACTICE_MODEL):
    reply, _ = call_openrouter(api_key, model, TUTOR_PROMPT.format(
        course=COURSE, guardrails=GUARDRAILS, query=query[:4000], context=context),
        title="Property exam practice")
    return reply.strip()
