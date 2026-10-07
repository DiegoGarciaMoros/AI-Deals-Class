"""The briefing prompt, the themes each case is coded on, and the OpenRouter call.

Shared by brief_cases.py (batch over my casebook) and app.py (one case at a time).
"""
import csv
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Any id from https://openrouter.ai/models. A long-context model is needed:
# some opinions (Moore, Intel) run past 100,000 characters.
DEFAULT_MODEL = "google/gemini-2.5-flash"
MAX_CHARS = 250_000

HERE = Path(__file__).parent
CASES = list(csv.DictReader(open(HERE / "cases.csv")))
COURSE_CASES = [r["case_name"] for r in CASES]

# Each theme: (one-line question, allowed values). Lists marked "many" allow several.
THEMES = {
    "competing_values": ("many", "What interest was weighed against the property holder's claim?", [
        "necessity", "custom", "public_rights", "equity_hardship", "reliance_or_repose",
        "labor_or_investment", "personhood_dignity", "productive_use", "freedom_of_contract",
        "third_party_protection", "state_sovereignty", "none"]),
    "justifications": ("many", "Which theories of property does the court's reasoning rest on?", [
        "first_possession", "labor", "utilitarian_efficiency", "personhood", "custom_community",
        "public_trust_democratic", "fairness_equity", "settled_expectations",
        "administrability_clear_rules", "owner_autonomy", "precedent_formalism"]),
    "sticks": ("many", "Which sticks in the bundle are at stake?", [
        "exclude", "use", "possess", "transfer", "destroy", "abandon", "inherit_or_devise",
        "commodify", "income"]),
    "resource": ("one", "What kind of thing is the property?", [
        "land", "water", "wild_animal", "chattel", "human_body", "intangible_or_ip",
        "digital_systems", "artifact_or_cultural", "other"]),
    "rule_or_standard": ("one", "Did the court adopt a bright-line rule or a flexible standard?", [
        "bright_line_rule", "flexible_standard", "mixed"]),
    "entitlement_protection": ("one", "How is the winner's entitlement protected (Calabresi & Melamed)?", [
        "property_rule", "liability_rule", "inalienability", "none", "unclear"]),
    "lawmaker": ("one", "Who changes the law here?", [
        "court_made_new_law", "applied_existing_law", "deferred_to_legislature", "applied_statute"]),
    "time_shifts_rights": ("bool", "Did the passage of time or long possession create or end a right?", None),
}


def _theme_lines():
    lines = []
    for name, (kind, question, options) in THEMES.items():
        if kind == "bool":
            lines.append(f'  "{name}": true/false,   // {question}')
        elif kind == "many":
            lines.append(f'  "{name}": [1-3 of {json.dumps(options)}],   // {question}')
        else:
            lines.append(f'  "{name}": one of {json.dumps(options)},   // {question}')
    return "\n".join(lines)


BRIEF_FORMAT = f"""You are my briefing assistant for first-year Property at NYU Law. Brief the
opinion below in MY format, shown here. Use short bullets, plain sentences, and bold
doctrine names. Accuracy matters more than polish.

FORMAT (Markdown):

## [Case Name] ([Court], [Year])

**Facts**
- [Only the facts the court relied on, in chronological order. Who did what to whom.]

**Procedural History**
- [Trial court result, any intermediate appeal, who appealed]

**Issue**
- [One plain-English question, e.g. "Can a landlord retake a leased property by changing the locks while the tenant is away, without going to court?"]

**Holding**
- [Winner (role) wins.] [One or two sentences answering the Issue.] [Affirmed / Reversed / Remanded.]

**Rules**
- **[Short bold label].** [One general sentence I could paste into an outline.]
- [One bullet per rule the court states or applies, including rules it rejects, marked "Rejected:".]

**Reasoning**
- [The court's main reasons, as short bullets. Sub-bullets for supporting points.]

**Dissent ([Judge])** / **Concurrence ([Judge])**
- [Core disagreement and the alternative rule.] If none, write "None."

**NOTES:**
1. [Why this case matters for the course, and how it connects to other cases I've studied. Only name cases from this list or cases cited in the opinion: {", ".join(COURSE_CASES)}]
2. [Any tension, open question, or hypo worth raising in class]

**Takeaway:** [One sentence.]

GUARDRAILS
- Every fact, holding, and rule must come from the opinion text. Do not add facts from memory.
- Never invent a case, citation, or quote. Quote only exact words from the opinion.
- Keep majority and dissent reasoning separate. Mark anything the court didn't need to decide as *(dicta)*.
- If something is unclear, write [CHECK: reason] instead of guessing.
- Aim for 350-650 words.
"""

