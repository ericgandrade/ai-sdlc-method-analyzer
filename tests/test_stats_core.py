"""Core stats goldens needed by the baseline port (the full suite is Task 2.x)."""
import math
from engine import stats

def test_alpha_fixtures():
    assert abs(stats.alpha_ordinal([(1,1),(2,2),(3,3),(4,4),(5,5),(1,2),(2,3),(4,4)]) - 0.9294) < 1e-4
    assert abs(stats.alpha_ordinal([(0,1),(1,1),(2,3),(3,3),(4,5),(5,5)]) - 0.9197) < 1e-4

def test_alpha_general_three_coders_missing():
    u = [[1,1,None],[2,3,2],[3,3,3],[4,None,5],[0,1,1],[5,5,4],[2,2,None]]
    assert abs(stats.alpha_ordinal_general(u) - 0.9297) < 1e-4

def test_u_rules():
    assert stats.criterion_u(["H", "M"], [3, 4]) == 0.5
    assert stats.criterion_u(["H", "H"], [2, 4]) == 1.0
    assert abs(stats.criterion_u(["M"], [3], r=0.8, design=4) - math.sqrt(0.25 + 0.16)) < 1e-12

def test_margin_and_bounds():
    assert stats.margin(3.1, 3.6) == 9.5 and stats.margin(1, 1) == 5.0
    assert stats.total([0]*16, [6.25]*16) == 0.0 and stats.total([5]*16, [6.25]*16) == 100.0
