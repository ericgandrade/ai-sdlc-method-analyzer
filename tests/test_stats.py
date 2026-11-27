"""Totals, uncertainty, margin and Krippendorff alpha (plan §7.3 golden table; Task 2.3)."""
import json
import math
import pathlib
import random

import pytest

from engine import baseline, stats
from engine.common import PROFILES

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORDER = ["baseline", "equal", "startup", "regulated", "autonomous"]
A1 = {
    "ai-dlc": [2, 4, 3, 5, 4, 4, 3, 4, 3, 3, 2, 3, 5, 3, 2, 3],
    "agile-v": [3, 2, 3, 5, 4, 4, 3, 2, 3, 4, 3, 2, 4, 4, 5, 2],
    "bmad": [5, 4, 3, 4, 4, 4, 3, 3, 3, 3, 2, 2, 4, 3, 2, 3],
    "addyosmani": [2, 3, 5, 3, 3, 2, 2, 2, 2, 2, 3, 3, 5, 3, 4, 0],
    "superpowers": [2, 2, 4, 4, 4, 4, 2, 3, 2, 2, 1, 0, 5, 2, 4, 2],
    "kiro": [4, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 1, 3, 3, 2, 2],
    "mattpocock": [2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 1, 1, 4, 3, 3, 2],
    "spec-kit": [4, 3, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1, 3, 2, 5, 0],
    "openspec": [3, 4, 3, 2, 2, 2, 2, 0, 1, 2, 1, 1, 2, 2, 2, 0],
}
A2 = {  # Appendix A.2
    "ai-dlc": [68.6, 66.2, 67.4, 68.4, 72.0],
    "agile-v": [67.0, 66.2, 68.0, 65.6, 67.4],
    "bmad": [66.8, 65.0, 68.8, 65.2, 67.8],
    "addyosmani": [57.6, 55.0, 60.2, 54.6, 57.2],
    "superpowers": [56.0, 53.8, 58.4, 51.0, 60.2],
    "kiro": [44.4, 45.0, 48.2, 41.6, 45.2],
    "mattpocock": [43.8, 43.8, 46.6, 40.4, 44.6],
    "spec-kit": [43.2, 43.8, 48.2, 39.6, 43.2],
    "openspec": [38.8, 36.2, 40.6, 37.2, 36.8],
}
F1 = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (1, 2), (2, 3), (4, 4)]
F2 = [(0, 1), (1, 1), (2, 3), (3, 3), (4, 5), (5, 5)]
ROUNDS = baseline.rounds(ROOT)


def baseline_pairs(r):
    """The 144 pre-reconciliation pairs, read from the shipped scorecards (9 methods x 16)."""
    d = baseline.round_dir(ROOT, r) / "scorecards"
    pairs = []
    for slug_dir in sorted(p for p in d.iterdir() if p.is_dir()):
        cards = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(slug_dir.glob("S-*.json"))]
        assert len(cards) == 2
        for i in range(1, 17):
            pairs.append(tuple(c["scores"][f"C{i}"]["s"] for c in cards))
    return pairs


@pytest.mark.parametrize("slug", sorted(A2))
def test_total_baseline_refs(slug):
    assert [stats.total(A1[slug], PROFILES[p]) for p in ORDER] == A2[slug]


def test_total_bounds():
    for w in PROFILES.values():
        assert stats.total([0] * 16, w) == 0.0
        assert stats.total([5] * 16, w) == 100.0


def test_margin():
    assert stats.margin(3.1, 3.6) == 9.5
    assert stats.margin(1, 1) == 5.0


def test_alpha_fixture_1():
    assert abs(stats.alpha_ordinal(F1) - 0.9294) < 1e-4


def test_alpha_fixture_2():
    assert abs(stats.alpha_ordinal(F2) - 0.9197) < 1e-4


@pytest.mark.skipif(not ROUNDS, reason="no baseline round")
@pytest.mark.parametrize("r", ROUNDS)
def test_alpha_baseline_round(r):
    pairs = baseline_pairs(r)
    assert len(pairs) == 144
    assert abs(stats.alpha_ordinal(pairs) - 0.857) < 5e-4


def test_alpha_perfect():
    assert stats.alpha_ordinal([(2, 2), (3, 3), (4, 4)]) == 1.0
    assert stats.alpha_ordinal_general([[1, 1, 1], [3, 3, None]]) == 1.0


def test_u_rules():
    assert stats.criterion_u(["H", "M"], [3, 4]) == 0.5
    assert stats.criterion_u(["H", "H"], [2, 4]) == 1.0
    assert abs(stats.criterion_u(["M"], [3], r=0.8, design=4) - math.sqrt(0.25 + 0.16)) < 1e-12
    assert abs(math.sqrt(0.25 + 0.16) - 0.6403) < 1e-4


@pytest.mark.skipif(not ROUNDS, reason="no baseline round")
def test_alpha_general_equals_two_coder():
    for pairs in (F1, F2, baseline_pairs(ROUNDS[-1])):
        g = stats.alpha_ordinal_general([list(p) for p in pairs])
        assert abs(g - stats.alpha_ordinal(pairs)) < 1e-12


def test_alpha_general_three_coders_missing():
    u = [[1, 1, None], [2, 3, 2], [3, 3, 3], [4, None, 5], [0, 1, 1], [5, 5, 4], [2, 2, None]]
    assert abs(stats.alpha_ordinal_general(u) - 0.9297) < 1e-4


@pytest.mark.skipif(not ROUNDS, reason="no baseline round")
def test_alpha_bootstrap():
    units = [list(p) for p in baseline_pairs(ROUNDS[-1])]
    lo, hi = stats.alpha_bootstrap(units, random.Random(1))
    assert lo <= 0.857 <= hi
    assert (lo, hi) == stats.alpha_bootstrap(units, random.Random(1))


def test_total_u_matches_recorded_where_reproducible():
    # U recomputed from per-criterion u reproduces the recorded value for 6 of 9 (plan §7.6)
    l1 = json.loads((baseline.round_dir(ROOT) / "l1.json").read_text(encoding="utf-8"))
    same = [s for s, v in l1.items() if stats.total_u(v["u"], PROFILES["baseline"]) == v["U_recorded"]]
    assert sorted(set(l1) - set(same)) == ["ai-dlc", "bmad", "openspec"]
