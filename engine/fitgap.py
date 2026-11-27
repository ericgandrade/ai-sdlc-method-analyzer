"""`fitgap` (plan §7.13, stages F1 and S15): what a target can learn from the best of each reference.

`fitgap --run <id>` writes `fitgap-pre.json`:
- per criterion with target < best reference: the gap in baseline points `(best - target)·w/5`, the
  leaders, the benchmark median and the target's first unmet requirement (reconciled scorecard cell);
- per feature with target < 2 ("NA" counts 0): the references that have it at 2.
`fitgap --run <id> --project` reads the writer's `fitgap.json` and writes `fitgap-projection.json`:
the baseline total if each horizon is done, cumulatively, with every item lifting its criteria to
its stated `to_level`. Capped at 100 and labelled a hypothesis, never a score.
"""
import statistics
import sys

from .common import CRITERIA, EXIT_MISSING, EXIT_OK, EXIT_USAGE, FEATURES, PROFILES
from .jsonio import read_json, write_json
from .stats import total

HORIZONS = ["now", "30", "60-90"]


def fitgap_pre(target, refs, first_unmet=None):
    """target, refs[m]: results.json entries. refs: the benchmark references compared against."""
    w = PROFILES["baseline"]
    s = target["L1_scores"]
    crit = []
    for i, c in enumerate(CRITERIA):
        vals = {m: e["L1_scores"][i] for m, e in refs.items()}
        best = max(vals.values())
        if s[i] < best:
            crit.append({"c": c, "target": s[i], "best": best,
                         "gap_points_baseline": round((best - s[i]) * w[i] / 5, 2),
                         "leaders": sorted(m for m, v in vals.items() if v == best),
                         "median_refs": statistics.median(vals.values()),
                         "first_unmet": (first_unmet or {}).get(c)})
    feats = []
    l4 = target.get("L4") or {}
    for f in FEATURES:
        v = l4.get(f, 0)
        v = 0 if v == "NA" else v
        if v < 2:
            feats.append({"f": f, "target": l4.get(f, 0),
                          "refs_at_2": sorted(m for m, e in refs.items() if (e.get("L4") or {}).get(f) == 2)})
    return {"criteria": crit, "features": feats, "against": sorted(refs),
            "total_gap_points_baseline": round(sum(x["gap_points_baseline"] for x in crit), 2)}


def project(scores, items):
    w = PROFILES["baseline"]
    s = list(scores)
    out, unstated = {}, []
    for h in HORIZONS:
        for it in items:
            if it.get("horizon") != h:
                continue
            if not it.get("to_level"):
                unstated.append(it.get("id"))
                continue
            for c, lvl in it["to_level"].items():
                i = CRITERIA.index(c)
                s[i] = max(s[i], min(5, lvl))
        out[h] = min(100.0, total(s, w))
    return {"current": total(scores, w), "baseline_total_if_done": out, "cumulative": True,
            "items_without_to_level": unstated, "hypothesis": True,
            "label": "hypothesis: assumes each item lifts its criteria to the stated level; not a score"}


def _source(st):
    from . import state
    rid = st["sources"][0] if st["mode"] == "fitgap" else st["run_id"]
    return rid, state.run_path(rid)


def configure(p):
    p.add_argument("--run", required=True)
    p.add_argument("--against", default="all", help="all benchmark references, or comma-separated slugs")
    p.add_argument("--project", action="store_true", help="compute the cumulative projection from fitgap.json")


def run(args):
    from . import state
    try:
        st = state.load(args.run)
    except state.StateError as e:
        print(f"fitgap: {e}", file=sys.stderr)
        return e.code
    rd = state.run_path(args.run)
    src_id, src = _source(st)
    if not (src / "results.json").exists():
        print(f"fitgap: results.json missing in {src_id} (run consolidate first)", file=sys.stderr)
        return EXIT_MISSING
    results = read_json(src / "results.json")
    tgt = [e for e in results.values() if e.get("run") == src_id]
    if not tgt:
        print(f"fitgap: no target entry for {src_id} in results.json", file=sys.stderr)
        return EXIT_MISSING
    target = tgt[0]
    if args.project:
        if not (rd / "fitgap.json").exists():
            print("fitgap: fitgap.json missing (the writer produces it at S15)", file=sys.stderr)
            return EXIT_MISSING
        out = project(target["L1_scores"], read_json(rd / "fitgap.json").get("items", []))
        write_json(rd / "fitgap-projection.json", out)
        print(f"fitgap: projection (hypothesis) {out['baseline_total_if_done']}")
        return EXIT_OK
    refs = {m: e for m, e in results.items() if e.get("role") == "reference" and e.get("benchmark")}
    if args.against != "all":
        want = [s for s in args.against.split(",") if s]
        if set(want) - set(refs):
            print(f"fitgap: not benchmark references: {sorted(set(want) - set(refs))}", file=sys.stderr)
            return EXIT_USAGE
        refs = {m: refs[m] for m in want}
    cells = read_json(src / "reconciled.json").get("cells", {}) if (src / "reconciled.json").exists() else {}
    out = fitgap_pre(target, refs, {c: v.get("first_unmet") for c, v in cells.items() if v.get("first_unmet")})
    out["source_run"] = src_id
    write_json(rd / "fitgap-pre.json", out)
    print(f"fitgap: {len(out['criteria'])} criteria below best, {len(out['features'])} features below 2")
    return EXIT_OK
