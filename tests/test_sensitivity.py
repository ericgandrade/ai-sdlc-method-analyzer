"""sensitivity and P(first) (plan §7.11; Task 2.12)."""
import copy
import pathlib
import random
import time

import pytest

from engine import consolidate as cons
from engine import sensitivity as sn
from engine.jsonio import dumps, read_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "baseline" / "rounds" / "2026-11" / "derived"


@pytest.fixture(scope="module")
def base():
    return read_json(DERIVED / "results.json")


def add(base, slug, scores, role="target", benchmark=False, u=0.5):
    res = copy.deepcopy(base)
    e = copy.deepcopy(base["openspec"])
    e.update(role=role, benchmark=benchmark, L1_scores=scores, L1=cons.totals(scores), u=[u] * 16, name=slug)
    res[slug] = e
    return res


def test_dirichlet_sums_to_100_and_is_reproducible():
    a = sn.dirichlet(random.Random(7), [0.5 * w for w in sn.BASE])
    b = sn.dirichlet(random.Random(7), [0.5 * w for w in sn.BASE])
    assert a == b and abs(sum(a) - 100) < 1e-9 and len(a) == 16


def test_dominant_vector_has_p_first_one():
    vec = {"hi": [5] * 16, "lo": [0] * 16}
    pf, mean = sn.p_first(vec, {"hi": [0.5] * 16, "lo": [0.5] * 16}, 1, 500)
    assert all(pf[s]["hi"] == 1.0 for s in pf) and all(mean[s]["hi"] == 1.0 for s in mean)


def test_ties_share_the_win():
    vec = {"a": [3] * 16, "b": [3] * 16}
    pf, _ = sn.p_first(vec, {"a": [0.0] * 16, "b": [0.0] * 16}, 1, 200)
    assert pf["centred"] == {"a": 0.5, "b": 0.5} and pf["score_perturbation"] == {"a": 0.5, "b": 0.5}


def test_tornado_and_loo_shapes_and_determinism(base):
    vec = {m: base[m]["L1_scores"] for m in sorted(base)}
    t1, t2 = sn.tornado(vec), sn.tornado(vec)
    assert t1 == t2 and len(t1) == 32 and {r["factor"] for r in t1} == {0.5, 1.5}
    rows = sn.loo(vec)
    assert len(rows) == 16 and all(set(r["ranks"]) == set(vec) for r in rows)


def test_perturbation_uses_each_methods_own_u_and_clips():
    draw = sn.perturbed({"a": [0.0] * 16, "b": [10.0] * 16})
    rng = random.Random(3)
    assert draw(rng, "a", [2] * 16) == [2] * 16
    assert all(0 <= x <= 5 for x in draw(rng, "b", [4] * 16))


def test_verdict_set_is_byte_identical_with_extra_methods(base):
    one = add(base, "x", [4] * 16)
    more = add(add(one, "extra-ref", [5] * 16, role="reference"), "y", [3] * 16)
    a = sn.sensitivity(one, 11, 400)
    b = sn.sensitivity(more, 11, 400)
    assert dumps(a["verdict_set"]["x"]) == dumps(b["verdict_set"]["x"])
    assert a["verdict_set"]["x"]["members"] == sorted([m for m in base] + ["x"])
    assert "extra-ref" in b["p_first"]["centred"]                     # display set may include it
    assert set(b["verdict_set"]) == {"x", "y"}


def test_seed_reproducible_and_docs_excluded(base):
    res = add(base, "docsy", [2] * 16)
    res["docsy"]["range"] = {"floor": {}}
    a, b = sn.sensitivity(res, 5, 300), sn.sensitivity(res, 5, 300)
    assert a == b and "docsy" not in a["p_first"]["centred"] and "docsy" not in a["verdict_set"]


def test_runtime_3x10000_draws_on_11_methods(base):
    res = add(add(base, "x", [4] * 16), "y", [3] * 16)
    vec = {m: res[m]["L1_scores"] for m in sorted(res)}
    t = time.perf_counter()
    sn.p_first(vec, {m: res[m]["u"] for m in vec}, 20261127, 10000)
    assert time.perf_counter() - t < 60


def test_shipped_baseline_sensitivity(base):
    """Committed with seed 20261127; P(first) is compared within a tolerance because the gamma
    sampler goes through the platform's libm (CI runs Linux, macOS and Windows)."""
    shipped = read_json(DERIVED / "sensitivity.json")
    assert shipped["seed"] == 20261127 and shipped["draws"] == 10000
    fresh = sn.sensitivity(base, 20261127, 10000)
    for k in ("profiles", "tornado", "loo", "verdict_set"):
        assert fresh[k] == shipped[k], k
    for s in fresh["p_first"]:
        for m, p in fresh["p_first"][s].items():
            assert abs(p - shipped["p_first"][s][m]) <= 0.002, (s, m)
