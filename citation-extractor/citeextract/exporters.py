"""Export analyzed citations to downloadable files."""

from __future__ import annotations

import csv
import html
import io
import json
import zipfile
from datetime import date
from typing import Any, Callable

from .extractor import KIND_LABELS

OCCURRENCE_LABELS = {"full": "Full", "short": "Short", "id": "Id.", "supra": "Supra", "reference": "Reference"}


def _link(authority: dict[str, Any]) -> str:
    links = authority.get("links") or {}
    return links.get("courtlistener") or links.get("source") or links.get("courtlistener_citation") or ""


def _context_text(occurrence: dict[str, Any]) -> str:
    ctx = occurrence["context"]
    return f"{ctx['before']}[[{ctx['match']}]]{ctx['after']}"


def authorities_csv(result: dict[str, Any]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "id", "type", "case_name", "citation", "parallel_citations", "full_citation", "court", "year",
        "reporter", "times_cited", "full_cites", "short_cites", "id_cites", "supra_cites", "pin_cites",
        "signals", "parentheticals", "courtlistener_status", "courtlistener_case_name", "link",
    ])
    for a in result["authorities"]:
        cl = a.get("courtlistener") or {}
        counts = a.get("counts", {})
        writer.writerow([
            a["id"], a["kind"], a.get("case_name") or "", a["citation"], "; ".join(a["parallel_citations"]),
            a["full_citation"], a.get("court_name") or a.get("court") or "", a.get("year") or "",
            a.get("reporter_name") or a.get("reporter") or "", a["occurrence_count"], counts.get("full", 0),
            counts.get("short", 0), counts.get("id", 0), counts.get("supra", 0), "; ".join(a["pin_cites"]),
            "; ".join(a["signals"]), " | ".join(a["parentheticals"]), cl.get("status", ""),
            cl.get("case_name") or "", _link(a),
        ])
    return out.getvalue()


def occurrences_csv(result: dict[str, Any]) -> str:
    rows = []
    for a in result["authorities"]:
        for o in a["occurrences"]:
            rows.append((o["start"], a["id"], a.get("case_name") or a["citation"], a["citation"], o))
    for o in result["unresolved"]:
        rows.append((o["start"], "", f"(unresolved) {o.get('antecedent_guess') or ''}".strip(), "", o))
    rows.sort(key=lambda r: r[0])

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["position", "authority_id", "authority", "citation", "form", "as_written", "pin_cite",
                     "signal", "parenthetical", "context"])
    for start, aid, name, cite, o in rows:
        writer.writerow([start, aid, name, cite, OCCURRENCE_LABELS.get(o["type"], o["type"]),
                         o.get("full_text") or o["text"], o.get("pin_cite") or "", o.get("signal") or "",
                         o.get("parenthetical") or "", _context_text(o)])
    return out.getvalue()


def to_json(result: dict[str, Any], include_text: bool = False) -> str:
    data = {k: v for k, v in result.items() if include_text or k != "text"}
    data["generated"] = date.today().isoformat()
    return json.dumps(data, indent=2, ensure_ascii=False)


def _grouped(result: dict[str, Any]):
    for kind, label in KIND_LABELS.items():
        items = [a for a in result["authorities"] if a["kind"] == kind]
        if items:
            yield label, items


def table_of_authorities_md(result: dict[str, Any], title: str = "Table of Authorities") -> str:
    s = result["stats"]
    lines = [f"# {title}", "",
             f"_{s['unique_authorities']} authorities · {s['total_citations']} citations · "
             f"generated {date.today().isoformat()}_", ""]
    for label, items in _grouped(result):
        lines += [f"## {label}", ""]
        for a in items:
            name = a["full_citation"]
            if a.get("case_name"):
                name = name.replace(a["case_name"], f"*{a['case_name']}*", 1)
            link = _link(a)
            entry = f"- [{name}]({link})" if link else f"- {name}"
            detail = [f"cited {a['occurrence_count']}×"]
            if a["pin_cites"]:
                detail.append("at " + ", ".join(a["pin_cites"]))
            lines.append(f"{entry} — {'; '.join(detail)}")
            for p in a["parentheticals"]:
                lines.append(f"  - ({p})")
        lines.append("")
    if result["unresolved"]:
        lines += ["## Unresolved short-form citations", ""]
        for o in result["unresolved"]:
            lines.append(f"- {o.get('full_text') or o['text']}")
        lines.append("")
    return "\n".join(lines)


