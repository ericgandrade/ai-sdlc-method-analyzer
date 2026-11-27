"""fitgap (plan §7.13; Task 2.16)."""
import copy
import pathlib

import pytest

from engine import consolidate as cons
from engine import fitgap, state
from engine.cli import main
from engine.common import FEATURES
from engine.jsonio import read_json, write_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "baseline" / "rounds" / "2026-11" / "derived"
MEDIAN = [3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 4, 3, 3, 2]


@pytest.fixture(scope="module")
def results():
    return read_json(DERIVED / "results.json")


def bench(results):
    return {m: e for m, e in results.items() if e["benchmark"]}


def target(scores, l4=None):
    return {"L1_scores": scores, "L4": l4 or {f: 2 for f in FEATURES}}


def test_gap_points_for_c5(results):
    s = list(MEDIAN)
    s[4] = 2
    out = fitgap.fitgap_pre(target(s), bench(results), {"C5": "independent reviewer context"})
    c5 = next(x for x in out["criteria"] if x["c"] == "C5")
    assert c5["best"] == 4 and c5["gap_points_baseline"] == 3.2
    assert "bmad" in c5["leaders"] and len(c5["leaders"]) > 1
    assert c5["first_unmet"] == "independent reviewer context" and c5["median_refs"] == 3


def test_refs_at_2_for_a_feature(results):
    l4 = {f: 2 for f in FEATURES}
    l4["F18"], l4["F21"] = 0, "NA"
    out = fitgap.fitgap_pre(target(list(MEDIAN), l4), bench(results))
    f18 = next(x for x in out["features"] if x["f"] == "F18")
    expected = sorted(m for m, e in bench(results).items() if e["L4"]["F18"] == 2)
    assert f18["refs_at_2"] == expected and "ai-dlc" not in expected        # ai-dlc has F18 at 0
    assert [x["f"] for x in out["features"]] == ["F18", "F21"]


def test_projection_is_cumulative_capped_and_a_hypothesis():
    items = [{"id": "R1", "horizon": "now", "to_level": {"C5": 4}},
             {"id": "R2", "horizon": "30", "to_level": {"C4": 5}},
             {"id": "R3", "horizon": "60-90", "to_level": {c: 9 for c in [f"C{i}" for i in range(1, 17)]}},
             {"id": "R4", "horizon": "30"}]
    s = list(MEDIAN)
    s[4] = 2
    out = fitgap.project(s, items)
    now, d30, d90 = (out["baseline_total_if_done"][h] for h in ("now", "30", "60-90"))
    assert now == round(out["current"] + 3.2, 1)
    assert d30 > now and d90 == 100.0
    assert out["hypothesis"] is True and out["items_without_to_level"] == ["R4"]


def test_cli_on_a_fitgap_run(monkeypatch, results):
    monkeypatch.chdir(ROOT)
    src = "20261127-101500-tiny"
    state.init(src, "folder", "tiny")
    res = copy.deepcopy(results)
    s = list(MEDIAN)
    s[4] = 2
    e = copy.deepcopy(results["openspec"])
    e.update(role="target", benchmark=False, L1_scores=s, L1=cons.totals(s), run=src)
    res["tiny"] = e
    write_json(state.run_path(src) / "results.json", res)
    st = state.load(src)
    st["status"] = "closed"
    state.save(st)
    fg = "20261127-111500-fitgap-tiny"
    state.init(fg, "fitgap", "tiny", sources=[src])
    assert main(["fitgap", "--run", fg]) == 0
    pre = read_json(state.run_path(fg) / "fitgap-pre.json")
    assert pre["source_run"] == src and any(x["c"] == "C5" for x in pre["criteria"])
    assert main(["fitgap", "--run", fg, "--project"]) == 3
    write_json(state.run_path(fg) / "fitgap.json", {"items": [{"id": "R1", "horizon": "now", "to_level": {"C5": 4}}]})
    assert main(["fitgap", "--run", fg, "--project"]) == 0
    assert read_json(state.run_path(fg) / "fitgap-projection.json")["hypothesis"] is True
