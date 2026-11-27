"""`consolidate` (plan §7.9, stage S11 and C1): build results.json (schema §7.6).

Baseline references come from `baseline/rounds/<round>/` (l1.json, lenses/, tokens.json) and the
registry. Every target run listed is consolidated against **the round named in its own
`round_id`** (#62), never against `baseline/current`.

Rules (the prototype's consolidation script):
- `L2_scores[c] = max(L1[c], ceiling[c])`; `L4_points = Σ v` with "NA" = 0 (listed in `L4_na`);
  `L4_coverage = round(100·points/68)`; groups `round(100·Σ/(2·len))`; `L3_num = LEVELS.index`; `C8 = L1[7]`.
- U (§7.6): for references `U.baseline = U_recorded`; every other profile, and every target, uses
  `total_u(u, w)`. No other module recomputes U.
- Design-only targets: `L1_scores = RA_scores`, `L1 = RA_total`, and `design` carries D, r, RA and the gap.
- Documentation-only targets carry `range` (engine ranges) and never enter a ranking as a point.
"""
import pathlib
import sys

from . import baseline, paths, stats
from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK, EXIT_USAGE, FEATURES, GROUPS, LEVELS, PROFILES
from .jsonio import read_json, write_json


class ConsolidateError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def totals(scores):
    return {p: stats.total(scores, w) for p, w in PROFILES.items()}


def totals_u(u):
    return {p: stats.total_u(u, w) for p, w in PROFILES.items()}


def lens_fields(lenses, scores):
    """L2, L3 and L4 fields of a results entry from a (final) lenses file."""
    out = {"L2_scores": None, "L2": None, "L3": None, "L3_num": None, "L3_conf": None, "L4": None,
           "L4_points": None, "L4_coverage": None, "L4_groups": None, "L4_na": []}
    if not lenses:
        return out
    l2 = lenses.get("L2")
    if l2:
        ceiling = l2.get("ceiling") or {}
        s2 = [max(scores[i], (ceiling.get(c) or {}).get("s", 0)) for i, c in enumerate(CRITERIA)]
        out["L2_scores"], out["L2"] = s2, totals(s2)
    l3 = lenses.get("L3")
    if l3 and l3.get("level") in LEVELS:
        out.update(L3=l3["level"], L3_num=LEVELS.index(l3["level"]), L3_conf=l3.get("conf"))
    l4 = lenses.get("L4")
    if l4:
        vals = {f: (l4.get(f) or {}).get("v", 0) for f in FEATURES}
        out["L4"] = vals                                     # numbers (and "NA") only, never lens text
        out["L4_na"] = [f for f in FEATURES if vals[f] == "NA"]
        num = {f: (0 if v == "NA" else v) for f, v in vals.items()}
        pts = sum(num.values())
        out["L4_points"] = pts
        out["L4_coverage"] = round(100 * pts / (2 * len(FEATURES)))
        out["L4_groups"] = {g: round(100 * sum(num[f"F{i}"] for i in rng) / (2 * len(rng))) for g, rng in GROUPS.items()}
    return out


def l5_fields(row):
    if not row:
        return None
    return {k: row.get(k) for k in ("T1", "T2", "T3", "T0")} | {
        "tokenizer": row.get("tokenizer"), "comparable": bool(row.get("comparable"))}


def design_block(D, r):
    ra = [round(s * x, 2) for s, x in zip(D, r)]
    dt, rt = totals(D), totals(ra)
    return {"D_scores": list(D), "r": list(r), "RA_scores": ra, "design_total": dt, "RA_total": rt,
            "realization_gap": {p: round(dt[p] - rt[p], 1) for p in PROFILES}}


def entry(*, name, origin, role, type_, host, status, benchmark, scores, u, U_recorded=None, lenses=None,
          tokens_row=None, design=None, self_assessment=False, comparison="same-round", round_id=None,
          reliability=None, models=None, excluded_dirs=None, range_=None, extra=None):
    l1 = design["RA_total"] if design else totals(scores)
    U = totals_u(u)
    if U_recorded is not None:
        U["baseline"] = U_recorded
    e = {"name": name, "origin": origin, "role": role, "type": type_, "host": host, "status": status,
         "benchmark": bool(benchmark), "self_assessment": bool(self_assessment), "comparison": comparison,
         "round_id": round_id, "L1_scores": list(scores), "u": [round(x, 4) for x in u], "L1": l1, "design": design,
         "U": U, "U_recorded": U_recorded, "C8": scores[7], "L5": l5_fields(tokens_row), "reliability": reliability,
         "models": models, "excluded_dirs": excluded_dirs or [], "range": range_}
    e.update(lens_fields(lenses, scores))
    e.update(extra or {})
    return e


