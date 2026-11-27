"""`superiority` (plan §7.12, methodology §9, stage S12): the verdict for each target.

`superiority()` is the plan's code. The CLI wrapper checks the pre-conditions first; each unmet one
gives `verdict: "none"` with a reason:
1. `refs` are exactly the 9 `benchmark: true` references (an additional reference is rejected);
2. the target's `comparison` is `same-round` (protocol §9);
3. `weakest_vs_median` is present for the target (methodology §10.4);
4. no contest is open (G8).
The S3 inputs come only from `sensitivity.verdict_set[target]` (#47).

Interpretations (protocol §13, D6): `strict` (default) requires S5 for "Conditionally superior"
(I-1) and reads the S2/S3 clause as "S2 failures ≤ 1 and (S2 or S3) short" (I-2); `literal` reads
methodology §9 as written: "S2 fails for at most one profile, or S3 falls short".
"""
import statistics
import sys

from .common import CORE, CRITERIA, EXIT_MISSING, EXIT_OK, EXIT_USAGE, PROFILES
from .jsonio import read_json, write_json
from .registry import BENCHMARK_COUNT
from .stats import margin, total

NOTES = {
    "I-1": "strict: 'Conditionally superior' also requires S5 (methodology 9 lists S1, S4, S6 and S7); "
           "literal: S5 is not required for that verdict.",
    "I-2": "strict: S2 failures <= 1 and at least one of S2 or S3 not fully passing; "
           "literal: S2 fails for at most one profile, or S3 falls short.",
    "U": "every U is read from results.json (plan 7.6); B(P) is the tied best reference with the larger U[P], then slug order.",
}


class SuperiorityError(ValueError):
    pass


def superiority(x, refs, p_first, loo_first_count, redteam_done, alpha, interpretation="strict"):
    """x, refs[m]: {"s":[16], "U":{profile: U}} taken from results.json (§7.6 U rule; never recomputed here);
    p_first: {"centred":p,"uniform":p,"score_perturbation":p} for x."""
    res, fails = {}, []

    def best_ref(P):
        # refs = benchmark set only (benchmark == true). Ties: larger U wins (stricter margin), then slug order.
        w = PROFILES[P]
        top = max(total(refs[m]["s"], w) for m in refs)
        tied = sorted((m for m in refs if total(refs[m]["s"], w) == top), key=lambda m: (-refs[m]["U"][P], m))
        return tied[0], top

    def check_profile(P):
        w = PROFILES[P]
        b, tb = best_ref(P)
        tx = total(x["s"], w)
        m = margin(x["U"][P], refs[b]["U"][P])
        return {"best": b, "delta": round(tx - tb, 1), "M": m, "pass": tx - tb >= m}
    res["S1"] = check_profile("baseline")
    s2 = {P: check_profile(P) for P in ("equal", "startup", "regulated", "autonomous")}
    res["S2"] = {"profiles": s2, "failed": [P for P, r in s2.items() if not r["pass"]]}
    res["S2"]["pass"] = not res["S2"]["failed"]
    s3 = {"centred": p_first["centred"] >= 0.90, "uniform": p_first["uniform"] >= 0.75,
          "score_perturbation": p_first["score_perturbation"] >= 0.90, "loo": loo_first_count == 16}
    res["S3"] = {"checks": s3, "pass": all(s3.values())}
    med = [statistics.median(refs[m]["s"][i] for m in refs) for i in range(16)]
    best = [max(refs[m]["s"][i] for m in refs) for i in range(16)]
    below = [CRITERIA[i] for i in range(16) if x["s"][i] < med[i]]
    res["S4"] = {"below_median": below, "pass": not below}
    bic = [CRITERIA[i] for i in range(16) if x["s"][i] >= best[i] - 0.25]
    core = [c for c in bic if c in CORE]
    res["S5"] = {"best_in_class": bic, "core": core, "pass": len(bic) >= 6 and len(core) >= 3}
    res["S6"] = {"pass": bool(redteam_done)}
    res["S7"] = {"alpha": alpha, "pass": alpha is not None and alpha >= 0.667}
    ok = {k: res[k]["pass"] for k in ("S1", "S2", "S3", "S4", "S5", "S6", "S7")}
    n2 = len(res["S2"]["failed"])
    if interpretation == "strict":       # I-1 (S5 required) + I-2 (S2 ≤ 1 failure AND (S2 or S3) short)
        cond = ok["S5"] and n2 <= 1 and (not ok["S2"] or not ok["S3"])
    else:                                # literal §9: (S2 fails for at most one profile) OR (S3 falls short)
        cond = (n2 <= 1) or (not ok["S3"])
    if all(ok.values()):
        verdict = "Superior"
    elif ok["S1"] and ok["S4"] and ok["S6"] and ok["S7"] and cond:
        verdict = "Conditionally superior"
    elif abs(res["S1"]["delta"]) < res["S1"]["M"]:
        verdict = "Comparable"
    else:
        verdict = "Not superior"
    res["failed"] = [k for k, v in ok.items() if not v]
    res["verdict"] = verdict
    res["interpretation"] = interpretation
    return res


