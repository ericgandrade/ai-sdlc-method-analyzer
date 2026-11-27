"""Markdown report (plan §8.6): the same model, sections and order as the HTML report, with
Unicode Harvey glyphs beside each number and the ±U band as text. GitHub-renderable, no HTML."""
import re

from . import report_model
from .md import glyph_text

FEATURE_GLYPH = {0: "○", 1: "◑", 2: "●"}
GROUP_GLYPH = {0: "○", 1: "◔", 2: "◑", 3: "◕", 4: "●"}
TAG = re.compile(r"<[A-Za-z/!]")


def _safe(s):
    return str(s).replace("<", "&lt;").replace("\n", " ")


def cell(c):
    if isinstance(c, tuple):
        kind = c[0]
        if kind == "n":
            return _safe(c[1])
        if kind == "ball":
            _, pref, k, label = c
            g = glyph_text(k) if pref == "c" else FEATURE_GLYPH[k] if pref == "f" else GROUP_GLYPH[k]
            return f"{g} {_safe(label)}"
        if kind == "band":
            return f"{c[1]:.1f} ± {c[2]:.1f}"
        if kind == "chip":
            return _safe(c[1])
    return _safe(c)


def table(head, rows, foot):
    esc = lambda s: s.replace("|", "\\|")
    out = ["| " + " | ".join(esc(cell(h)) for h in head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows + ([foot] if foot else []):
        out.append("| " + " | ".join(esc(cell(c)) for c in r) + " |")
    return "\n".join(out)


def narrative(text):
    lines = []
    for ln in text.replace("<", "&lt;").split("\n"):
        lines.append("##" + ln if ln.startswith("#") else ln)
    return "\n".join(lines)


def blocks(bs, depth=3):
    out = []
    for b in bs:
        kind = b[0]
        if kind == "md":
            out.append(narrative(b[1]))
        elif kind == "kpis":
            out.append("\n".join(f"- **{_safe(l)}:** {_safe(v)}" for l, v, _ in b[1]))
        elif kind == "table":
            out.append(table(b[1], b[2], b[3]))
        elif kind == "callout":
            out.append(f"> **{_safe(b[1])}.** {_safe(b[2])}")
        elif kind == "details":
            _, _, summary, chips, inner = b
            extra = f" ({', '.join(cell(c) for c in chips)})" if chips else ""
            out.append(f"{'#' * depth} {_safe(summary)}{extra}")
            out.append(blocks(inner, min(6, depth + 1)))
        elif kind == "banner":
            out.append(f"> **{_safe(b[1])}**")
        # "grid" has no Markdown form: the table beside it carries the same numbers
    return "\n\n".join(x for x in out if x)


def render(inputs):
    secs = report_model.build(inputs)
    out = []
    for s in secs:
        if s["id"] == "header":
            out.append(f"# {_safe(s['title'])}")
            out.append(" · ".join(f"{_safe(k)} **{_safe(v)}**" for k, v in s["meta"]))
            if s["blocks"]:
                out.append(blocks(s["blocks"]))
        elif s["id"] == "footer":
            out.append("---")
            out.append("\n\n".join(_safe(x) for x in s["lines"]))
            if s["links"]:
                out.append("Sources: " + " · ".join(f"[{_safe(nm)}]({u})" for nm, u in s["links"]))
        else:
            out.append(f"## {_safe(s['title'])}")
            if s.get("key"):
                out.append(f"**Key message:** {_safe(s['key'])}")
            if s.get("sub"):
                out.append(f"*{_safe(s['sub'])}*")
            body = blocks(s["blocks"])
            if body:
                out.append(body)
    return "\n\n".join(out).rstrip() + "\n"


def check(doc):
    """Violations of the Markdown contract; empty means it passes."""
    errs = []
    if TAG.search(doc):
        errs.append("contains an HTML tag")
    if len(re.findall(r"^# ", doc, flags=re.M)) != 1:
        errs.append("not exactly one top-level heading")
    return errs
