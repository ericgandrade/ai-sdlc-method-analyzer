"""Reconciliation support, calibration, reliability and red-team scope (plan §7.7, protocol §2–§5).

Commands: `reconcile pre|blind`, `calibration`, `alpha`, `audit-scope`. All read the active
scorer instances from state.json (#93): a replacement is used instead of the instance it
replaced, and a third scorer is added.
"""
import math
import random
import sys

from . import baseline, paths, state, stats
from .common import CONF_ORDER, CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK, PROFILES
from .jsonio import read_json, write_json
from .scorecard import ScorecardError, extract

ALPHA_GATE = 0.667
AGREEMENT_MIN = 0.5
SAMPLE_SHARE = 0.15


class ReconcileError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def _cards(st, name):
    """{instance: card} for every active instance that has sealed/<inst>/<name>."""
    rd = state.run_path(st["run_id"])
    out = {}
    for inst in state.active_instances(st):
        p = rd / "sealed" / inst / name
        if p.exists():
            out[inst] = extract(p)
    return out


def _design(st):
    return (st.get("target") or {}).get("status") == "design-only"


# ------------------------------------------------------------------ reconcile pre / blind

def pre(run_id):
    st = state.load(run_id)
    cards = _cards(st, "target.md")
    base = [i for i in state.active_instances(st)[:2]]
    if any(i not in cards for i in base):
        raise ReconcileError(f"target scorecards missing for {[i for i in base if i not in cards]}", EXIT_MISSING)
    design = _design(st)
    cells = {}
    for c in CRITERIA:
        s = {i: cards[i]["scores"][c]["s"] for i in cards}
        confs = [cards[i]["scores"][c]["conf"] for i in cards]
        diff = max(s.values()) - min(s.values())
        proposal = "equal" if diff == 0 else "lower" if diff == 1 else "needs-written"
        cell = {"scores": s, "diff": diff, "proposal": proposal,
                "proposed": min(s.values()) if diff <= 1 else None,
                "conf_worst": max(confs, key=CONF_ORDER.index)}
        if design:
            r = {i: cards[i]["scores"][c].get("r", 1.0) for i in cards}
            cell.update(r=r, r_proposal="lower", r_proposed=min(r.values()))
        cells[c] = cell
    out = {"instances": sorted(cards), "design_only": design, "cells": cells,
           "needs_written": [c for c in CRITERIA if cells[c]["proposal"] == "needs-written"]}
    write_json(state.run_path(run_id) / "reconcile-pre.json", out)
    return out


def blind(run_id):
    rd = state.run_path(run_id)
    if not (rd / "reconciled.json").exists():
        raise ReconcileError("reconciled.json missing", EXIT_MISSING)
    rec = read_json(rd / "reconciled.json")
    out = {k: v for k, v in rec.items() if k not in ("r", "ra")}
    out["cells"] = {c: {k: v for k, v in cell.items() if k not in ("r", "r_rule", "ra")}
                    for c, cell in rec.get("cells", {}).items()}
    write_json(rd / "reconciled-blind.json", out)
    return out


# ------------------------------------------------------------------ calibration (protocol §2)

def _agreement(a, b):
    return round(sum(1 for x, y in zip(a, b) if x == y) / len(a), 4)


