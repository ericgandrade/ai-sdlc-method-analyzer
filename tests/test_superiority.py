"""superiority (plan §7.12; Task 2.13)."""
import copy
import pathlib

import pytest

from engine import consolidate as cons
from engine import rank as rk
from engine import sensitivity as sn
from engine.jsonio import read_json
from engine.superiority import SuperiorityError, check_refs, evaluate, superiority, verdict_refs

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "baseline" / "rounds" / "2026-11" / "derived"
P1 = {"centred": 1.0, "uniform": 1.0, "score_perturbation": 1.0}
PROFS = ("baseline", "equal", "startup", "regulated", "autonomous")


@pytest.fixture(scope="module")
def results():
    return read_json(DERIVED / "results.json")


@pytest.fixture(scope="module")
def refs(results):
    return verdict_refs(results)


def X(s, U=2.0, **over):
    u = {p: U for p in PROFS}
    u.update(over)
    return {"s": s, "U": u}


def test_superior(refs):
    r = superiority(X([5] * 16), refs, P1, 16, True, 0.9)
    assert r["verdict"] == "Superior" and r["failed"] == []
    assert r["S1"]["delta"] == round(100.0 - 68.6, 1)


def test_one_criterion_below_median_is_not_superior(refs):
    s = [5] * 16
    s[0] = 2                                           # C1 median 3
    r = superiority(X(s), refs, P1, 16, True, 0.9)
    assert r["verdict"] == "Not superior" and "S4" in r["failed"] and r["S4"]["below_median"] == ["C1"]


def test_within_margin_is_comparable(refs, results):
    s = list(results["bmad"]["L1_scores"])
    r = superiority(X(s, 2.7), refs, P1, 16, True, 0.9)
    assert r["verdict"] == "Comparable"


def test_prototype_regression_top_reference_is_comparable(refs, results):
    r = superiority(X(list(results["ai-dlc"]["L1_scores"]), 3.1), refs, P1, 16, True, 0.9)
    assert r["verdict"] == "Comparable"
    assert r["S1"]["delta"] == 0 and r["S1"]["M"] == 8.8


# Synthetic references for the interpretation cases: best = 2 and median = 1.5 everywhere.
SYN = {"r1": {"s": [2] * 16, "U": {p: 0.5 for p in PROFS}}, "r2": {"s": [1] * 16, "U": {p: 0.5 for p in PROFS}}}
# Five non-core criteria at 5 (best in class), the rest at the median: S1 and S4 pass, S5 fails.
S5_FAIL = [5 if c in (0, 6, 7, 8, 9) else 1.5 for c in range(16)]


def test_s2_fails_once_s3_passes_s5_fails():
    x = X(S5_FAIL, 0.5, regulated=10.0)                # one S2 failure through a wide margin
    strict = superiority(x, SYN, P1, 16, True, 0.9, "strict")
    literal = superiority(x, SYN, P1, 16, True, 0.9, "literal")
    assert strict["S2"]["failed"] == ["regulated"] and strict["S3"]["pass"] and not strict["S5"]["pass"]
    assert strict["verdict"] in ("Not superior", "Comparable")
    assert literal["verdict"] == "Conditionally superior"


def test_s2_fails_three_times_and_s3_short():
    x = X(S5_FAIL, 0.5, regulated=10.0, startup=10.0, autonomous=10.0)
    short = dict(P1, centred=0.5)
    strict = superiority(x, SYN, short, 16, True, 0.9, "strict")
    literal = superiority(x, SYN, short, 16, True, 0.9, "literal")
    assert len(strict["S2"]["failed"]) == 3 and not strict["S3"]["pass"]
    assert strict["verdict"] != "Conditionally superior"
    assert literal["verdict"] == "Conditionally superior"


def test_s5_alone_failing():
    x = X(S5_FAIL, 0.5)
    strict = superiority(x, SYN, P1, 16, True, 0.9, "strict")
    literal = superiority(x, SYN, P1, 16, True, 0.9, "literal")
    assert strict["failed"] == literal["failed"] == ["S5"]
    assert literal["verdict"] == "Conditionally superior"
    assert strict["verdict"] != "Conditionally superior"


def test_failed_lists_every_failed_condition(refs):
    r = superiority(X([0] * 16), refs, {"centred": 0, "uniform": 0, "score_perturbation": 0}, 0, False, 0.1)
    assert r["failed"] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]


def test_tie_under_equal_weights_uses_the_larger_u(refs):
    """ai-dlc and agile-v tie at 66.2 under equal weights; B(P) is the one with the larger U[equal]
    from results.json (ai-dlc 4.0 > agile-v 3.3; see TODO.md, owner review of the tie key)."""
    r = superiority(X([5] * 16), refs, P1, 16, True, 0.9)
    assert r["S2"]["profiles"]["equal"]["best"] == "ai-dlc"
    assert refs["ai-dlc"]["U"]["equal"] > refs["agile-v"]["U"]["equal"]


def with_target(results, slug, scores, comparison="same-round", role="target", benchmark=False):
    res = copy.deepcopy(results)
    e = copy.deepcopy(results["openspec"])
    e.update(role=role, benchmark=benchmark, L1_scores=scores, L1=cons.totals(scores), comparison=comparison,
             U={p: 2.0 for p in PROFS}, reliability={"alpha": 0.9}, redteam={"completed": True, "open_contests": 0})
    res[slug] = e
    return res


def pipeline(res, draws=300):
    return rk.rank(res), sn.sensitivity(res, 7, draws)


def test_verdict_set_ignores_additional_references(results):
    one = with_target(results, "x", [5] * 16)
    more = with_target(one, "extra-ref", [4] * 16, role="reference")
    a = evaluate(one, *pipeline(one), "x")
    b = evaluate(more, *pipeline(more), "x")
    assert a == b and a["verdict"] == "Superior"


def test_refs_with_an_additional_reference_are_rejected(results):
    res = with_target(results, "extra-ref", [4] * 16, role="reference")
    refs = verdict_refs(res)
    refs["extra-ref"] = {"s": [4] * 16, "U": {p: 2.0 for p in PROFS}}
    with pytest.raises(SuperiorityError):
        check_refs(refs, res)
    out = evaluate(with_target(res, "x", [5] * 16), {"weakest_vs_median": {"x": []}}, {}, "x", refs=refs)
    assert out["verdict"] == "none" and "additional" in out["reason"]


def test_precondition_cross_round_gives_none(results):
    res = with_target(results, "x", [5] * 16, comparison="cross-round")
    out = evaluate(res, *pipeline(res), "x")
    assert out["verdict"] == "none" and "cross-round" in out["reason"]


def test_precondition_missing_weakest_vs_median_gives_none(results):
    res = with_target(results, "x", [5] * 16)
    ranking, sens = pipeline(res)
    del ranking["weakest_vs_median"]["x"]
    out = evaluate(res, ranking, sens, "x")
    assert out["verdict"] == "none" and "weakest_vs_median" in out["reason"]


def test_precondition_open_contest_gives_none(results):
    res = with_target(results, "x", [5] * 16)
    res["x"]["redteam"]["open_contests"] = 1
    assert evaluate(res, *pipeline(res), "x")["verdict"] == "none"
