"""consolidate (plan §7.9; Task 2.10)."""
import pathlib
import shutil

import pytest

from engine import consolidate as cons
from engine import state
from engine.common import FEATURES
from engine.jsonio import read_json, write_json
from engine.ranges import RangesError

ROOT = pathlib.Path(__file__).resolve().parents[1]
RID = "20261127-101500-tiny"
C = [f"C{i}" for i in range(1, 17)]
VEC = [2, 3, 3, 3, 2, 2, 2, 1, 2, 2, 2, 1, 3, 2, 3, 1]

A2 = {  # Appendix A.2: baseline, equal, startup, regulated, autonomous
    "ai-dlc": (68.6, 66.2, 67.4, 68.4, 72.0), "agile-v": (67.0, 66.2, 68.0, 65.6, 67.4),
    "bmad": (66.8, 65.0, 68.8, 65.2, 67.8), "addyosmani": (57.6, 55.0, 60.2, 54.6, 57.2),
    "superpowers": (56.0, 53.8, 58.4, 51.0, 60.2), "kiro": (44.4, 45.0, 48.2, 41.6, 45.2),
    "mattpocock": (43.8, 43.8, 46.6, 40.4, 44.6), "spec-kit": (43.2, 43.8, 48.2, 39.6, 43.2),
    "openspec": (38.8, 36.2, 40.6, 37.2, 36.8),
}
A3 = {  # Appendix A.3: L2 baseline, L3, C8, L4 points
    "ai-dlc": (69.8, "A3", 4, 57), "agile-v": (73.2, "A3", 2, 48), "bmad": (68.4, "A2", 3, 53),
    "addyosmani": (59.0, "A2", 2, 51), "superpowers": (56.0, "A3", 3, 40), "kiro": (45.4, "A3", 2, 33),
    "mattpocock": (45.4, "A3", 2, 35), "spec-kit": (45.0, "A2", 2, 33), "openspec": (38.8, "A1", 0, 27),
}
PROFILE_ORDER = ("baseline", "equal", "startup", "regulated", "autonomous")
RECORDED_U = {"ai-dlc": 3.1, "agile-v": 3.6, "bmad": 2.7, "addyosmani": 2.9, "superpowers": 2.3,
              "kiro": 2.7, "mattpocock": 2.8, "spec-kit": 2.6, "openspec": 2.6}


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)


def rd(rid=RID):
    return state.run_path(rid)


def lenses_l4(values):
    return {"L2": None, "L3": {"level": "A2", "conf": "M"}, "L4": {f: {"v": v} for f, v in zip(FEATURES, values)}}


def assessed_run(rid=RID, vector=VEC, design=False, r=None, calibration_drift=False):
    state.init(rid, "folder", "tiny", status="design-only" if design else "implemented")
    write_json(rd(rid) / "l1.final.json", {"vector": vector, "r": r, "ra": None, "source": "reconciled.vector",
                                           "adjudicated": [], "boundary": []})
    write_json(rd(rid) / "lenses.final.json", lenses_l4([1] * 34))
    cells = {c: {"s": vector[i], "conf": "M", "rule": "equal"} for i, c in enumerate(C)}
    write_json(rd(rid) / "reconciled.json", {"vector": vector, "cells": cells, "route": {"agreed": True}})
    write_json(rd(rid) / "calibration.json", {"refs": {}, "drift": calibration_drift})
    write_json(rd(rid) / "redteam.json", {"final": vector, "contests": [], "changes": [], "completed": True})


def test_baseline_reproduces_appendix_a2_for_every_profile(tmp_path):
    res = cons.consolidate(out_dir=tmp_path)
    assert sorted(res) == sorted(A2)
    for slug, row in A2.items():
        assert tuple(res[slug]["L1"][p] for p in PROFILE_ORDER) == row, slug
    assert read_json(tmp_path / "results.json") == res


def test_baseline_reproduces_appendix_a3_and_the_u_rule(tmp_path):
    res = cons.consolidate(out_dir=tmp_path)
    for slug, (l2, l3, c8, pts) in A3.items():
        e = res[slug]
        assert (e["L2"]["baseline"], e["L3"], e["C8"], e["L4_points"]) == (l2, l3, c8, pts), slug
        assert e["L3_num"] == int(l3[1])
        assert e["L4_coverage"] == round(100 * pts / 68)
        assert sum(e["L4_groups"].values()) > 0 and set(e["L4_groups"]) >= {"Discovery", "Economy"}
        assert e["U"]["baseline"] == RECORDED_U[slug] == e["U_recorded"]
        assert e["benchmark"] is True and e["role"] == "reference"
    # every other profile uses total_u(u, w): ai-dlc equal 4.0 (U from scorecards, not the recorded 3.1)
    assert res["ai-dlc"]["U"]["equal"] == 4.0
    assert res["kiro"]["L5"]["T0"] is None and res["addyosmani"]["L5"]["T1"] == 2338


def test_l4_na_counts_zero_and_is_listed():
    f = cons.lens_fields(lenses_l4(["NA", 2] + [1] * 32), [2] * 16)
    assert f["L4_points"] == 2 + 32 and f["L4_na"] == ["F1"]
    assert f["L4_groups"]["Discovery"] == round(100 * (0 + 2 + 1 + 1) / 8)


