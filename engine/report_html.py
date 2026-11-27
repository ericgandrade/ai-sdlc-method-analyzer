"""`engine report` (plan §8): render the self-contained HTML report (and the Markdown twin) from a
run's JSON, or from the shipped baseline with `--baseline-only`.

The layout CSS below is built in and references theme tokens only; the theme (validated by
`engine/theme.py`) is inlined before it. No script, no external resource.
"""
import datetime
import html
import pathlib
import re
import sys

from . import md, paths, report_model, theme
from .common import EXIT_GATE, EXIT_MISSING, EXIT_OK, EXIT_USAGE
from .jsonio import read_json
from .svg import ball, band, svg_defs

MAX_BYTES = 5 * 1024 * 1024
LAYOUT = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font);font-size:15px;line-height:1.6;padding-block:2.5rem 4rem;padding-inline:16px}
.wrap{max-width:1140px;margin-inline:auto}
header{border-block-end:1px solid var(--rule);padding-block-end:1.2rem}
h1{font-size:2.2rem;line-height:1.2;margin-block:0 .6rem}
h2{font-size:1.45rem;margin-block:0 .4rem;padding-block-start:.6rem;border-block-start:3px solid var(--accent)}
h3,h4,h5,h6{margin-block:1.2rem .4rem}
section{margin-block:3rem}
p,li{max-width:80ch}
a{color:var(--accent)}
code{font-family:var(--mono);font-size:.9em;background:var(--wash);padding-inline:.25em}
.hmeta{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;color:var(--ink-soft);font-size:.9rem;margin:0;padding:0;list-style:none}
.hmeta b{color:var(--ink);font-weight:600}
.banner{border-inline-start:4px solid var(--neg);background:var(--wash);padding-block:.6rem;padding-inline:1rem;margin-block:1rem;font-weight:600}
.key{font-size:1.05rem}
.sub,.lead p{color:var(--ink-soft)}
.kpis{display:flex;flex-wrap:wrap;gap:1rem 2.4rem;border-block:1px solid var(--rule);padding-block:1rem;margin-block:1.2rem}
.kl{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-soft)}
.kv{font-size:1.5rem;font-weight:600}
.kpi.org .kv{color:var(--accent)}
.call{border-inline-start:3px solid var(--accent);background:var(--wash);padding-block:.8rem;padding-inline:1rem;margin-block:1.2rem}
.tw{overflow-x:auto;margin-block:1rem}
table{border-collapse:collapse;width:100%;font-size:.9rem}
thead th{background:var(--ink);color:var(--paper);text-align:start;font-weight:600;padding-block:.45rem;padding-inline:.6rem;white-space:nowrap}
td{border-block-end:1px solid var(--rule-soft);padding-block:.35rem;padding-inline:.6rem;vertical-align:top;text-align:start}
td.n{text-align:end;white-space:nowrap;font-variant-numeric:tabular-nums}
tfoot td{background:var(--wash);font-weight:600;border-block-start:1px solid var(--rule)}
.chip{display:inline-block;border:1px solid var(--rule);border-radius:999px;padding-inline:.55rem;font-size:.78rem;color:var(--ink-soft);white-space:nowrap}
.chip.org{border-color:var(--accent);color:var(--accent)}
.hb{width:14px;height:14px;vertical-align:-2px;color:var(--accent-2);margin-inline-end:.25rem}
.defs{position:absolute;width:0;height:0;overflow:hidden}
.band{width:240px;max-width:40vw;height:12px}
.band .axis{stroke:var(--rule);stroke-width:1}
.band .u{fill:var(--accent);opacity:.35}
.band .t{stroke:var(--ink);stroke-width:2}
.grid{max-width:520px;width:100%;height:auto;color:var(--ink);margin-block:1rem}
.grid .cell{fill:none;stroke:var(--rule-soft)}
.grid .ax{fill:var(--ink-soft);font-size:10px}
.grid .lb{fill:var(--ink);font-size:9px}
.grid .dot{fill:var(--accent)}
details{border-block-end:1px solid var(--rule);padding-block:.5rem}
summary{cursor:pointer;font-weight:600;list-style:none;display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";color:var(--accent);font-weight:700;width:1rem}
details[open]>summary::before{content:"–"}
summary .chips{margin-inline-start:auto;display:flex;gap:.35rem}
.hint{color:var(--ink-faint);font-size:.85rem}
footer{border-block-start:1px solid var(--rule);color:var(--ink-soft);font-size:.8rem;padding-block-start:1rem;margin-block-start:3rem}
footer p{margin-block:.3rem}
@media (max-width:640px){h1{font-size:1.7rem}.kv{font-size:1.25rem}.band{max-width:30vw}}
@media print{body{padding:1rem} section,tr{break-inside:avoid} h2{break-after:avoid} details{display:block} details>summary{list-style:none} .band .axis{stroke:#000} details:not([open])>*:not(summary){display:block}}
"""


# ------------------------------------------------------------------ rendering

def _text(s):
    return md.inline(str(s))


def cell(c):
    if isinstance(c, tuple):
        kind = c[0]
        if kind == "n":
            return f'<td class="n">{_text(c[1])}</td>'
        if kind == "ball":
            _, pref, k, label = c
            unit = {"c": "of 5", "f": "of 2", "g": "group band"}[pref]
            aria = f"{label} {unit}" if pref != "g" else label
            return f'<td class="n">{ball(pref, k, html.escape(aria))}{html.escape(label)}</td>'
        if kind == "band":
            return f'<td>{band(c[1], c[2])}</td>'
        if kind == "chip":
            return f'<td>{chip(c)}</td>'
    return f"<td>{_text(c)}</td>"


def chip(c):
    mod = f" {c[2]}" if len(c) > 2 and c[2] else ""
    return f'<span class="chip{mod}">{html.escape(c[1])}</span>'


def table(head, rows, foot):
    th = "".join(f'<th scope="col">{_text(h)}</th>' for h in head)
    body = "".join("<tr>" + "".join(cell(c) for c in r) + "</tr>" for r in rows)
    tf = ("<tfoot><tr>" + "".join(cell(c) for c in foot) + "</tr></tfoot>") if foot else ""
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody>{tf}</table></div>'


def grid(points):
    """6×6 grid: L3 (A0–A5) on x, C8 (0–5) on y; method labels stacked per cell."""
    cw, ch, ox, oy = 72, 42, 34, 8
    out = [f'<svg class="grid" viewBox="0 0 {ox + 6 * cw + 4} {oy + 6 * ch + 30}" role="img" '
           f'aria-label="Autonomy level L3 against safety C8 for {len(points)} methods">']
    for i in range(6):
        for j in range(6):
            out.append(f'<rect class="cell" x="{ox + i * cw}" y="{oy + j * ch}" width="{cw}" height="{ch}"/>')
        out.append(f'<text class="ax" x="{ox + i * cw + cw / 2:g}" y="{oy + 6 * ch + 14}" text-anchor="middle">A{i}</text>')
        out.append(f'<text class="ax" x="{ox - 8}" y="{oy + (5 - i) * ch + ch / 2 + 3:g}" text-anchor="end">{i}</text>')
    out.append(f'<text class="ax" x="{ox + 3 * cw}" y="{oy + 6 * ch + 27}" text-anchor="middle">L3 autonomy →   ·   C8 safety ↑</text>')
    stack = {}
    for name, x, y in points:
        k = stack.get((x, y), 0)
        stack[(x, y)] = k + 1
        px, py = ox + x * cw + 6, oy + (5 - y) * ch + 11 + k * 10
        out.append(f'<circle class="dot" cx="{px}" cy="{py - 3}" r="2.5"/>'
                   f'<text class="lb" x="{px + 5}" y="{py}">{html.escape(name[:16])}</text>')
    out.append("</svg>")
    return "".join(out)


def blocks(bs):
    out = []
    for b in bs:
        kind = b[0]
        if kind == "md":
            out.append(md.to_html(b[1]))
        elif kind == "kpis":
            out.append('<div class="kpis">' + "".join(
                f'<div class="kpi{(" " + mod) if mod else ""}"><div class="kl">{html.escape(l)}</div>'
                f'<div class="kv">{html.escape(v)}</div></div>' for l, v, mod in b[1]) + "</div>")
        elif kind == "table":
            out.append(table(b[1], b[2], b[3]))
        elif kind == "callout":
            out.append(f'<div class="call"><strong>{html.escape(b[1])}.</strong> {_text(b[2])}</div>')
        elif kind == "details":
            _, cls, summary, chips, inner = b
            cs = f'<span class="chips">{"".join(chip(c) for c in chips)}</span>' if chips else ""
            out.append(f'<details class="{cls}"><summary>{html.escape(summary)}{cs}</summary>{blocks(inner)}</details>')
        elif kind == "grid":
            out.append(grid(b[1]))
        elif kind == "banner":
            out.append(f'<div class="banner">{html.escape(b[1])}</div>')
    return "\n".join(out)


def render(inputs, theme_css):
    secs = report_model.build(inputs)
    title = secs[0]["title"]
    out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           f'<title>{html.escape(title)}</title>', '<style>', theme_css.strip(), LAYOUT.strip(), '</style>',
           '</head>', '<body>', '<div class="wrap">', svg_defs()]
    for s in secs:
        if s["id"] == "header":
            meta = "".join(f"<li>{html.escape(k)} <b>{html.escape(v)}</b></li>" for k, v in s["meta"])
            out.append(f'<header id="s-header"><h1>{html.escape(title)}</h1><ul class="hmeta">{meta}</ul>'
                       f'{blocks(s["blocks"])}</header>')
        elif s["id"] == "footer":
            links = " · ".join(f'<a href="{html.escape(u)}">{html.escape(nm)}</a>' for nm, u in s["links"])
            lines = "".join(f"<p>{html.escape(x)}</p>" for x in s["lines"])
            out.append(f'<footer id="s-footer">{lines}' + (f"<p>Sources: {links}</p>" if links else "") + "</footer>")
        else:
            cls = ' class="lead"' if s["id"] == "lead" else ""
            parts = [f'<section id="{s["id"]}"{cls}>', f'<h2>{html.escape(s["title"])}</h2>']
            if s.get("key"):
                parts.append(f'<p class="key"><strong>Key message:</strong> {_text(s["key"])}</p>')
            if s.get("sub"):
                parts.append(f'<p class="sub">{_text(s["sub"])}</p>')
            parts.append(blocks(s["blocks"]))
            parts.append("</section>")
            out.append("\n".join(parts))
    out += ["</div>", "</body>", "</html>", ""]
    return "\n".join(out)


# ------------------------------------------------------------------ selfcheck (§8.5)

def selfcheck(doc, private):
    """Return a list of violations; empty means the report passes."""
    errs = []
    lower = doc.lower()
    if "<script" in lower:
        errs.append("script tag")
    if re.search(r"\son[a-z]+\s*=", lower):
        errs.append("on* event attribute")
    if "javascript:" in lower:
        errs.append("javascript: URL")
    if "data:text/html" in lower:
        errs.append("data:text/html URL")
    body = re.sub(r"<footer\b.*?</footer>", "", doc, flags=re.S | re.I)
    if re.search(r"""\b(?:src|href)\s*=\s*["']?\s*https?://""", body, re.I):
        errs.append("external src/href outside the footer")
    if len(doc.encode("utf-8")) > MAX_BYTES:
        errs.append("larger than 5 MB")
    for need, label in (('<html lang="en">', "html lang"), ('<meta charset="utf-8">', "meta charset"),
                        ('<meta name="viewport"', "meta viewport")):
        if need not in doc:
            errs.append(f"missing {label}")
    if len(re.findall(r"<h1\b", doc)) != 1:
        errs.append("not exactly one <h1>")
    for tag in re.findall(r'<svg class="(?:hb|band)"[^>]*>', doc):
        if "aria-label=" not in tag:
            errs.append("svg.hb or svg.band without aria-label")
            break
    for t in re.findall(r"<table\b.*?</table>", doc, flags=re.S):
        m = re.search(r"<thead>(.*?)</thead>", t, flags=re.S)
        if not m or not re.search(r"<th\b", m.group(1)) or re.search(r'<th(?![^>]*scope="col")', m.group(1)):
            errs.append("table without <thead> and <th scope=\"col\">")
            break
    ids = re.findall(r"<section\b[^>]*\bid=\"([^\"]+)\"", doc)
    if not ids or ids[-1] != "limitations":
        errs.append("limitations is not the last section")
    if (report_model.PRIVATE_BANNER in doc) != bool(private):
        errs.append("private banner present without a private target" if not private else "private target without the private banner")
    return errs


# ------------------------------------------------------------------ inputs

def _short_hashes(root):
    from .freeze import records
    rec = {name: sha for name, sha, _, _ in records(root)}
    return (f"v1.0 {rec.get('methodology-v1.0.md', '')[:8]}", f"v2.0 {rec.get('rubric-v2.0.pt.md', '')[:8]}")


def _version(root):
    m = re.search(r'^version\s*=\s*"([^"]+)"', (pathlib.Path(root) / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def _registry(root):
    from .registry import entries, load_registry
    return {e["slug"]: e for e in entries(load_registry(root))}


def load_inputs(src, root, date, title=None, sections_dir=None):
    """Read every JSON input of a report from directory `src`."""
    src = pathlib.Path(src)
    need = ["results", "ranking", "sensitivity"]
    missing = [x for x in need if not (src / f"{x}.json").exists()]
    if missing:
        raise FileNotFoundError(", ".join(f"{x}.json" for x in missing))
    opt = lambda name: read_json(src / name) if (src / name).exists() else None
    sec_dir = pathlib.Path(sections_dir) if sections_dir else src / "report" / "sections"
    sections = {p.stem: p.read_text(encoding="utf-8").replace("\r\n", "\n")
                for p in sorted(sec_dir.glob("*.md"))} if sec_dir.is_dir() else {}
    results = read_json(src / "results.json")
    rounds = sorted({e.get("round_id") for e in results.values() if e.get("round_id")})
    mh, rh = _short_hashes(root)
    st = opt("state.json") or {}
    return {"results": results, "ranking": read_json(src / "ranking.json"), "sensitivity": read_json(src / "sensitivity.json"),
            "superiority": opt("superiority.json"), "fitgap_pre": opt("fitgap-pre.json"), "fitgap": opt("fitgap.json"),
            "projection": opt("fitgap-projection.json"), "registry": _registry(root), "sections": sections,
            "meta": {"date": date, "title": title, "methodology_hash": mh, "rubric_hash": rh,
                     "round_id": ", ".join(rounds), "version": _version(root), "isolation": st.get("isolation")}}


# ------------------------------------------------------------------ CLI

def configure(p):
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", help="run id: reads runs/<id>/, writes reports/<id>/")
    g.add_argument("--baseline-only", action="store_true", help="the shipped baseline round only; writes reports/baseline/")
    g.add_argument("--from", dest="src", help="a directory holding results.json, ranking.json, sensitivity.json, …")
    p.add_argument("--out", default=None, help="output directory (default: reports/<id>/ or reports/baseline/)")
    p.add_argument("--date", default=None, help="date-base shown in the report, YYYY-MM-DD (default: today)")
    p.add_argument("--theme", default=None, help="theme CSS (default: themes/neutral.css)")
    p.add_argument("--title", default=None)
    p.add_argument("--update-golden", action="store_true", help="with --from: rewrite tests/golden/report.{html,md}")


def write_text(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run(args):
    from . import baseline, report_md
    try:
        root = paths.project_root()
        date = args.date or datetime.date.today().isoformat()
        try:
            theme_css = theme.load(args.theme or root / "themes" / "neutral.css")
        except theme.ThemeError as e:
            print(f"report: theme: {e}", file=sys.stderr)
            return EXIT_GATE
        if args.baseline_only:
            src = baseline.round_dir(root, baseline.current_round(root)) / "derived"
            out = pathlib.Path(args.out) if args.out else paths.reports_dir(create=True) / "baseline"
        elif args.run:
            src = paths.run_dir(args.run)
            out = pathlib.Path(args.out) if args.out else paths.reports_dir(create=True) / args.run
        else:
            src = pathlib.Path(args.src)
            out = pathlib.Path(args.out) if args.out else None
        if args.update_golden:
            out = root / "tests" / "golden"
        if out is None:
            print("report: --out is required with --from", file=sys.stderr)
            return EXIT_USAGE
        inputs = load_inputs(src, root, date, args.title)
    except paths.PathError as e:
        print(f"report: {e}", file=sys.stderr)
        return e.code
    except FileNotFoundError as e:
        print(f"report: missing {e}", file=sys.stderr)
        return EXIT_MISSING
    doc = render(inputs, theme_css)
    private = any(e.get("private") for e in inputs["results"].values())
    errs = selfcheck(doc, private)
    if errs:
        print("report: selfcheck failed: " + "; ".join(errs), file=sys.stderr)
        return EXIT_GATE
    mdoc = report_md.render(inputs)
    bad = report_md.check(mdoc)
    if bad:
        print("report: Markdown check failed: " + "; ".join(bad), file=sys.stderr)
        return EXIT_GATE
    write_text(out / "report.html", doc)
    write_text(out / "report.md", mdoc)
    print(f"report: {out / 'report.html'} ({len(doc.encode('utf-8')):,} bytes) and report.md")
    return EXIT_OK
