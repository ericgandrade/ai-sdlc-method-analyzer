"""rank (plan §7.10; Task 2.11)."""
import copy
import pathlib

import pytest

from engine import consolidate as cons
from engine import rank as rk
from engine.jsonio import read_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
MEDIAN = [3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 4, 3, 3, 2]
BEST = [5, 4, 5, 5, 4, 4, 3, 4, 3, 4, 3, 3, 5, 4, 5, 3]
ORDER = ["ai-dlc", "agile-v", "bmad", "addyosmani", "superpowers", "kiro", "mattpocock", "spec-kit", "openspec"]


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    import os
    os.chdir(ROOT)
    return cons.consolidate(out_dir=tmp_path_factory.mktemp("derived"))


def with_target(base, slug, scores, U=3.0, role="target", benchmark=False):
    res = copy.deepcopy(base)
    e = copy.deepcopy(base["openspec"])
    e.update(role=role, benchmark=benchmark, L1_scores=scores, L1=cons.totals(scores),
             U={p: U for p in e["U"]}, name=slug)
    res[slug] = e
    return res


def test_baseline_order_and_median_best(base):
    out = rk.rank(base)
    assert [r["slug"] for r in out["profiles"]["baseline"]] == ORDER
    assert out["median_refs"] == MEDIAN and out["best_refs"] == BEST


def test_additional_reference_changes_no_median_or_best(base):
    out0 = rk.rank(base)
    res = with_target(base, "extra-ref", [5] * 16, role="reference", benchmark=False)
    out1 = rk.rank(res)
    assert out1["median_refs"] == out0["median_refs"] and out1["best_refs"] == out0["best_refs"]
    assert out1["leaders_criterion"]["C1"]["leaders"] == out0["leaders_criterion"]["C1"]["leaders"]
    assert out1["profiles"]["baseline"][0]["slug"] == "extra-ref"      # ranked and profiled, not a benchmark
    for m in base:
        assert out1["weakest_vs_median"][m] == out0["weakest_vs_median"][m]


def test_tie_rule_under_equal_weights(base):
    out = rk.rank(base)
    assert out["leaders"]["equal"]["tied"] == ["agile-v", "ai-dlc"]
    # U[equal] from results.json (§7.6 U rule): ai-dlc 4.0 > agile-v 3.3, so ai-dlc gives the stricter margin.
    assert base["ai-dlc"]["U"]["equal"] > base["agile-v"]["U"]["equal"]
    assert out["leaders"]["equal"]["leader"] == "ai-dlc"
    assert out["margins_profiles"]["equal"]["agile-v"]["reading"] == "leader"


def test_tie_rule_picks_larger_u_then_slug():
    e = lambda U: {"L1": {"baseline": 50.0}, "U": {"baseline": U}}
    assert rk.leader_of({"b": e(3.0), "a": e(2.0)}, "baseline") == ("b", ["a", "b"])
    assert rk.leader_of({"b": e(2.0), "a": e(2.0)}, "baseline") == ("a", ["a", "b"])


def test_margin_reading_agile_v_is_technical_tie(base):
    m = rk.rank(base)["margins"]
    assert m["agile-v"] == {"delta": -1.6, "margin": 9.5, "reading": "technical-tie", "against": "ai-dlc"}
    assert m["ai-dlc"]["reading"] == "leader"
    assert m["openspec"]["reading"] == "below"


def test_autonomy_readings(base):
    a = rk.rank(base)["autonomy_safety"]
    assert a["ai-dlc"]["reading"] == "orchestrates with partial protection"
    assert a["agile-v"]["reading"] == "autonomy above protection"
    assert a["openspec"]["reading"] == "assisted"
    assert rk.autonomy_reading(4, 4) == "autonomous and protected"


def test_weakest_vs_median_tie_break(base):
    # three criteria at -1 vs median: C2 (w 8), C4 (w 9), C5 (w 8) and C3 (w 9); weight desc then order
    s = list(MEDIAN)
    for i in (1, 2, 3, 4):
        s[i] -= 1
    out = rk.rank(with_target(base, "x", s))
    w = out["weakest_vs_median"]["x"]
    assert [e["c"] for e in w] == ["C3", "C4", "C2"]
    assert w[0] == {"c": "C3", "s": 2, "median": 3, "best": 5, "leaders": ["addyosmani"]}


def test_docs_entries_are_not_ranked(base):
    res = with_target(base, "docsy", [2] * 16)
    res["docsy"]["range"] = {"floor": {}}
    out = rk.rank(res)
    assert "docsy" not in [r["slug"] for r in out["profiles"]["baseline"]] and out["not_ranked"] == ["docsy"]


def test_shipped_derived_ranking_is_current(base, tmp_path):
    shipped = ROOT / "baseline" / "rounds" / "2026-11" / "derived" / "ranking.json"
    from engine.jsonio import dumps
    assert dumps(rk.rank(read_json(shipped.parent / "results.json"))).encode() == shipped.read_bytes()
