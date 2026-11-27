"""Harvey-ball sprite, balls and the ±U band (plan §8.3; the geometry is load-bearing)."""
import math


def _pie(frac):
    if frac <= 0:
        return ""
    if frac >= 1:
        return '<circle cx="8" cy="8" r="6.2" fill="currentColor"/>'
    a = 2 * math.pi * frac
    x, y = 8 + 6.2 * math.sin(a), 8 - 6.2 * math.cos(a)
    large = 1 if frac > 0.5 else 0
    return f'<path d="M8 8 L8 1.8 A6.2 6.2 0 {large} 1 {x:.2f} {y:.2f} Z" fill="currentColor"/>'


def svg_defs():
    sym = []
    for pref, n in (("c", 5), ("f", 2), ("g", 4)):      # criteria 0–5, features 0–2, groups 5 bands
        for k in range(n + 1):
            sym.append(f'<symbol id="{pref}{k}" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.6" fill="none" '
                       f'stroke="currentColor" stroke-width="1.2"/>{_pie(k / n)}</symbol>')
    return '<svg width="0" height="0" class="defs" aria-hidden="true">' + "".join(sym) + "</svg>"


def ball(pref, k, label):
    return f'<svg class="hb" viewBox="0 0 16 16" role="img" aria-label="{label}"><use href="#{pref}{k}"/></svg>'


def group_band(p):   # percent → 0..4
    return 0 if p <= 12 else 1 if p <= 37 else 2 if p <= 62 else 3 if p <= 87 else 4


def band(t, u, width=240):
    x = lambda v: round(max(0, min(100, v)) / 100 * width, 1)
    return (f'<svg class="band" viewBox="0 0 {width} 12" role="img" aria-label="{t:.1f} ± {u:.1f}">'
            f'<line class="axis" x1="0" y1="6" x2="{width}" y2="6"/>'
            f'<rect class="u" x="{x(t-u)}" y="3" width="{round(x(t+u)-x(t-u),1)}" height="6"/>'
            f'<line class="t" x1="{x(t)}" y1="1" x2="{x(t)}" y2="11"/></svg>')
