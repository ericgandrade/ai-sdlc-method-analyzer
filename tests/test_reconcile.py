"""reconcile pre/blind, calibration, alpha, audit-scope, adjudication import (plan §7.7, §5.16; Task 2.7)."""
import json
import math
import pathlib
import shutil

import pytest

from engine import adjudication, reconcile, state, stats
from engine.adjudication import AdjudicationError
from engine.jsonio import read_json, write_json
from engine.reconcile import ReconcileError

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "run-min"
RID = "20261127-101500-tiny"
C = [f"C{i}" for i in range(1, 17)]
S1 = [2, 3, 3, 3, 2, 2, 2, 1, 2, 2, 2, 1, 3, 2, 3, 1]


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)


def rd(rid=RID):
    return state.run_path(rid)


def run_min(rid=RID, **kw):
    st = state.init(rid, "folder", "tiny", **kw)
    shutil.copytree(FIX / "sealed", rd(rid) / "sealed")
    return st


def reconciled(vector, conf=None, r=None):
    cells = {c: {"s": vector[i], "conf": (conf or {}).get(c, "M"), "rule": "equal", "cites": [], "note": "",
                 **({"r": r[i], "r_rule": "lower"} if r else {})} for i, c in enumerate(C)}
    out = {"vector": vector, "cells": cells, "route": {"agreed": True, "route": "default", "note": ""}}
    if r:
        out.update(r=r, ra=[round(v * x, 2) for v, x in zip(vector, r)])
    write_json(rd() / "reconciled.json", out)
    return out


# ---------------------------------------------------------------- reconcile pre / blind

def test_pre_proposals_for_0_1_and_3():
    run_min()
    out = reconcile.pre(RID)
    cells = out["cells"]
    assert cells["C1"]["diff"] == 0 and cells["C1"]["proposal"] == "equal" and cells["C1"]["proposed"] == 2
    assert cells["C2"]["diff"] == 1 and cells["C2"]["proposal"] == "lower" and cells["C2"]["proposed"] == 2
    assert cells["C5"]["diff"] == 3 and cells["C5"]["proposal"] == "needs-written" and cells["C5"]["proposed"] is None
    assert out["needs_written"] == ["C5"]
    assert cells["C4"]["conf_worst"] == "L"
    assert (rd() / "reconcile-pre.json").exists()


def test_pre_r_proposals_take_the_lower_value_for_design_only():
    run_min(status="design-only")
    for inst, r in (("S1", 0.9), ("S2", 0.7)):
        p = rd() / "sealed" / inst / "target.md"
        text = p.read_text()
        card = json.loads(text.split("```json\n")[-1].split("\n```")[0])
        for cell in card["scores"].values():
            cell.update(D=cell["s"], r=r, ra=round(cell["s"] * r, 2))
        p.write_text("```json\n" + json.dumps(card) + "\n```\n")
    cells = reconcile.pre(RID)["cells"]
    assert cells["C1"]["r"] == {"S1": 0.9, "S2": 0.7} and cells["C1"]["r_proposed"] == 0.7
    assert cells["C1"]["r_proposal"] == "lower"


def test_pre_uses_the_replacement_instance():
    run_min()
    st = state.load(RID)
    st["instances"]["S1"] = "S1r"
    state.save(st)
    shutil.copytree(rd() / "sealed" / "S2", rd() / "sealed" / "S1r")
    assert reconcile.pre(RID)["instances"] == ["S1r", "S2"]


def test_blind_has_no_r_field():
    run_min(status="design-only")
    reconciled(S1, r=[0.8] * 16)
    out = reconcile.blind(RID)
    text = (rd() / "reconciled-blind.json").read_text()
    assert '"r"' not in text and '"ra"' not in text and '"r_rule"' not in text
    assert out["vector"] == S1


# ---------------------------------------------------------------- calibration

def test_calibration_both_deltas_and_drift():
    run_min()
    out = reconcile.calibration(RID)
    ref = out["refs"]["addyosmani"]
    assert ref["reconciled_total"] == 57.6 and ref["threshold"] == 2.9
    s1, s2 = ref["per_scorer"]["S1"], ref["per_scorer"]["S2"]
    assert s1["delta_reconciled"] == 0.0 and s1["agreement_exact_reconciled"] == 1.0 and s1["drift"] is False
    raw_mean = sum(ref["raw_totals"]) / 2
    assert s1["delta_raw"] == round(57.6 - raw_mean, 1)
    assert s2["delta_reconciled"] == round(35.4 - 57.6, 1) and s2["drift"] is True
    assert out["drift"] is True
    assert reconcile.comparison(RID) == "cross-round" and state.load(RID)["comparison"] == "cross-round"


