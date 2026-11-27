"""Shipped baseline (plan §0.3 #42, §7.15): round resolution and `engine baseline verify`.
`promote` arrives with the run layer (Phase 2)."""
import hashlib
import json
import pathlib
import sys

from .common import EXIT_INTEGRITY, EXIT_MISSING, EXIT_OK, EXIT_USAGE


def current_round(root="."):
    p = pathlib.Path(root) / "baseline" / "current"
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def round_dir(root=".", round_id=None):
    rid = round_id or current_round(root) or "_none_"
    return pathlib.Path(root) / "baseline" / "rounds" / rid


def rounds(root="."):
    base = pathlib.Path(root) / "baseline" / "rounds"
    return sorted(p.name for p in base.iterdir() if p.is_dir()) if base.exists() else []


def verify(root=".", round_id=None):
    """Return (problems, n_files). Problems: missing, changed or unlisted files."""
    d = round_dir(root, round_id)
    m = d / "MANIFEST.json"
    if not m.exists():
        return [f"{d.name}: MANIFEST.json missing"], 0
    files = json.loads(m.read_text(encoding="utf-8"))["files"]
    problems = []
    for rel, sha in sorted(files.items()):
        p = d / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            problems.append(f"changed {rel}")
    for p in sorted(d.rglob("*")):
        rel = p.relative_to(d).as_posix()
        if p.is_file() and rel != "MANIFEST.json" and rel not in files:
            problems.append(f"unlisted {rel}")
    return problems, len(files)


def configure(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    v = sub.add_parser("verify", help="check MANIFEST.json hashes (exit 4 on mismatch)")
    v.add_argument("--root", default=".")
    v.add_argument("--round", default=None, help="round id (default: every round present)")
    sub.add_parser("promote", help="not implemented yet (needs the run layer)")


def run(args):
    if args.action != "verify":
        print("baseline promote: not implemented", file=sys.stderr)
        return EXIT_USAGE
    ids = [args.round] if args.round else rounds(args.root)
    if not ids:
        print("baseline verify: no rounds found", file=sys.stderr)
        return EXIT_MISSING
    bad = False
    for rid in ids:
        problems, n = verify(args.root, rid)
        for pr in problems:
            print(f"baseline verify: {rid}: {pr}", file=sys.stderr)
        bad = bad or bool(problems)
        if not problems:
            print(f"baseline verify: {rid}: {n} files match")
    return EXIT_INTEGRITY if bad else EXIT_OK
