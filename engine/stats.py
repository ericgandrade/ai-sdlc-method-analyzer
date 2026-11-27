"""Totals, uncertainty, margin and Krippendorff alpha (plan §7.3, numerically load-bearing)."""
import math
from .common import PROFILES, U_CONF, CONF_ORDER

def total(scores, weights):
    """T(m,P) = Σ w·s/5 on 0–100 (methodology §7.2); normalised so any weight vector summing ≠100 still maps to 0–100."""
    return round(sum(s * w for s, w in zip(scores, weights)) / 5 * (100 / sum(weights)), 1)

def criterion_u(confs, scores, r=1.0, design=None):
    """u(m,c) = max(u_conf(worst confidence), half pre-reconciliation range) (§7.3);
    design-only: sqrt(u² + ((1-r)·D/2)²) (§8.3)."""
    worst = max(confs, key=CONF_ORDER.index)
    u = max(U_CONF[worst], (max(scores) - min(scores)) / 2)
    if design is not None:
        u = math.sqrt(u ** 2 + ((1 - r) * design / 2) ** 2)
    return u

def total_u(u, weights):
    """U(m,P) = sqrt(Σ (w/5 · u)²), same normalisation as total()."""
    k = 100 / sum(weights)
    return round(math.sqrt(sum((w * k / 5 * x) ** 2 for w, x in zip(weights, u))), 1)

def margin(u_x, u_b):
    """M(P) = max(5.0, 2·sqrt(U_x² + U_b²)) (methodology §9, S1)."""
    return round(max(5.0, 2 * math.sqrt(u_x ** 2 + u_b ** 2)), 1)

def alpha_ordinal(pairs):
    """Krippendorff's α, ordinal, 2 coders, no missing values. Kept as the fast path; must equal alpha_ordinal_general."""
    vals = [v for p in pairs for v in p]
    cats = sorted(set(vals))
    if len(cats) < 2:
        return 1.0
    n = {c: vals.count(c) for c in cats}
    def d2(a, b):
        lo, hi = min(a, b), max(a, b)
        s = sum(n[g] for g in cats if lo <= g <= hi) - (n[a] + n[b]) / 2
        return s * s
    do = sum(d2(a, b) for a, b in pairs) / len(pairs)
    N = len(vals)
    de = sum(n[a] * n[b] * d2(a, b) for a in cats for b in cats) / (N * (N - 1))
    return 1 - do / de

def alpha_ordinal_general(units):
    """Krippendorff's α, ordinal, any number of coders, missing values allowed.
    units = [[v or None, ...] per unit]. Coincidence-matrix form (Krippendorff 2004, ch. 11)."""
    from collections import defaultdict
    o = defaultdict(float)
    for u in units:
        vals = [v for v in u if v is not None]
        m = len(vals)
        if m < 2:
            continue                      # unpairable unit
        for i, a in enumerate(vals):
            for j, b in enumerate(vals):
                if i != j:
                    o[(a, b)] += 1 / (m - 1)
    cats = sorted({a for a, _ in o} | {b for _, b in o})
    n = {c: sum(o[(c, k)] for k in cats) for c in cats}
    N = sum(n.values())
    if len(cats) < 2:
        return 1.0
    def d2(a, b):
        lo, hi = min(a, b), max(a, b)
        s = sum(n[g] for g in cats if lo <= g <= hi) - (n[a] + n[b]) / 2
        return s * s
    do = sum(o[(a, b)] * d2(a, b) for a in cats for b in cats) / N
    de = sum(n[a] * n[b] * d2(a, b) for a in cats for b in cats) / (N * (N - 1))
    return 1 - do / de

def alpha_bootstrap(units, rng, draws=2000, level=0.90):
    """Seeded percentile bootstrap over units (cells). Returns (lo, hi)."""
    vals = sorted(alpha_ordinal_general([units[rng.randrange(len(units))] for _ in units]) for _ in range(draws))
    k = int((1 - level) / 2 * draws)
    return round(vals[k], 3), round(vals[draws - 1 - k], 3)