def test_drift_threshold_is_u_ref_on_either_delta(monkeypatch):
    run_min()
    # S2 one point higher on C2 (weight 8): total 59.2, within U_ref 2.9 of both the reconciled
    # total 57.6 and the raw-sheet mean 60.3, and agreement at least 0.5 -> no drift
    p = rd() / "sealed" / "S2" / "cal-addyosmani.md"
    card = json.loads(p.read_text().split("```json\n")[-1].split("\n```")[0])
    for c, v in zip(C, [2, 3, 5, 3, 3, 2, 2, 2, 2, 2, 3, 3, 5, 3, 4, 0]):
        card["scores"][c]["s"] = v
    card["scores"]["C2"]["s"] = 4
    p.write_text("```json\n" + json.dumps(card) + "\n```\n")
    out = reconcile.calibration(RID)
    assert out["refs"]["addyosmani"]["per_scorer"]["S2"]["drift"] is False and out["drift"] is False


def test_cal_refs_length_two_for_design_only_and_target_excluded():
    assert state.init(RID, "folder", "tiny", status="design-only")["cal_refs"] == ["mattpocock", "bmad"]
    with pytest.raises(state.StateError):
        state.init("20261127-101501-tiny", "folder", "tiny", cal_refs=["addyosmani", "tiny"])


# ---------------------------------------------------------------- alpha

def test_alpha_over_the_fixture_equals_hand_checked_value():
    run_min()
    out = reconcile.alpha(RID)
    pairs = [(2, 2), (3, 2), (3, 3), (3, 3), (2, 5), (2, 2), (2, 2), (1, 1), (2, 2), (2, 2), (2, 2), (1, 1), (3, 3),
             (2, 2), (3, 3), (1, 1),
             (2, 1), (3, 2), (5, 3), (3, 2), (3, 2), (2, 1), (2, 1), (2, 1), (2, 1), (2, 1), (3, 2), (3, 2), (5, 3),
             (3, 2), (4, 3), (0, 0)]
    assert out["units"] == 32 and out["coders"] == 2 and out["small_set"] is True
    assert out["alpha"] == round(stats.alpha_ordinal(pairs), 4) == 0.6116
    assert out["gate"] is False
    lo, hi = out["ci90"]
    assert lo <= out["alpha"] <= hi


def test_alpha_with_a_third_scorer_and_missing_cells():
    run_min()
    st = state.load(RID)
    st["instances"]["extra"] = ["S3"]
    state.save(st)
    (rd() / "sealed" / "S3").mkdir()
    shutil.copy(rd() / "sealed" / "S1" / "target.md", rd() / "sealed" / "S3" / "target.md")
    out = reconcile.alpha(RID)
    assert out["coders"] == 3 and out["units"] == 32
    units, _ = reconcile.units_for(state.load(RID))
    assert units[16][2] is None              # S3 has no calibration sheet
    assert out["alpha"] == round(stats.alpha_ordinal_general(units), 4)


# ---------------------------------------------------------------- audit scope (#43)

def test_audit_scope_rules_and_seed():
    run_min()
    vec = list(S1)
    vec[4], vec[15], vec[0], vec[7], vec[11] = 4, 3, 0, 0, 0   # C5 at 4; total 44.0, next to kiro at 44.4
    reconciled(vec, conf={"C9": "L"})
    a = reconcile.audit_scope(RID)
    assert not a["full"]
    assert "C5" in a["cells"] and "C9" in a["cells"]
    forced = [c for c, r in a["reasons"].items() if any("sample" not in x for x in r)]
    rest = 16 - len(forced)
    assert len(a["sample"]) == math.ceil(0.15 * rest)
    assert reconcile.audit_scope(RID) == a          # deterministic for the run's seed
    rank_moves = [c for c, r in a["reasons"].items() if any("rank" in x for x in r)]
    assert rank_moves                                 # 44.x sits next to kiro at 44.4


