"""Shipped baseline (plan §0.3 #42, §7.15): round resolution, `engine baseline verify`
and `engine baseline promote` (interactive only, #78)."""
import hashlib
import json
import pathlib
import sys

from .common import EXIT_INTEGRITY, EXIT_MISSING, EXIT_OK, EXIT_USAGE

DERIVED_SEED = 20261127


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
    pr = sub.add_parser("promote", help="promote a closed reference run into its round (interactive only)")
    pr.add_argument("--run", required=True)
    pr.add_argument("--root", default=".")


def refresh_manifest(root=".", round_id=None):
    """Recompute MANIFEST.json `files` for every file in the round (notes are kept)."""
    from .jsonio import read_json, write_json
    d = round_dir(root, round_id)
    m = d / "MANIFEST.json"
    man = read_json(m) if m.exists() else {"files": {}, "notes": {}}
    man["files"] = {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(d.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    write_json(m, man)
    return man


class PromoteError(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def promote(run_id, root="."):
    """Write a closed reference run into baseline/rounds/<the run's round>/ only (#62)."""
    from . import state
    from .jsonio import read_json, write_json
    from .registry import entries, load_registry
    st = state.load(run_id)
    state.require_tty(f"baseline promote --run {run_id}", st.get("python", "python3"))
    if st["mode"] != "reference" or st["status"] != "closed":
        raise PromoteError("only a closed reference run can be promoted")
    rid = st["round_id"].split("+", 1)[-1]
    d = round_dir(root, rid)
    if not d.is_dir():
        raise PromoteError(f"round {rid} of the run does not exist under baseline/rounds/")
    rd = state.run_path(run_id)
    slug = st["target"]["slug"]
    reg = {e["slug"]: e for e in entries(load_registry(root))}
    target = read_json(rd / "target.json")
    if slug not in reg or target.get("pin") != reg[slug].get("pin"):
        raise PromoteError(f"pin mismatch: the run's pin differs from the registry pin of {slug}", 4)
    changelog = pathlib.Path(root) / "CHANGELOG.md"
    if not changelog.exists() or run_id not in changelog.read_text(encoding="utf-8"):
        raise PromoteError(f"CHANGELOG.md has no entry naming run {run_id}")
    for f in ("l1.final.json", "lenses.final.json", "reconcile-pre.json", "lens-audit.json", "tokens.json"):
        if not (rd / f).exists():
            raise PromoteError(f"run file {f} missing", EXIT_MISSING)
    row = promoted_l1_row(st, rd)
    tok = read_json(rd / "tokens.json").get("methods", {}).get(slug)
    if tok is None:
        raise PromoteError(f"tokens.json of the run has no row for {slug}", EXIT_MISSING)
    write_json(d / "lenses" / f"{slug}.json", read_json(rd / "lenses.final.json"))
    write_json(d / "audits" / f"{slug}.json", read_json(rd / "lens-audit.json"))
    l1 = read_json(d / "l1.json")
    l1[slug] = row
    write_json(d / "l1.json", l1)
    tp = d / "tokens.json"
    tokens = read_json(tp) if tp.exists() else {"methods": {}}
    tokens.setdefault("methods", {})[slug] = tok
    write_json(tp, tokens)
    refresh_derived(root, rid)
    refresh_manifest(root, rid)
    return rid


def promoted_l1_row(st, rd):
    """The l1.json row of a promoted reference run: the final vector, the pre-reconciliation pairs of
    the two active scorer instances, u from those pairs (plan 7.3), and U_recorded = total_u(u, baseline):
    a re-scored reference records the engine's own U (see TODO.md)."""
    from . import state, stats
    from .common import CRITERIA, PROFILES
    from .consolidate import _u_for
    from .jsonio import read_json
    final = read_json(rd / "l1.final.json")
    pre = read_json(rd / "reconcile-pre.json")
    insts = state.active_instances(st)[:2]
    pairs = []
    for c in CRITERIA:
        sc = pre["cells"][c]["scores"]
        if any(i not in sc for i in insts):
            raise PromoteError(f"reconcile-pre.json lacks scores of {insts} for {c}", EXIT_MISSING)
        pairs.append([sc[i] for i in insts])
    cells = read_json(rd / "reconciled.json").get("cells", {}) if (rd / "reconciled.json").exists() else {}
    u = [round(x, 4) for x in _u_for(rd, final["vector"], cells)]
    models = [st["stages"].get(f"S04:{i}", {}).get("model") or i for i in insts]
    return {"scores": final["vector"], "pairs": pairs, "u": u, "scorers": models,
            "U_recorded": stats.total_u(u, PROFILES["baseline"]), "run": st["run_id"]}


def refresh_derived(root=".", round_id=None):
    """Recompute derived/{results,ranking,sensitivity}.json of a round, keeping its seed and draws."""
    from . import rank, sensitivity
    from .consolidate import consolidate
    from .jsonio import read_json, write_json
    d = round_dir(root, round_id) / "derived"
    old = read_json(d / "sensitivity.json") if (d / "sensitivity.json").exists() else {}
    results = consolidate(out_dir=d, root=root, round_id=round_id)
    write_json(d / "ranking.json", rank.rank(results))
    write_json(d / "sensitivity.json", sensitivity.sensitivity(
        results, old.get("seed", DERIVED_SEED), old.get("draws", sensitivity.DEFAULT_DRAWS)))


def run(args):
    if args.action == "promote":
        from . import state
        try:
            rid = promote(args.run, args.root)
        except (PromoteError, state.StateError) as e:
            print(f"baseline promote: {e}", file=sys.stderr)
            return e.code
        print(f"baseline promote: {args.run} written into round {rid}")
        return EXIT_OK
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
