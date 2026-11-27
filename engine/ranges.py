"""`ranges` (plan §7.13, stage D3): floor, centre and ceiling of a documentation-only target.

Reads `docs-only.json` (§5.10) and writes `results.json[target].range` (through consolidate).
A single-assessor documentation-only run never enters a ranking as a point (protocol §6): its
position is shown per reading, against the 9 benchmark references only.
"""
import sys

from . import stats
from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK, EXIT_USAGE, LEVELS, PROFILES
from .jsonio import read_json

CAPS = {"closed": (4, "A3"), "open-unread": (3, "A2")}     # §5.10 type caps (score, L3)
U_DOCS = {"M": 0.5, "L": 1.0}


class RangesError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def cap_violations(docs):
    """Cells above the type cap (no cell may be 5: a 5 needs I evidence), and an L3 above its cap."""
    decl = docs.get("type_declaration")
    if decl not in CAPS:
        return [f"type_declaration must be one of {sorted(CAPS)}"]
    cap, l3cap = CAPS[decl]
    out = []
    for name in ("L1_floor", "L1_ceiling"):
        for c, s in zip(CRITERIA, docs[name]):
            if s > cap:
                out.append(f"{name} {c} = {s} > cap {cap}")
    for c, (f, h) in zip(CRITERIA, zip(docs["L1_floor"], docs["L1_ceiling"])):
        if f > h:
            out.append(f"{c}: floor {f} above ceiling {h}")
    l3 = docs.get("L3")
    if l3 in LEVELS and LEVELS.index(l3) > LEVELS.index(l3cap):
        out.append(f"L3 {l3} > cap {l3cap}")
    for c, conf in (docs.get("conf") or {}).items():
        if conf not in U_DOCS:
            out.append(f"conf {c} = {conf}: documentation-only confidence is M or L")
    return out


def _u(docs):
    conf = docs.get("conf") or {}
    return [U_DOCS.get(conf.get(c, "L"), 1.0) for c in CRITERIA]


def _benchmark_totals(root, round_id):
    from .consolidate import reference_entries
    return {k: v["L1"] for k, v in reference_entries(root, round_id).items() if v["benchmark"]}


def compute(docs, bench):
    """bench: {slug: {profile: total}} of the benchmark references."""
    u = _u(docs)
    U = {p: stats.total_u(u, w) for p, w in PROFILES.items()}
    floor = {p: stats.total(docs["L1_floor"], w) for p, w in PROFILES.items()}
    ceil = {p: stats.total(docs["L1_ceiling"], w) for p, w in PROFILES.items()}
    centre = {p: round((floor[p] + ceil[p]) / 2, 1) for p in PROFILES}

    def position(t):
        return {p: 1 + sum(1 for b in bench.values() if b[p] > t[p]) for p in PROFILES}

    def reading(scores, t):
        return {"scores": scores, "totals": t, "U": U, "position": position(t)}

    mid = [(a + b) / 2 for a, b in zip(docs["L1_floor"], docs["L1_ceiling"])]
    return {"floor": reading(list(docs["L1_floor"]), floor), "centre": reading(mid, centre),
            "ceiling": reading(list(docs["L1_ceiling"]), ceil), "against": sorted(bench),
            "type_declaration": docs.get("type_declaration")}, mid, u


def docs_entry_fields(rd, root, round_id, _decl=None):
    p = rd / "docs-only.json"
    if not p.exists():
        raise RangesError("docs-only.json missing", EXIT_MISSING)
    docs = read_json(p)
    bad = cap_violations(docs)
    if bad:
        raise RangesError("cap check failed: " + "; ".join(bad), EXIT_GATE)
    rng, mid, u = compute(docs, _benchmark_totals(root, round_id))
    lenses = {"L3": {"level": docs.get("L3"), "conf": "L"}, "L4": docs.get("L4"), "L2": None}
    return {"scores": mid, "u": u, "lenses": lenses, "range_": rng}


def configure(p):
    p.add_argument("--run", required=True)


def run(args):
    from . import state
    from .consolidate import ConsolidateError, consolidate
    try:
        if state.load(args.run)["mode"] != "docs":
            print("ranges: only a documentation-only (docs) run has ranges", file=sys.stderr)
            return EXIT_USAGE
        res = consolidate(args.run)
    except (RangesError, ConsolidateError, state.StateError) as e:
        print(f"ranges: {e}", file=sys.stderr)
        return e.code
    r = next(e["range"] for e in res.values() if e.get("run") == args.run)
    print(f"ranges: baseline floor {r['floor']['totals']['baseline']}, centre {r['centre']['totals']['baseline']}, "
          f"ceiling {r['ceiling']['totals']['baseline']}")
    return EXIT_OK
