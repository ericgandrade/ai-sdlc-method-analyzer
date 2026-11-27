"""`engine verify-freeze`: check the SHA-256 records in methodology/FREEZE.md (plan §2)."""
import hashlib
import pathlib
import re
import sys

from .common import EXIT_INTEGRITY, EXIT_MISSING, EXIT_OK

ROW = re.compile(r"^\|\s*([^|\s]+)\s*\|\s*([0-9a-f]{64})\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def records(root):
    """[(file name, sha256, date, normative)] from FREEZE.md under <root>/methodology."""
    text = (pathlib.Path(root) / "methodology" / "FREEZE.md").read_text(encoding="utf-8")
    return [m.groups() for m in map(ROW.match, text.splitlines()) if m]


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def verify(root, only=None):
    """Return [(file, expected, actual or None)] for every mismatch."""
    bad = []
    for name, expected, _, _ in records(root):
        rel = f"methodology/{name}"
        if only and pathlib.PurePosixPath(only).as_posix() not in (rel, name):
            continue
        p = pathlib.Path(root) / rel
        actual = sha256(p) if p.exists() else None
        if actual != expected:
            bad.append((rel, expected, actual))
    return bad


def configure(p):
    p.add_argument("--root", default=".", help="repository root (default: current directory)")
    p.add_argument("--file", help="check one file only")
    p.add_argument("--print", action="store_true", dest="print_",
                   help="print the sha256 of every methodology/*.md file (or of --file)")


def run(args):
    root = pathlib.Path(args.root)
    if not (root / "methodology" / "FREEZE.md").exists():
        print("verify-freeze: methodology/FREEZE.md not found", file=sys.stderr)
        return EXIT_MISSING
    if args.print_:
        files = [root / args.file] if args.file else sorted((root / "methodology").glob("*.md"))
        for f in files:
            if not f.exists():
                print(f"verify-freeze: {f.name} not found", file=sys.stderr)
                return EXIT_MISSING
            print(f"{sha256(f)}  {f.relative_to(root).as_posix()}")
        return EXIT_OK
    if args.file and not any(args.file in (f"methodology/{n}", n) for n, *_ in records(root)):
        print(f"verify-freeze: {args.file} has no freeze record", file=sys.stderr)
        return EXIT_MISSING
    bad = verify(root, args.file)
    for rel, expected, actual in bad:
        print(f"verify-freeze: MISMATCH {rel}: expected {expected[:12]}…, got {(actual or 'missing')[:12]}",
              file=sys.stderr)
    if bad:
        return EXIT_INTEGRITY
    n = 1 if args.file else len(records(root))
    print(f"verify-freeze: {n} file(s) match")
    return EXIT_OK
