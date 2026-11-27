"""`sensitivity` (plan §7.11, methodology §5.4, stage S12): profiles, tornado, leave-one-out and P(first).

The samplers follow the methodology, not the prototype shortcut (centred Dirichlet 0.8·w, Gaussian
noise, u = U/3 for the other methods):
- centred: Dirichlet with α_c = 0.5·w_c (Σα = 50), scores fixed;
- uniform: Dirichlet with α_c = 1, scores fixed;
- score_perturbation: baseline weights, every score drawn uniformly within ±u of that method's own
  per-criterion u (results.json), clipped to [0, 5].
Ties for first share the win equally (1/k each).

Determinism: every sampler of every analysis uses a fresh `random.Random(seed)` and the methods in
slug order, so `verdict_set[X]` (#47: the 9 benchmarks plus X only) is byte-identical whatever else
the display set contains.
"""
import random
import sys

from .common import CRITERIA, EXIT_MISSING, EXIT_OK, EXIT_USAGE, PROFILES
from .jsonio import read_json, write_json
from .rank import benchmark, competition_ranks, io_paths, points, targets
from .stats import total

DEFAULT_DRAWS = 10000
LOO_RULE = "x counts as first in a leave-one-out run only when its total is strictly above every other total"


def dirichlet(rng, alphas):
    g = [rng.gammavariate(a, 1.0) for a in alphas]
    s = sum(g)
    return [x / s * 100 for x in g]


def rank_first_prob(vectors, draw_weights, draw_scores, n, rng):
    """vectors: {slug: [16]}. Ties share the win equally (1/k each)."""
    wins = {m: 0.0 for m in vectors}
    ranks = {m: 0.0 for m in vectors}
    for _ in range(n):
        w = draw_weights(rng)
        sc = {m: total(draw_scores(rng, m, v), w) for m, v in vectors.items()}
        top = max(sc.values())
        leaders = [m for m in sc if sc[m] == top]
        for m in leaders:
            wins[m] += 1 / len(leaders)
        order = sorted(sc, key=lambda m: -sc[m])
        for i, m in enumerate(order):
            ranks[m] += i + 1
    return {m: round(wins[m] / n, 3) for m in vectors}, {m: round(ranks[m] / n, 2) for m in vectors}


BASE = PROFILES["baseline"]


def centred(rng):
    return dirichlet(rng, [0.5 * w for w in BASE])          # α_c = 0.5·w_c, Σα = 50


def uniform(rng):
    return dirichlet(rng, [1.0] * 16)                        # α_c = 1


def fixed_w(rng):
    return BASE


def same_scores(rng, m, v):
    return v


def perturbed(u_by_method):
    # §5.4 item 5: uniform within ±u, clipped to [0, 5] (clipping documented)
    return lambda rng, m, v: [min(5, max(0, s + rng.uniform(-u, u))) for s, u in zip(v, u_by_method[m])]


def _ranks(vectors, w):
    return competition_ranks({m: total(v, w) for m, v in vectors.items()})


def tornado(vectors):
    base = _ranks(vectors, BASE)
    rows = []
    for i, c in enumerate(CRITERIA):
        for f in (0.5, 1.5):
            w = list(BASE)
            w[i] *= f
            s = sum(w)
            w = [x * 100 / s for x in w]
            r = _ranks(vectors, w)
            rows.append({"c": c, "factor": f, "ranks": r, "changes": {m: r[m] - base[m] for m in sorted(r)}})
    return rows


def loo(vectors):
    rows = []
    for i, c in enumerate(CRITERIA):
        w = list(BASE)
        w[i] = 0
        tot = {m: total(v, w) for m, v in vectors.items()}
        top = max(tot.values())
        rows.append({"c": c, "totals": tot, "ranks": competition_ranks(tot),
                     "first": sorted(m for m in tot if tot[m] == top)})
    return rows


def p_first(vectors, u_by, seed, draws):
    out, mean = {}, {}
    for name, dw, ds in (("centred", centred, same_scores), ("uniform", uniform, same_scores),
                         ("score_perturbation", fixed_w, perturbed(u_by))):
        out[name], mean[name] = rank_first_prob(vectors, dw, ds, draws, random.Random(seed))
    return out, mean


def _vectors(entries):
    return ({m: entries[m]["L1_scores"] for m in sorted(entries)}, {m: entries[m]["u"] for m in sorted(entries)})


def verdict_set(results, x, seed, draws):
    members = dict(benchmark(results))
    members[x] = results[x]
    vec, u = _vectors(members)
    pf, mean = p_first(vec, u, seed, draws)
    rows = loo(vec)
    first = sum(1 for r in rows if r["first"] == [x])
    return {"members": sorted(members), "p_first": {k: v[x] for k, v in pf.items()},
            "p_first_all": pf, "mean_rank": mean, "loo_first_count": first, "loo_rule": LOO_RULE}


def sensitivity(results, seed, draws=DEFAULT_DRAWS):
    pts = points(results)
    vec, u = _vectors(pts)
    prof = {}
    for p, w in PROFILES.items():
        tot = {m: total(v, w) for m, v in vec.items()}
        rk = competition_ranks(tot)
        prof[p] = {m: {"total": tot[m], "rank": rk[m]} for m in sorted(tot)}
    pf, mean = p_first(vec, u, seed, draws)
    return {"seed": seed, "draws": draws, "profiles": prof, "tornado": tornado(vec), "loo": loo(vec),
            "p_first": pf, "mean_rank": mean, "loo_rule": LOO_RULE,
            "samplers": {"centred": "Dirichlet alpha_c = 0.5 w_c (sum 50), scores fixed",
                         "uniform": "Dirichlet alpha_c = 1, scores fixed",
                         "score_perturbation": "baseline weights; s + U(-u, u) per criterion with each method's u, "
                                               "clipped to [0, 5]"},
            "verdict_set": {x: verdict_set(results, x, seed, draws) for x in sorted(targets(results))}}


def configure(p):
    p.add_argument("--run", default=None)
    p.add_argument("--results", default=None, help="results.json to read (without --run)")
    p.add_argument("--out", default=None, help="directory for sensitivity.json (without --run)")
    p.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    p.add_argument("--seed", type=int, default=None, help="default: the run's seed (required without --run)")


def run(args):
    from . import state
    src, dest = io_paths(args, "sensitivity.json")
    if src is None:
        print("sensitivity: --run, or --results with --out, is required", file=sys.stderr)
        return EXIT_USAGE
    seed = args.seed
    if seed is None:
        if not args.run:
            print("sensitivity: --seed is required without --run", file=sys.stderr)
            return EXIT_USAGE
        seed = state.load(args.run)["seed"]
    if not src.exists():
        print("sensitivity: results.json missing (run consolidate first)", file=sys.stderr)
        return EXIT_MISSING
    out = sensitivity(read_json(src), seed, args.draws)
    write_json(dest, out)
    top = sorted(out["p_first"]["centred"].items(), key=lambda kv: -kv[1])[:3]
    print(f"sensitivity: seed {seed}, {args.draws} draws; P(first) centred " + ", ".join(f"{m} {p}" for m, p in top))
    return EXIT_OK
