"""`engine scorecard check|extract` (plan §7.6, §7.7): the scorecard's machine-readable block.

The block is the last ```json fenced block of the scorecard Markdown. `check` validates the
schema and cross-field rules (errors), then the methodology §6.2 caps (warnings, or errors
with --type).
"""
import json
import pathlib
import re
import sys

from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK
from .jsonio import write_json

FENCE = re.compile(r"```json[ \t]*\r?\n(.*?)\r?\n[ \t]*```", re.S)


class ScorecardError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def extract_text(text):
    blocks = FENCE.findall(text)
    if not blocks:
        raise ScorecardError("no ```json block found")
    try:
        return json.loads(blocks[-1])
    except ValueError as e:
        raise ScorecardError(f"the last json block is not valid JSON ({e})")


def extract(path):
    p = pathlib.Path(path)
    if not p.exists():
        raise ScorecardError("scorecard not found", EXIT_MISSING)
    return extract_text(p.read_text(encoding="utf-8", errors="replace"))


def cap_findings(card, type_=None):
    """Methodology §6.2 caps that depend on the method type (rules/evidence.md)."""
    out = []
    for c in CRITERIA:
        cell = (card.get("scores") or {}).get(c) or {}
        s, ev = cell.get("s"), cell.get("ev")
        if not isinstance(s, int):
            continue
        if ev == "D" and type_ in (None, "open") and s > 3:
            out.append(f"{c}: D evidence on an open method caps at 3 (source exists)")
        if ev == "D" and type_ == "closed" and s > 4:
            out.append(f"{c}: D evidence on a closed product caps at 4")
        if s >= 4 and type_ in (None, "open") and ev != "I":
            out.append(f"{c}: levels 4-5 on an open method need I evidence")
    return out


def check(card, type_=None):
    """(errors, warnings)."""
    from .validate import check as vcheck
    errors = vcheck("scorecard", card)
    caps = cap_findings(card, type_)
    return (errors + caps, []) if type_ else (errors, caps)


def vector(card, field="s"):
    return [card["scores"][c][field] for c in CRITERIA]


def configure(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--type", dest="type_", choices=["open", "closed"], default=None)
    e = sub.add_parser("extract")
    e.add_argument("file")
    e.add_argument("-o", "--out", required=True)


def run(args):
    try:
        card = extract(args.file)
        if args.action == "extract":
            write_json(args.out, card)
            print(f"scorecard extract: wrote {pathlib.Path(args.out).name}")
            return EXIT_OK
        errors, warnings = check(card, args.type_)
    except ScorecardError as e:
        print(f"scorecard {args.action}: {e}", file=sys.stderr)
        return e.code
    for w in warnings:
        print(f"scorecard check: warning: {w}")
    for e in errors:
        print(f"scorecard check: {e}", file=sys.stderr)
    if errors:
        return EXIT_GATE
    print(f"scorecard check: valid ({len(warnings)} cap warning(s))")
    return EXIT_OK