# ------------------------------------------------------------------ references

def _registry(root):
    from .registry import entries, load_registry
    return {e["slug"]: e for e in entries(load_registry(root))}


def reference_entries(root, round_id, include=None):
    d = baseline.round_dir(root, round_id)
    if not (d / "l1.json").exists():
        raise ConsolidateError(f"baseline round {round_id}: l1.json missing", EXIT_MISSING)
    l1 = read_json(d / "l1.json")
    tok = read_json(d / "tokens.json").get("methods", {}) if (d / "tokens.json").exists() else {}
    reg = _registry(root)
    out = {}
    for slug in sorted(l1):
        if include and slug not in include:
            continue
        b, e = l1[slug], reg.get(slug, {})
        lp = d / "lenses" / f"{slug}.json"
        out[slug] = entry(name=e.get("name", slug), origin=e.get("origin", ""), role="reference",
                          type_=e.get("type", "open"), host=e.get("host", ""), status="implemented",
                          benchmark=bool(e.get("benchmark")), scores=b["scores"], u=b["u"],
                          U_recorded=b.get("U_recorded"), lenses=read_json(lp) if lp.exists() else None,
                          tokens_row=tok.get(slug), round_id=round_id)
    if include and set(include) - set(out):
        raise ConsolidateError(f"not in round {round_id}: {sorted(set(include) - set(out))}", EXIT_MISSING)
    return out


# ------------------------------------------------------------------ targets

def comparison_for(st, rd, root):
    """Protocol §9 / #41: same-round only if (a) the run's own round records an A2 pass for this
    pipeline major.minor and (b) the run's calibration shows no drift."""
    from .state import reproduction_passes
    version, rnd = st["round_id"].split("+", 1)
    if not reproduction_passes(root, rnd, version):
        return "cross-round"
    cal = rd / "calibration.json"
    if not cal.exists() or read_json(cal).get("drift"):
        return "cross-round"
    return "same-round"


def _u_for(rd, vector, cells, r=None):
    pre = read_json(rd / "reconcile-pre.json") if (rd / "reconcile-pre.json").exists() else {"cells": {}}
    u = []
    for i, c in enumerate(CRITERIA):
        p = pre["cells"].get(c) or {}
        confs = [x for x in (p.get("conf_worst"), (cells.get(c) or {}).get("conf")) if x] or ["M"]
        scores = list((p.get("scores") or {}).values()) or [vector[i]]
        u.append(stats.criterion_u(confs, scores, r[i] if r else 1.0, vector[i] if r else None))
    return u


def _reliability(rd):
    if not (rd / "alpha.json").exists():
        return None
    a = read_json(rd / "alpha.json")
    out = {k: a.get(k) for k in ("alpha", "ci90", "units", "coders")}
    if (rd / "calibration.json").exists():
        cal = read_json(rd / "calibration.json")
        refs = sorted(cal.get("refs", {}))
        per = [cal["refs"][r]["per_scorer"][i] for r in refs for i in sorted(cal["refs"][r]["per_scorer"])]
        out["calibration"] = {"refs": refs, "delta_raw": [p["delta_raw"] for p in per],
                              "delta_reconciled": [p["delta_reconciled"] for p in per], "drift": bool(cal.get("drift"))}
    return out


def _redteam(rd):
    from .adjudication import open_contests
    rt = read_json(rd / "redteam.json") if (rd / "redteam.json").exists() else {}
    decided = set()
    if (rd / "adjudication.json").exists():
        decided = {d.get("contest_id") for d in read_json(rd / "adjudication.json").get("decisions", [])}
    pending = [c for c in open_contests(rd) if c["contest_id"] not in decided] if rt else []
    return {"completed": bool(rt.get("completed")), "open_contests": len(pending)}