def table_of_authorities_html(result: dict[str, Any], title: str = "Table of Authorities") -> str:
    e = html.escape
    s = result["stats"]
    parts = [f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
 body{{font-family:Georgia,'Times New Roman',serif;max-width:760px;margin:48px auto;padding:0 20px;color:#1b1b1b;line-height:1.5;background:#fff}}
 h1{{text-align:center;font-size:1.5rem;letter-spacing:.08em;text-transform:uppercase}}
 h2{{font-size:1.05rem;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #999;padding-bottom:4px;margin-top:2em}}
 .meta{{text-align:center;color:#555;font-size:.9rem}}
 ul{{list-style:none;padding:0}} li{{margin:.55em 0;display:flex;gap:12px}}
 li .cite{{flex:1}} li .refs{{white-space:nowrap;color:#555;font-size:.9rem}}
 .paren{{display:block;color:#555;font-size:.88rem;margin-left:1.5em}}
 a{{color:#1a4d8f;text-decoration:none}} a:hover{{text-decoration:underline}}
 @media print{{a{{color:inherit}} body{{margin:0}}}}
</style></head><body>
<h1>{e(title)}</h1>
<p class="meta">{s['unique_authorities']} authorities · {s['total_citations']} citations · {date.today().isoformat()}</p>
"""]
    for label, items in _grouped(result):
        parts.append(f"<h2>{e(label)}</h2><ul>")
        for a in items:
            cite = e(a["full_citation"])
            if a.get("case_name"):
                cite = cite.replace(e(a["case_name"]), f"<i>{e(a['case_name'])}</i>", 1)
            link = _link(a)
            if link:
                cite = f'<a href="{e(link)}">{cite}</a>'
            parens = "".join(f'<span class="paren">({e(p)})</span>' for p in a["parentheticals"])
            refs = f"{a['occurrence_count']}×" + (f" · at {e(', '.join(a['pin_cites']))}" if a["pin_cites"] else "")
            parts.append(f'<li><span class="cite">{cite}{parens}</span><span class="refs">{refs}</span></li>')
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


def annotated_html(result: dict[str, Any], title: str = "Annotated Opinion") -> str:
    """The cleaned opinion text with each citation highlighted and linked."""
    e = html.escape
    text = result["text"]
    marks = []
    by_id = {a["id"]: a for a in result["authorities"]}
    for a in result["authorities"]:
        for o in a["occurrences"]:
            marks.append((o["start"], o["end"], a["id"]))
    for o in result["unresolved"]:
        marks.append((o["start"], o["end"], None))
    marks.sort()
    body, pos = [], 0
    for start, end, aid in marks:
        if start < pos:
            continue
        body.append(e(text[pos:start]))
        frag = e(text[start:end])
        if aid:
            a = by_id[aid]
            link = _link(a)
            tip = e(a["full_citation"])
            frag = (f'<a class="c c-{a["kind"]}" href="{e(link)}" title="{tip}">{frag}</a>' if link
                    else f'<mark class="c c-{a["kind"]}" title="{tip}">{frag}</mark>')
        else:
            frag = f'<mark class="c c-unresolved" title="Unresolved">{frag}</mark>'
        body.append(frag)
        pos = end
    body.append(e(text[pos:]))
    paragraphs = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in "".join(body).split("\n\n"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
 body{{font-family:Georgia,serif;max-width:760px;margin:40px auto;padding:0 20px;line-height:1.65;color:#1b1b1b;background:#fff}}
 .c{{padding:1px 2px;border-radius:3px;text-decoration:none;color:inherit}}
 .c-case{{background:#dbe8ff}} .c-statute{{background:#dff3e4}} .c-journal{{background:#f6e7c8}} .c-unresolved{{background:#f3d6d6}}
</style></head><body><h1>{e(title)}</h1>{paragraphs}</body></html>"""


EXPORTS: dict[str, tuple[str, str, Callable[[dict[str, Any]], str]]] = {
    "authorities_csv": ("citations-authorities.csv", "text/csv", authorities_csv),
    "occurrences_csv": ("citations-occurrences.csv", "text/csv", occurrences_csv),
    "json": ("citations.json", "application/json", to_json),
    "toa_md": ("table-of-authorities.md", "text/markdown", table_of_authorities_md),
    "toa_html": ("table-of-authorities.html", "text/html", table_of_authorities_html),
    "annotated_html": ("annotated-opinion.html", "text/html", annotated_html),
}


def export(result: dict[str, Any], fmt: str) -> tuple[str, str, bytes]:
    """Return (filename, mimetype, content) for one export format, or "zip" for all."""
    if fmt == "zip":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, _, fn in EXPORTS.values():
                zf.writestr(filename, fn(result))
        return "citations-export.zip", "application/zip", buffer.getvalue()
    if fmt not in EXPORTS:
        raise KeyError(fmt)
    filename, mimetype, fn = EXPORTS[fmt]
    return filename, mimetype, fn(result).encode("utf-8")