def calibration(run_id, root=None):
    st = state.load(run_id)
    root = root or paths.project_root()
    rnd = st["round_id"].split("+", 1)[-1]
    l1 = read_json(baseline.round_dir(root, rnd) / "l1.json")
    w = PROFILES["baseline"]
    out, any_drift = {"refs": {}}, False
    for ref in st["cal_refs"]:
        if ref not in l1:
            raise ReconcileError(f"{ref} is not in the baseline l1.json", EXIT_MISSING)
        b = l1[ref]
        recon_total = stats.total(b["scores"], w)
        raws = [[p[k] for p in b["pairs"]] for k in range(2)]
        raw_totals = [stats.total(r, w) for r in raws]
        raw_mean = sum(raw_totals) / len(raw_totals)
        thr = b["U_recorded"]
        per, ref_drift = {}, False
        cards = _cards(st, f"cal-{ref}.md")
        if not cards:
            raise ReconcileError(f"no calibration scorecard for {ref}", EXIT_MISSING)
        for inst, card in sorted(cards.items()):
            v = [card["scores"][c]["s"] for c in CRITERIA]
            t = stats.total(v, w)
            d_rec, d_raw = round(t - recon_total, 1), round(t - raw_mean, 1)
            a_rec = _agreement(v, b["scores"])
            a_raw = round(sum(_agreement(v, r) for r in raws) / len(raws), 4)
            drift = abs(d_raw) > thr or abs(d_rec) > thr or a_rec < AGREEMENT_MIN or a_raw < AGREEMENT_MIN
            model = st["stages"].get(f"S04:{inst}", {}).get("model")
            per[inst] = {"total": t, "delta_reconciled": d_rec, "delta_raw": d_raw, "agreement_exact_reconciled": a_rec,
                         "agreement_exact_raw": a_raw, "model": model, "drift": drift}
            ref_drift = ref_drift or drift
        out["refs"][ref] = {"reconciled_total": recon_total, "raw_totals": raw_totals, "per_scorer": per,
                            "threshold": thr, "drift": ref_drift}
        any_drift = any_drift or ref_drift
    out["drift"] = any_drift
    write_json(state.run_path(run_id) / "calibration.json", out)
    if any_drift and st["comparison"] != "cross-round":
        st["comparison"] = "cross-round"
        state.save(st)
    return out


def comparison(run_id):
    """Protocol §9: same-round only when the reproduction record passes (set at init) and this
    run's own calibration shows no drift."""
    st = state.load(run_id)
    p = state.run_path(run_id) / "calibration.json"
    if st["comparison"] == "cross-round" or not p.exists() or read_json(p).get("drift"):
        return "cross-round"
    return "same-round"


# ------------------------------------------------------------------ alpha (protocol §3, §4)

def units_for(st):
    """Pre-reconciliation ratings of the target plus the calibration reference(s), one unit per cell."""
    insts = state.active_instances(st)
    units = []
    for name in ["target.md"] + [f"cal-{r}.md" for r in st["cal_refs"]]:
        cards = _cards(st, name)
        if not cards:
            continue
        for c in CRITERIA:
            units.append([cards[i]["scores"][c]["s"] if i in cards and c in cards[i]["scores"] else None
                          for i in insts])
    return units, len(insts)


def alpha(run_id, pairs_file=None):
    st = state.load(run_id)
    if pairs_file:
        units = [list(p) for p in read_json(pairs_file)]
        coders = max(len(u) for u in units)
    else:
        units, coders = units_for(st)
    if not units:
        raise ReconcileError("no scorecards to compute alpha over", EXIT_MISSING)
    a = round(stats.alpha_ordinal_general(units), 4)
    lo, hi = stats.alpha_bootstrap(units, random.Random(st["seed"]))
    out = {"alpha": a, "units": len(units), "coders": coders, "ci90": [lo, hi], "small_set": len(units) < 64,
           "gate": a >= ALPHA_GATE, "instances": state.active_instances(st), "seed": st["seed"]}
    write_json(state.run_path(run_id) / "alpha.json", out)
    return out


# ------------------------------------------------------------------ audit scope (protocol §5)

def _rank(total_x, others):
    return 1 + sum(1 for t in others if t > total_x)


