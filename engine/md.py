"""Minimal Markdown-to-HTML converter for the report's narrative sections (plan §8.1).

Supports paragraphs, headings (demoted so the report keeps a single <h1>), bullet and numbered
lists, pipe tables (numeric cells get `class="n"`), and inline bold, italic and code. All text is
HTML-escaped first. Harvey glyphs (○ ◔ ◑ ◑⁺ ◕ ●) become SVG balls with an aria-label.
"""
import html
import re

from .svg import ball

GLYPHS = [("◑⁺", 3), ("○", 0), ("◔", 1), ("◑", 2), ("◕", 4), ("●", 5)]   # two-codepoint glyph first
GLYPH_RE = re.compile("|".join(re.escape(g) for g, _ in GLYPHS))
GLYPH_K = dict(GLYPHS)
NUMERIC = re.compile(r"^(?:[-+−]?\d[\d,]*(?:\.\d+)?(?:\s*%|\s*±\s*\d+(?:\.\d+)?)?|n/m|n/a|—|approx\. [\d,.]+)$")
TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")


def glyph_text(k):
    """The Unicode Harvey glyph for a 0–5 criterion score (Markdown fallback)."""
    return {v: g for g, v in GLYPHS}[k]


def inline(text):
    """Escape, then apply code, bold, italic and Harvey glyphs."""
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for p in parts:
        if len(p) >= 2 and p.startswith("`") and p.endswith("`"):
            out.append(f"<code>{html.escape(p[1:-1], quote=False)}</code>")
            continue
        s = html.escape(p, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", s)
        s = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", s)
        s = GLYPH_RE.sub(lambda m: ball("c", GLYPH_K[m.group(0)], f"{GLYPH_K[m.group(0)]} of 5"), s)
        out.append(s)
    return "".join(out)


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_numeric(cell):
    return bool(NUMERIC.match(cell.strip()))


def table_html(head, rows):
    th = "".join(f'<th scope="col">{inline(h)}</th>' for h in head)
    body = []
    for r in rows:
        tds = "".join(f'<td class="n">{inline(c)}</td>' if is_numeric(c) else f"<td>{inline(c)}</td>" for c in r)
        body.append(f"<tr>{tds}</tr>")
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def to_html(text):
    lines = text.replace("\r\n", "\n").split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(x.strip() for x in para))}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush()
            lvl = min(6, len(m.group(1)) + 2)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1].strip()):
            flush()
            head = _cells(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append(table_html(head, rows))
            continue
        lm = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if lm:
            flush()
            tag = "ol" if lm.group(1)[0].isdigit() else "ul"
            items = []
            while i < len(lines):
                lm = re.match(r"^([-*]|\d+\.)\s+(.*)$", lines[i].strip())
                if not lm:
                    if lines[i].startswith("  ") and lines[i].strip() and items:
                        items[-1] += " " + lines[i].strip()
                        i += 1
                        continue
                    break
                items.append(lm.group(2))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)