def verdict_refs(results):
    """The benchmark set as superiority() input; rejects anything else."""
    refs = {m: e for m, e in results.items() if e.get("role") == "reference" and e.get("benchmark")}
    return {m: {"s": e["L1_scores"], "U": e["U"]} for m, e in sorted(refs.items())}


def check_refs(refs, results):
    extra = [m for m in refs if not (results.get(m, {}).get("role") == "reference" and results[m].get("benchmark"))]
    if extra:
        raise SuperiorityError(f"refs must be benchmark references only; additional: {sorted(extra)}")
    if len(refs) != BENCHMARK_COUNT:
        raise SuperiorityError(f"refs must be exactly the {BENCHMARK_COUNT} benchmark references, got {len(refs)}")


def evaluate(results, ranking, sens, target, interpretation="strict", refs=None):
    e = results[target]
    none = lambda reason: {"verdict": "none", "reason": reason, "interpretation": interpretation, "notes": NOTES}
    refs = verdict_refs(results) if refs is None else refs
    try:
        check_refs(refs, results)
    except SuperiorityError as err:
        return none(str(err))
    if e.get("range"):
        return none("documentation-only targets are reported as a range, never as a point (protocol 6)")
    if e.get("comparison") != "same-round":
        return none("cross-round comparison: no superiority verdict (protocol 9)")
    if target not in (ranking.get("weakest_vs_median") or {}):
        return none("weakest_vs_median missing for the target (methodology 10.4)")
    if (e.get("redteam") or {}).get("open_contests"):
        return none("a contest is still open (gate G8)")
    vs = (sens.get("verdict_set") or {}).get(target)
    if not vs:
        return none("verdict_set missing for the target in sensitivity.json (#47)")
    out = superiority({"s": e["L1_scores"], "U": e["U"]}, refs, vs["p_first"], vs["loo_first_count"],
                      (e.get("redteam") or {}).get("completed"), (e.get("reliability") or {}).get("alpha"),
                      interpretation)
    out["notes"] = NOTES
    return out


def configure(p):
    p.add_argument("--run", required=True)
    p.add_argument("--target", default=None, help="slug in results.json (default: every target)")
    p.add_argument("--interpretation", choices=("strict", "literal"), default="strict")


def run(args):
    from . import state
    rd = state.run_path(args.run)
    files = {n: rd / f"{n}.json" for n in ("results", "ranking", "sensitivity")}
    missing = [n for n, p in files.items() if not p.exists()]
    if missing:
        print(f"superiority: missing {', '.join(missing)} (run consolidate, rank and sensitivity first)", file=sys.stderr)
        return EXIT_MISSING
    results, ranking, sens = (read_json(files[n]) for n in ("results", "ranking", "sensitivity"))
    tgts = [args.target] if args.target else sorted(m for m, e in results.items() if e.get("role") == "target")
    if args.target and args.target not in results:
        print(f"superiority: {args.target} is not in results.json", file=sys.stderr)
        return EXIT_USAGE
    out = {t: evaluate(results, ranking, sens, t, args.interpretation) for t in tgts}
    write_json(rd / "superiority.json", out)
    for t, r in out.items():
        print(f"superiority: {t}: {r['verdict']}" + (f" ({r['reason']})" if r.get("reason") else
                                                     f"; failed {r['failed']}" if r["failed"] else ""))
    return EXIT_OK