def audit_scope(run_id, root=None):
    from .registry import benchmark_slugs, load_registry
    st = state.load(run_id)
    root = root or paths.project_root()
    rd = state.run_path(run_id)
    if not (rd / "reconciled.json").exists():
        raise ReconcileError("reconciled.json missing", EXIT_MISSING)
    rec = read_json(rd / "reconciled.json")
    vec = rec.get("ra") if _design(st) and rec.get("ra") else rec["vector"]
    rnd = st["round_id"].split("+", 1)[-1]
    l1 = read_json(baseline.round_dir(root, rnd) / "l1.json")
    w = PROFILES["baseline"]
    bench = [stats.total(l1[s]["scores"], w) for s in benchmark_slugs(load_registry(root)) if s in l1]
    t = stats.total(vec, w)
    reasons = {c: [] for c in CRITERIA}
    full = False
    if _design(st):
        full, why = True, "design-only target: full audit (methodology 10.3)"
    elif _rank(t, bench) <= 2:
        full, why = True, "top two under baseline among the 9 benchmarks plus the target (methodology 10.3)"
    if full:
        for c in CRITERIA:
            reasons[c].append(why)
        out = {"cells": list(CRITERIA), "full": True, "reasons": reasons, "seed": st["audit_seed"], "sample": []}
        write_json(rd / "audit_scope.json", out)
        return out
    base_rank = _rank(t, bench)
    for i, c in enumerate(CRITERIA):
        s = rec["vector"][i]
        conf = (rec.get("cells") or {}).get(c, {}).get("conf")
        if s >= 4:
            reasons[c].append("score 4 or 5")
        if conf == "L":
            reasons[c].append("Low confidence")
        for d in (-1, 1):
            v = list(vec)
            v[i] = min(5, max(0, v[i] + d))
            if _rank(stats.total(v, w), bench) != base_rank:
                reasons[c].append(f"a {'+' if d > 0 else '-'}1 change moves the rank")
                break
    chosen = [c for c in CRITERIA if reasons[c]]
    rest = [c for c in CRITERIA if not reasons[c]]
    k = math.ceil(SAMPLE_SHARE * len(rest))
    sample = sorted(random.Random(st["audit_seed"]).sample(rest, k), key=CRITERIA.index) if rest else []
    for c in sample:
        reasons[c].append("seeded 15% sample")
    out = {"cells": sorted(chosen + sample, key=CRITERIA.index), "full": False,
           "reasons": {c: r for c, r in reasons.items() if r}, "seed": st["audit_seed"], "sample": sample}
    write_json(rd / "audit_scope.json", out)
    return out


# ------------------------------------------------------------------ CLI

def configure_reconcile(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    for n in ("pre", "blind"):
        q = sub.add_parser(n)
        q.add_argument("--run", required=True)


def _wrap(name, fn):
    try:
        out = fn()
    except (ReconcileError, ScorecardError, state.StateError, paths.PathError) as e:
        print(f"{name}: {e}", file=sys.stderr)
        return e.code, None
    return EXIT_OK, out


def run_reconcile(args):
    code, out = _wrap(f"reconcile {args.action}", lambda: (pre if args.action == "pre" else blind)(args.run))
    if out is not None:
        extra = f"; {len(out['needs_written'])} cell(s) need a written reconciliation" if args.action == "pre" else ""
        print(f"reconcile {args.action}: written{extra}")
    return code


def configure_run(p):
    p.add_argument("--run", required=True)


def configure_alpha(p):
    p.add_argument("--run", required=True)
    p.add_argument("--pairs", default=None)


def run_calibration(args):
    code, out = _wrap("calibration", lambda: calibration(args.run))
    if out is not None:
        print("calibration: " + ("DRIFT (warning, gate G2; the run is cross-round)" if out["drift"] else "no drift"))
    return code


def run_alpha(args):
    code, out = _wrap("alpha", lambda: alpha(args.run, args.pairs))
    if out is None:
        return code
    print(f"alpha: {out['alpha']} over {out['units']} units, {out['coders']} coders, ci90 {out['ci90']}"
          + (" (small set)" if out["small_set"] else ""))
    return EXIT_OK if out["gate"] else EXIT_GATE


def run_audit_scope(args):
    code, out = _wrap("audit-scope", lambda: audit_scope(args.run))
    if out is not None:
        print(f"audit-scope: {len(out['cells'])} cell(s){' (full audit)' if out['full'] else ''}")
    return code