def target_entry(run_id, root):
    from . import state
    st = state.load(run_id)
    rd = state.run_path(run_id)
    if st["mode"] in ("compare", "fitgap"):
        raise ConsolidateError(f"{run_id} is a {st['mode']} run, not an assessment run", EXIT_USAGE)
    t = st["target"]
    rec = read_json(rd / "target.json") if (rd / "target.json").exists() else {}
    common = dict(name=t.get("name", t["slug"]), origin=rec.get("origin", ""), role="target",
                  host=rec.get("host") or st.get("host") or "", benchmark=False,
                  self_assessment=st.get("self_assessment", False), round_id=st["round_id"])
    if st["mode"] == "docs":
        from .ranges import docs_entry_fields
        f = docs_entry_fields(rd, root, st["round_id"].split("+", 1)[1], rec.get("type_declaration"))
        return entry(type_="docs", status="implemented", comparison="cross-round", extra={"run": run_id}, **common, **f)
    if rec:
        from .intake import IntakeError, verify_snapshot
        try:
            verify_snapshot(run_id)                      # gate G9
        except IntakeError as e:
            raise ConsolidateError(str(e), e.code)
    for f in ("l1.final.json", "lenses.final.json"):
        if not (rd / f).exists():
            raise ConsolidateError(f"{run_id}: {f} missing (run apply-audit first)", EXIT_MISSING)
    l1 = read_json(rd / "l1.final.json")
    lenses = read_json(rd / "lenses.final.json")
    cells = read_json(rd / "reconciled.json").get("cells", {}) if (rd / "reconciled.json").exists() else {}
    vector = l1["vector"]
    design = None
    if t.get("status") == "design-only":
        r = l1.get("r") or [1.0] * 16
        design = design_block(vector, r)
        scores, u = design["RA_scores"], _u_for(rd, vector, cells, r)
    else:
        scores, u = vector, _u_for(rd, vector, cells)
    tok = read_json(rd / "tokens.json").get("methods", {}) if (rd / "tokens.json").exists() else {}
    models = {k.split(":", 1)[1]: v.get("model") for k, v in st["stages"].items()
              if k.startswith("S04:") and v.get("status") == "done"} or None
    return entry(type_=t.get("type", "open"), status=t.get("status", "implemented"), scores=scores, u=u,
                 lenses=lenses, tokens_row=tok.get(t["slug"]), design=design,
                 comparison=comparison_for(st, rd, root), reliability=_reliability(rd), models=models,
                 excluded_dirs=rec.get("excluded_dirs", []),
                 extra={"run": run_id, "redteam": _redteam(rd)}, **common)


# ------------------------------------------------------------------ driver

def consolidate(run_id=None, out_dir=None, include=None, targets=(), root=None, round_id=None):
    """Return results; write `<out_dir or run dir>/results.json`."""
    from . import state
    root = root or paths.project_root()
    targets = list(targets or [])
    st = None
    if run_id:
        st = state.load(run_id)
        if st["mode"] in ("compare", "fitgap"):
            targets = list(st.get("sources", [])) + [t for t in targets if t not in st.get("sources", [])]
        else:
            targets = [run_id] + [t for t in targets if t != run_id]
    rounds = set()
    if st:
        rounds.add(st["round_id"].split("+", 1)[1])
    for t in targets:
        rounds.add(state.load(t)["round_id"].split("+", 1)[1])
    if len(rounds) > 1:
        raise ConsolidateError(f"runs come from different rounds {sorted(rounds)} (#62)")
    rnd = round_id or (rounds.pop() if rounds else baseline.current_round(root))
    if not rnd:
        raise ConsolidateError("no baseline round", EXIT_MISSING)
    results = reference_entries(root, rnd, include)
    for t in targets:
        e = target_entry(t, root)
        slug = state.load(t)["target"]["slug"]
        key = slug if slug not in results else f"{slug}@{t}"
        results[key] = e
    from .validate import check
    errors = list(check("results", results))
    if errors:
        raise ConsolidateError("results.json would be invalid: " + "; ".join(errors[:5]))
    dest = pathlib.Path(out_dir) if out_dir else state.run_path(run_id)
    write_json(dest / "results.json", results)
    return results


def configure(p):
    p.add_argument("--run", default=None)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--include", default=None, help="comma-separated reference slugs")
    g.add_argument("--all-refs", action="store_true", help="every reference of the round (default)")
    p.add_argument("--targets", default=None, help="comma-separated extra target run ids")
    p.add_argument("--out", default=None, help="write results.json here (required without --run)")
    p.add_argument("--round", default=None, help="baseline round (without --run; default: current)")


def split(s):
    return [x for x in (s or "").split(",") if x]


def run(args):
    from . import state
    from .ranges import RangesError
    if not args.run and not args.out:
        print("consolidate: --run or --out is required", file=sys.stderr)
        return EXIT_USAGE
    try:
        res = consolidate(args.run, args.out, split(args.include) or None, split(args.targets), round_id=args.round)
    except (ConsolidateError, RangesError, state.StateError) as e:
        print(f"consolidate: {e}", file=sys.stderr)
        return e.code
    for slug, e in res.items():
        print(f"consolidate: {slug}: baseline {e['L1']['baseline']} (U {e['U']['baseline']})")
    return EXIT_OK
