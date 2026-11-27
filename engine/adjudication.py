"""Person adjudication flow (plan §5.16, #46): `adjudication request` and `adjudication import`.

`request` writes runs/<id>/adjudication-request.md with each open contest, both positions and
the cited evidence, and no totals, ranks or other cells; the run then waits for a person
(`waiting-external`). `import` (interactive only, #78) reads the filled decision table,
validates it and writes adjudication.json.
"""
import pathlib
import re
import sys

from . import paths, state
from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK
from .jsonio import read_json, write_json

BANNER = "> **Private: contains the assessment of a private target.**"
NOTE = "Handing this file to a person is your own act; the tool sends nothing."
COLUMNS = ["contest_id", "c", "kind", "decision", "after", "after_r", "boundary_verdict", "evidence", "reason"]


class AdjudicationError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def open_contests(rd):
    rt = read_json(rd / "redteam.json")
    return [dict(c, contest_id=i) for i, c in enumerate(rt.get("contests", [])) if c.get("outcome") == "to-adjudicator"]


def _kind(contest):
    t = str(contest.get("kind") or contest.get("type") or "")
    return "r" if t in ("r", "f") else "boundary" if t == "boundary" else "score"


def request(run_id):
    st = state.load(run_id)
    rd = state.run_path(run_id)
    if not (rd / "redteam.json").exists():
        raise AdjudicationError("redteam.json missing", EXIT_MISSING)
    contests = open_contests(rd)
    if not contests:
        raise AdjudicationError("no contest is marked to-adjudicator")
    rec = read_json(rd / "reconciled.json") if (rd / "reconciled.json").exists() else {"cells": {}}
    target = read_json(rd / "target.json") if (rd / "target.json").exists() else {}
    lines = []
    if target.get("private", True):
        lines += [BANNER, ""]
    lines += ["# Adjudication request", "", NOTE, "",
              "Decide each contest on the cited evidence. When two levels remain defensible, take the lower (R-LOW).", ""]
    for c in contests:
        cell = (rec.get("cells") or {}).get(c["c"], {})
        lines += [f"## Contest {c['contest_id']}: {c['c']} ({_kind(c)})", "",
                  f"- Reconciled position: {cell.get('s', 'n/a')}" + (f", r {cell['r']}" if 'r' in cell else ""),
                  f"- Red-team position: {c.get('after', c.get('proposed', 'see evidence'))}",
                  f"- Red-team evidence: {c.get('evidence', '')}",
                  f"- Reconciler citations: {', '.join(cell.get('cites', []))}", ""]
    lines += ["## Decisions", "", "Fill one row per contest. `decision` is upheld or rejected; `after` (score contests), "
              "`after_r` (0.6-1.0, r contests) and `boundary_verdict` (in or out, boundary contests).", "",
              "| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for c in contests:
        lines.append(f"| {c['contest_id']} | {c['c']} | {_kind(c)} |  |  |  |  |  |  |")
    paths.assert_portable(lines)
    (rd / "adjudication-request.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    state.set_waiting_external(run_id)
    return rd / "adjudication-request.md"


def _num(x, cast):
    x = (x or "").strip()
    if x in ("", "-", "null", "None"):
        return None
    try:
        return cast(x)
    except ValueError:
        raise AdjudicationError(f"not a number: {x!r}")


def parse_table(text):
    rows, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if cells[:2] == ["contest_id", "c"]:
                header = cells
            continue
        if all(re.fullmatch(r"-+", c or "-") for c in cells):
            continue
        rows.append(dict(zip(header, cells)))
    if header is None:
        raise AdjudicationError("no decision table found")
    out = []
    for r in rows:
        out.append({"contest_id": _num(r.get("contest_id"), int), "c": r.get("c", ""), "kind": r.get("kind", ""),
                    "decision": r.get("decision", ""), "after": _num(r.get("after"), int),
                    "after_r": _num(r.get("after_r"), float), "boundary_verdict": (r.get("boundary_verdict") or None),
                    "evidence": r.get("evidence", ""), "reason": r.get("reason", "")})
    return out


def validate_decisions(decisions, contests):
    """Every contest answered; every decision with evidence; kind-specific fields (§5.16)."""
    errors = []
    by_id = {d.get("contest_id"): d for d in decisions}
    for c in contests:
        d = by_id.get(c["contest_id"])
        if d is None or d.get("decision") not in ("upheld", "rejected"):
            errors.append(f"contest {c['contest_id']} ({c['c']}): no decision")
            continue
        if not str(d.get("evidence") or "").strip():
            errors.append(f"contest {c['contest_id']}: decision without evidence")
        kind = d.get("kind")
        if kind not in ("score", "r", "boundary"):
            errors.append(f"contest {c['contest_id']}: kind must be score, r or boundary")
        if d.get("c") not in CRITERIA:
            errors.append(f"contest {c['contest_id']}: unknown criterion {d.get('c')!r}")
        if d.get("decision") == "upheld":
            if kind == "score" and not (isinstance(d.get("after"), int) and 0 <= d["after"] <= 5):
                errors.append(f"contest {c['contest_id']}: an upheld score contest needs after 0-5")
            if kind == "r":
                r = d.get("after_r")
                if r is None:
                    errors.append(f"contest {c['contest_id']}: an r contest needs after_r")
                elif not 0.6 <= r <= 1.0:
                    errors.append(f"contest {c['contest_id']}: after_r must be within 0.6-1.0")
            if kind == "boundary" and d.get("boundary_verdict") not in ("in", "out"):
                errors.append(f"contest {c['contest_id']}: boundary_verdict must be in or out")
        elif kind == "r" and d.get("after_r") is not None and not 0.6 <= d["after_r"] <= 1.0:
            errors.append(f"contest {c['contest_id']}: after_r must be within 0.6-1.0")
    extra = set(by_id) - {c["contest_id"] for c in contests}
    if extra:
        errors.append(f"decisions for unknown contests: {sorted(extra, key=str)}")
    return errors


def import_decisions(run_id, file):
    st = state.load(run_id)
    state.require_tty(f"adjudication import --run {run_id} {file}", st.get("python", "python3"))
    rd = state.run_path(run_id)
    p = pathlib.Path(file)
    if not p.exists():
        raise AdjudicationError("decision file not found", EXIT_MISSING)
    text = p.read_text(encoding="utf-8")
    decisions = read_json(p)["decisions"] if p.suffix == ".json" else parse_table(text)
    errors = validate_decisions(decisions, open_contests(rd))
    if errors:
        raise AdjudicationError("; ".join(errors))
    out = {"adjudicator": "person", "decisions": decisions}
    write_json(rd / "adjudication.json", out)
    return out


def configure(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    r = sub.add_parser("request")
    r.add_argument("--run", required=True)
    i = sub.add_parser("import")
    i.add_argument("--run", required=True)
    i.add_argument("file")


def run(args):
    try:
        if args.action == "request":
            out = request(args.run)
            print(f"adjudication request: wrote {paths.portable(out, run=state.run_path(args.run))}; "
                  f"run is waiting-external. After the person fills it: engine adjudication import, then state resume")
        else:
            out = import_decisions(args.run, args.file)
            print(f"adjudication import: {len(out['decisions'])} decision(s) recorded")
    except (AdjudicationError, state.StateError, paths.PathError) as e:
        print(f"adjudication {args.action}: {e}", file=sys.stderr)
        return e.code
    return EXIT_OK