def test_audit_scope_full_for_design_only():
    run_min(status="design-only")
    reconciled(S1, r=[0.8] * 16)
    a = reconcile.audit_scope(RID)
    assert a["full"] and a["cells"] == C


def test_audit_scope_full_for_baseline_top_two():
    run_min()
    reconciled([5] * 16)
    a = reconcile.audit_scope(RID)
    assert a["full"] and len(a["cells"]) == 16


def test_audit_scope_differs_by_seed():
    run_min(seed=1)
    reconciled(S1)
    a = reconcile.audit_scope(RID)
    state.init("20261127-101501-tiny", "folder", "tiny", seed=2)
    write_json(state.run_path("20261127-101501-tiny") / "reconciled.json", read_json(rd() / "reconciled.json"))
    b = reconcile.audit_scope("20261127-101501-tiny")
    assert a["seed"] != b["seed"]


# ---------------------------------------------------------------- adjudication import (#46)

def contests(*items):
    write_json(rd() / "redteam.json", {"final": S1, "changes": [], "completed": True, "contests": list(items)})


def decide(tmp_path, rows):
    f = tmp_path / "decisions.json"
    f.write_text(json.dumps({"decisions": rows}))
    return f


def test_adjudication_request_and_import(tmp_path, monkeypatch):
    run_min()
    reconciled(S1)
    write_json(rd() / "target.json", {"private": True})
    contests({"c": "C5", "type": "a", "outcome": "to-adjudicator", "evidence": "target:skills/review/SKILL.md:3"},
             {"c": "C2", "type": "f", "outcome": "to-adjudicator", "evidence": "target:skills/plan/SKILL.md:4"},
             {"c": "C3", "type": "b", "outcome": "rejected", "evidence": "x"})
    req = adjudication.request(RID)
    text = req.read_text()
    assert text.startswith("> **Private") and "the tool sends nothing" in text and "Contest 0" in text
    assert "total" not in text.lower().replace("totals, ranks", "")
    assert state.load(RID)["status"] == "waiting-external"
    monkeypatch.setattr(state, "is_interactive", lambda: True)
    ok = [{"contest_id": 0, "c": "C5", "kind": "score", "decision": "upheld", "after": 3, "after_r": None,
           "boundary_verdict": None, "evidence": "target:skills/review/SKILL.md:3", "reason": "opt-in"},
          {"contest_id": 1, "c": "C2", "kind": "r", "decision": "upheld", "after": None, "after_r": 0.8,
           "boundary_verdict": None, "evidence": "target:skills/plan/SKILL.md:4", "reason": "lower r"}]
    out = adjudication.import_decisions(RID, decide(tmp_path, ok))
    assert out["adjudicator"] == "person" and (rd() / "adjudication.json").exists()
    from engine.validate import check
    assert check("adjudication", read_json(rd() / "adjudication.json")) == []

    missing = ok[:1]
    with pytest.raises(AdjudicationError) as e:
        adjudication.import_decisions(RID, decide(tmp_path, missing))
    assert "no decision" in str(e.value)
    bad_r = [ok[0], dict(ok[1], after_r=0.5)]
    with pytest.raises(AdjudicationError) as e:
        adjudication.import_decisions(RID, decide(tmp_path, bad_r))
    assert "0.6-1.0" in str(e.value)
    no_r = [ok[0], dict(ok[1], after_r=None)]
    with pytest.raises(AdjudicationError) as e:
        adjudication.import_decisions(RID, decide(tmp_path, no_r))
    assert "needs after_r" in str(e.value)


def test_adjudication_markdown_table(tmp_path, monkeypatch):
    run_min()
    reconciled(S1)
    contests({"c": "C5", "type": "a", "outcome": "to-adjudicator", "evidence": "target:a.md:1"})
    req = adjudication.request(RID)
    filled = req.read_text().replace("| 0 | C5 | score |  |  |  |  |  |  |",
                                     "| 0 | C5 | score | rejected |  |  |  | target:a.md:1 | stays |")
    f = tmp_path / "filled.md"
    f.write_text(filled)
    monkeypatch.setattr(state, "is_interactive", lambda: True)
    assert adjudication.import_decisions(RID, f)["decisions"][0]["decision"] == "rejected"