def test_l2_takes_the_ceiling_where_higher():
    lenses = lenses_l4([0] * 34)
    lenses["L2"] = {"ceiling": {"C5": {"s": 4}, "C1": {"s": 1}}}
    f = cons.lens_fields(lenses, VEC)
    assert f["L2_scores"][4] == 4 and f["L2_scores"][0] == VEC[0]


def test_design_only_fixture_ra_gap():
    assessed_run(vector=[4] * 16, design=True, r=[0.8] * 16)
    res = cons.consolidate(RID)
    e = res["tiny"]
    assert e["L1_scores"] == [3.2] * 16 and e["design"]["RA_scores"] == [3.2] * 16
    assert e["L1"]["baseline"] == 64.0 == e["design"]["RA_total"]["baseline"]
    assert e["design"]["design_total"]["baseline"] == 80.0
    assert e["design"]["realization_gap"]["baseline"] == 16.0
    # u carries the realization term: sqrt(0.25 + ((1-0.8)*4/2)^2)
    assert e["u"][0] == round((0.25 + 0.16) ** 0.5, 4)


def test_target_fields_and_cross_round_without_a_reproduction_record():
    assessed_run()
    res = cons.consolidate(RID)
    assert set(res) == set(A2) | {"tiny"}
    e = res["tiny"]
    assert e["role"] == "target" and e["benchmark"] is False and e["run"] == RID
    assert e["comparison"] == "cross-round"
    assert e["L1_scores"] == VEC and e["redteam"] == {"completed": True, "open_contests": 0}
    assert (rd() / "results.json").exists()


def project_copy(tmp_path, version="0.1.0", passed=True):
    root = tmp_path / "proj"
    shutil.copytree(ROOT / "baseline", root / "baseline")
    shutil.copytree(ROOT / "references", root / "references")
    write_json(root / "baseline" / "rounds" / "2026-11" / "reproduction.json",
               {"records": [{"pipeline_version": version, "pass": passed}]})
    return root


def test_same_round_needs_the_record_and_no_drift(tmp_path):
    root = project_copy(tmp_path)
    assessed_run()
    assert cons.consolidate(RID, root=root)["tiny"]["comparison"] == "same-round"
    assessed_run("20261127-101501-tiny", calibration_drift=True)
    assert cons.consolidate("20261127-101501-tiny", root=root)["tiny"]["comparison"] == "cross-round"


def test_a_run_binds_to_its_own_round_not_current(tmp_path):
    root = project_copy(tmp_path)
    assessed_run()
    before = cons.consolidate(RID, root=root)["tiny"]["comparison"]
    new = root / "baseline" / "rounds" / "2026-12"
    shutil.copytree(root / "baseline" / "rounds" / "2026-11", new)
    (new / "reproduction.json").unlink()
    (root / "baseline" / "current").write_text("2026-12\n")
    after = cons.consolidate(RID, root=root)
    assert before == after["tiny"]["comparison"] == "same-round"
    assert after["tiny"]["round_id"].endswith("+2026-11")


@pytest.mark.parametrize("version,expected", [("0.1.7", "same-round"), ("0.2.0", "cross-round")])
def test_patch_difference_keeps_the_record_minor_does_not(tmp_path, version, expected):
    root = project_copy(tmp_path, version=version)
    assessed_run()
    assert cons.consolidate(RID, root=root)["tiny"]["comparison"] == expected


DOCS = {"name": "Docs sample", "evidence": "D", "type_declaration": "closed",
        "L1_floor": [2, 2, 3, 2, 3, 2, 1, 2, 2, 2, 1, 1, 3, 2, 2, 1],
        "L1_ceiling": [3, 3, 4, 3, 4, 3, 2, 2, 3, 3, 2, 2, 4, 3, 3, 2],
        "conf": {c: "M" for c in C}, "L3": "A2", "L4": {f: {"v": 1, "cite": "docs:a.md#p1"} for f in FEATURES},
        "not_assessable": [], "needed": []}


def docs_run(rid="20261127-101500-docsy", docs=DOCS):
    state.init(rid, "docs", "docsy")
    write_json(rd(rid) / "docs-only.json", docs)
    return rid


def test_docs_only_target_carries_range():
    rid = docs_run()
    e = cons.consolidate(rid)["docsy"]
    assert e["type"] == "docs" and e["range"]["centre"]["totals"]["baseline"] == 50.0
    assert e["comparison"] == "cross-round"


def test_docs_cap_violation_is_refused():
    rid = docs_run(docs=dict(DOCS, type_declaration="open-unread"))
    with pytest.raises(RangesError) as ei:
        cons.consolidate(rid)
    assert ei.value.code == 1


def test_cli_without_run_needs_out(capsys):
    from engine.cli import main
    assert main(["consolidate"]) == 2


def test_shipped_derived_results_are_current(tmp_path):
    cons.consolidate(out_dir=tmp_path)
    shipped = ROOT / "baseline" / "rounds" / "2026-11" / "derived" / "results.json"
    assert (tmp_path / "results.json").read_bytes() == shipped.read_bytes()