CONNECTIONS = """
After NOTES, add a section:

**Connections to my casebook**
- [3-5 bullets. Each names one case from the casebook index below and says, in one sentence,
  how this case agrees with it, departs from it, or answers the same question differently.
  Name ONLY cases from the index.]

CASEBOOK INDEX (case | year | owner won? | takeaway):
{index}
"""

FIELDS = f"""
AFTER the brief, output a fenced ```json block with these fields:
{{
  "case_name": "...",
  "year": 1900,
  "court": "full court name",
  "court_level": one of ["trial", "intermediate_appellate", "state_supreme", "federal_appellate", "us_supreme_court", "other"],
  "plaintiff": "...",
  "defendant": "...",
  "winner": one of ["plaintiff", "defendant", "mixed"],
  "disposition": one of ["affirmed", "reversed", "reversed_and_remanded", "affirmed_in_part", "original_decision"],
  "property_holder": "who holds the ownership / title / possessory interest at stake, and in what (e.g. 'Moore, in his excised cells')",
  "challenger": "who or what is asserting a claim against that interest",
  "owner_prevailed": one of ["yes", "no", "mixed", "not_applicable"],
  "owner_prevailed_why": "one sentence: did the court protect the property_holder's interest?",
{_theme_lines()}
  "principle": "one sentence stating the case's lesson about property, in general terms",
  "remedy": one of ["injunction", "damages", "restitution", "title_or_declaration", "criminal_conviction", "none", "other"],
  "has_dissent": true/false,
  "has_concurrence": true/false,
  "doctrines": ["2-4 short doctrine names"],
  "check_flags": number of [CHECK] flags in your brief
}}

Use ONLY the listed values for each field, and keep each value in its own field.

Decide "owner_prevailed" by comparing the winner to "property_holder", NOT to the plaintiff
or defendant: an owner can be the plaintiff (a car owner suing a garage over a theft) or the defendant. It asks
the theme of the course: did the court protect the person holding the property interest
(owner sovereignty), or did another interest (necessity, custom, public rights, equity, a
non-owner) win? Use "mixed" when both sides hold competing property interests and each
partly wins, and "not_applicable" only when no one's property interest is at stake.
"""


def build_prompt(index=None):
    """The full instruction. Pass a casebook index to add a Connections section."""
    connections = CONNECTIONS.format(index=index) if index else ""
    return BRIEF_FORMAT + connections + FIELDS + "\nOPINION:\n"


def call_openrouter(api_key, model, prompt, retries=5, title="Property case briefs"):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": title,
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read())
            if "choices" not in data:
                raise RuntimeError(f"unexpected response: {str(data)[:300]}")
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                wait = 2 ** (attempt + 2)
                print(f"  HTTP {e.code}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from e


def split_reply(reply):
    """Return (brief_markdown, fields_dict) from the model's reply."""
    blocks = list(re.finditer(r"```json\s*(\{.*?\})\s*```", reply, re.S))
    if not blocks:
        raise ValueError("no ```json block in reply")
    last = blocks[-1]
    try:
        fields = json.loads(last.group(1))
    except json.JSONDecodeError:  # the model echoed the // comments from the schema
        fields = json.loads(re.sub(r"//[^\n]*", "", last.group(1)))
    return reply[: last.start()].strip(), fields


def normalize(fields):
    """Keep only the allowed values for each theme (models sometimes cross fields)."""
    for name, (kind, _, options) in THEMES.items():
        value = fields.get(name)
        if kind == "bool":
            fields[name] = bool(value)
        elif kind == "many":
            kept = [v for v in (value if isinstance(value, list) else [value]) if v in options]
            fields[name] = kept or ["none" if "none" in options else "other"]
        elif value not in options:
            fields[name] = "unclear" if "unclear" in options else "mixed" if "mixed" in options else options[-1]
    return fields


def brief_opinion(api_key, model, text, index=None, retries=2):
    """Brief one opinion; retry if the model forgets the JSON block."""
    prompt = build_prompt(index) + text[:MAX_CHARS]
    for attempt in range(retries):
        reply, usage = call_openrouter(api_key, model, prompt)
        try:
            brief, fields = split_reply(reply)
            return brief, normalize(fields), usage
        except ValueError:
            if attempt == retries - 1:
                raise
