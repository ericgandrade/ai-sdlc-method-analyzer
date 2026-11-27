"""`rank` (plan §7.10, stage S12): ranking.json from results.json.

- Medians and best values are computed over the frozen benchmark set only (`role == reference`
  and `benchmark == true`), never over targets or additional references.
- Documentation-only entries (`range` set) are never ranked as a point (protocol §6).
- Ties: every leader with an equal total is listed in slug order. For a margin against "the"
  leader, the tied leader with the larger `U[profile]` (results.json, §7.6) is used, which gives
  the stricter margin; slug order breaks any remaining tie. The same key is used by `superiority`.
"""
import pathlib
import statistics
import sys

from . import stats
from .common import CRITERIA, EXIT_MISSING, EXIT_OK, EXIT_USAGE, GROUPS, PROFILES
from .jsonio import read_json, write_json


def points(results):
    """Entries that can be ranked as a point."""
    return {k: v for k, v in results.items() if not v.get("range")}


def benchmark(results):
    return {k: v for k, v in results.items() if v.get("role") == "reference" and v.get("benchmark")}


def targets(results):
    return {k: v for k, v in results.items() if v.get("role") == "target" and not v.get("range")}


def competition_ranks(scores):
    """{m: total} -> {m: 1 + number of strictly higher totals}."""
    return {m: 1 + sum(1 for x in scores.values() if x > t) for m, t in scores.items()}


def ordered(scores):
    return sorted(scores, key=lambda m: (-scores[m], m))


def leader_of(entries, profile):
    """(leader, tied leaders): the tied leader with the larger U[profile], then slug order."""
    top = max(e["L1"][profile] for e in entries.values())
    tied = sorted(m for m, e in entries.items() if e["L1"][profile] == top)
    chosen = sorted(tied, key=lambda m: (-entries[m]["U"][profile], m))[0]
    return chosen, tied


def margins(entries, profile):
    lead, tied = leader_of(entries, profile)
    L = entries[lead]
    out = {}
    for m, e in sorted(entries.items()):
        delta = round(e["L1"][profile] - L["L1"][profile], 1)
        M = stats.margin(e["U"][profile], L["U"][profile])
        reading = "leader" if m in tied else "technical-tie" if abs(delta) < M else "below"
        out[m] = {"delta": delta, "margin": M, "reading": reading, "against": lead}
    return lead, tied, out


def ref_vectors(results):
    b = benchmark(results)
    med = [statistics.median(b[m]["L1_scores"][i] for m in b) for i in range(16)] if b else []
    best = [max(b[m]["L1_scores"][i] for m in b) for i in range(16)] if b else []
    return med, best


def autonomy_reading(a, c8):
    if a is None or c8 is None:
        return "not assessed"
    if a >= 4 and c8 >= 4:
        return "autonomous and protected"
    if a >= 3 and c8 <= 2:
        return "autonomy above protection"
    if a >= 3:
        return "orchestrates with partial protection"
    return "assisted"


def weakest_vs_median(s, med, best, leaders):
    w = PROFILES["baseline"]
    order = sorted(range(16), key=lambda i: (s[i] - med[i], -w[i], i))[:3]
    return [{"c": CRITERIA[i], "s": s[i], "median": med[i], "best": best[i], "leaders": leaders[CRITERIA[i]]}
            for i in order]


def rank(results):
    pts = points(results)
    bench = benchmark(results)
    med, best = ref_vectors(results)
    out = {"profiles": {}, "leaders": {}, "margins_profiles": {}, "median_refs": med, "best_refs": best,
           "benchmark_set": sorted(bench), "not_ranked": sorted(set(results) - set(pts))}
    for p in PROFILES:
        tot = {m: e["L1"][p] for m, e in pts.items()}
        rk = competition_ranks(tot)
        out["profiles"][p] = [{"slug": m, "total": tot[m], "U": pts[m]["U"][p], "rank": rk[m]} for m in ordered(tot)]
        lead, tied, mg = margins(pts, p)
        out["leaders"][p] = {"leader": lead, "tied": tied}
        out["margins_profiles"][p] = mg
    out["margins"] = out["margins_profiles"]["baseline"]
    lc = {}
    for i, c in enumerate(CRITERIA):
        lc[c] = {"max": best[i], "leaders": sorted(m for m in bench if bench[m]["L1_scores"][i] == best[i]),
                 "median_refs": med[i],
                 "target": {m: e["L1_scores"][i] for m, e in sorted(targets(results).items())}}
    out["leaders_criterion"] = lc
    lg = {}
    for g in GROUPS:
        vals = {m: e["L4_groups"][g] for m, e in bench.items() if e.get("L4_groups")}
        top = max(vals.values()) if vals else None
        lg[g] = {"max": top, "leaders": sorted(m for m, v in vals.items() if v == top),
                 "median_refs": statistics.median(vals.values()) if vals else None,
                 "target": {m: (e.get("L4_groups") or {}).get(g) for m, e in sorted(targets(results).items())}}
    out["leaders_group"] = lg
    out["autonomy_safety"] = {m: {"L3": e.get("L3"), "C8": e.get("C8"), "L1": e["L1"]["baseline"],
                                  "reading": autonomy_reading(e.get("L3_num"), e.get("C8"))}
                              for m, e in sorted(pts.items())}
    leaders = {c: lc[c]["leaders"] for c in CRITERIA}
    out["weakest_vs_median"] = {m: weakest_vs_median(e["L1_scores"], med, best, leaders)
                                for m, e in sorted(pts.items())} if med else {}
    return out


def configure(p):
    p.add_argument("--run", default=None)
    p.add_argument("--results", default=None, help="results.json to read (without --run)")
    p.add_argument("--out", default=None, help="directory for ranking.json (without --run)")


def io_paths(args, name):
    from . import state
    if args.run:
        d = state.run_path(args.run)
        return d / "results.json", d / name
    if not args.results or not args.out:
        return None, None
    return pathlib.Path(args.results), pathlib.Path(args.out) / name


def run(args):
    src, dest = io_paths(args, "ranking.json")
    if src is None:
        print("rank: --run, or --results with --out, is required", file=sys.stderr)
        return EXIT_USAGE
    if not src.exists():
        print("rank: results.json missing (run consolidate first)", file=sys.stderr)
        return EXIT_MISSING
    out = rank(read_json(src))
    write_json(dest, out)
    print("rank: baseline order " + " > ".join(r["slug"] for r in out["profiles"]["baseline"]))
    return EXIT_OK
