"""apply-audit (plan §7.7; Task 2.8)."""
import json
import pathlib
import shutil

import pytest

from engine import apply_audit, state
from engine.apply_audit import AuditError
from engine.jsonio import read_json, write_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RID = "20261127-101500-tiny"
C = [f"C{i}" for i in range(1, 17)]
REC = [2, 3, 3, 3, 2, 2, 2, 1, 2, 2, 2, 1, 3, 2, 3, 1]


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)


def rd():
    return state.run_path(RID)


def setup_run(design=False, audit=None, redteam=None, adjudication=None):
    state.init(RID, "folder", "tiny", status="design-only" if design else "implemented")
    shutil.copytree(FIX / "tiny-method", rd() / "target")
    cells = {c: {"s": REC[i], "conf": "M", "rule": "equal"} for i, c in enumerate(C)}
    rec = {"vector": REC, "cells": cells, "route": {"agreed": True}}
    if design:
        rec.update(r=[0.9] * 16, ra=[round(v * 0.9, 2) for v in REC])
    write_json(rd() / "reconciled.json", rec)
    lenses = json.loads((FIX / "lenses-example.json").read_text())
    for e in lenses["L5"]["T1"] + lenses["L5"]["T2"] + lenses["L5"]["T3"]:
        e["path"] = e["path"].replace("cache:tiny/", "target:")
    write_json(rd() / "lenses.json", lenses)
    if redteam:
        write_json(rd() / "redteam.json", redteam)
    if audit:
        write_json(rd() / "lens-audit.json", audit)
    if adjudication:
        write_json(rd() / "adjudication.json", adjudication)
    return lenses


def red(final, final_r=None):
    return {"final": final, "final_r": final_r, "changes": [], "contests": [], "completed": True}


AUDIT = {"checked": {"L2": 1, "L3": 1, "L4": 34, "L5": 3}, "kept": {},
         "overrides": {"L3": "A1", "L2": {"C5": 2}, "L4": {"F2": 0}},
         "L5_corrections": {"T3_add": ["target:skills/review/SKILL.md"], "T1_remove": ["target:skills/plan/SKILL.md"]}}


def test_idempotent_byte_identical():
    setup_run(audit=AUDIT, redteam=red([1] * 16))
    apply_audit.apply(RID)
    a = ((rd() / "l1.final.json").read_bytes(), (rd() / "lenses.final.json").read_bytes())
    apply_audit.apply(RID)
    assert a == ((rd() / "l1.final.json").read_bytes(), (rd() / "lenses.final.json").read_bytes())


def test_starts_from_pristine_snapshot():
    setup_run(audit=AUDIT)
    (rd() / "pristine").mkdir()
    shutil.copy(rd() / "lenses.json", rd() / "pristine" / "lenses.json")
    l = read_json(rd() / "lenses.json")
    l["L3"]["level"] = "A5"
    write_json(rd() / "lenses.json", l)        # an edit after the stage was done is ignored
    _, lenses = apply_audit.apply(RID)
    assert lenses["L3"]["level"] == "A1"


def test_non_resolving_added_path_exit_3():
    audit = dict(AUDIT, L5_corrections={"T2_add": ["target:does/not/exist.md"]})
    setup_run(audit=audit)
    with pytest.raises(AuditError) as e:
        apply_audit.apply(RID)
    assert e.value.code == 3


def test_overrides_only_touch_listed_cells():
    before = setup_run(audit=AUDIT)
    _, after = apply_audit.apply(RID)
    changed_l4 = [f for f in before["L4"] if before["L4"][f]["v"] != after["L4"][f]["v"]]
    assert changed_l4 == ["F2"] and after["L4"]["F2"]["audit_override"] is True
    assert after["L3"]["level"] == "A1" and after["L2"]["ceiling"]["C5"]["s"] == 2
    assert {k: v for k, v in after["L2"]["ceiling"].items() if k != "C5"} == \
           {k: v for k, v in before["L2"]["ceiling"].items() if k != "C5"}
    assert [e["path"] for e in after["L5"]["T1"]] == []
    assert after["L5"]["T3"][-1]["path"] == "target:skills/review/SKILL.md"
    assert after["L5"]["T2"] == before["L5"]["T2"]


def test_redteam_final_replaces_l1_and_adjudication_applies_after():
    final = list(REC)
    final[4] = 4
    adj = {"adjudicator": "agent:adj", "decisions": [
        {"contest_id": 0, "c": "C5", "kind": "score", "decision": "upheld", "after": 3, "evidence": "target:a.md:1"},
        {"contest_id": 1, "c": "C2", "kind": "score", "decision": "rejected", "after": 0, "evidence": "target:a.md:2"}]}
    setup_run(redteam=red(final), adjudication=adj)
    l1, _ = apply_audit.apply(RID)
    assert l1["source"] == "redteam.final"
    assert l1["vector"][4] == 3 and l1["vector"][1] == REC[1]
    assert l1["adjudicated"] == [0]


def test_no_redteam_keeps_reconciled_vector():
    setup_run()
    assert apply_audit.apply(RID)[0]["vector"] == REC


def test_final_r_for_design_only():
    adj = {"adjudicator": "person", "decisions": [
        {"contest_id": 0, "c": "C3", "kind": "r", "decision": "upheld", "after_r": 0.6, "evidence": "target:a.md:1"}]}
    setup_run(design=True, redteam=red(REC, [0.8] * 16), adjudication=adj)
    l1, _ = apply_audit.apply(RID)
    assert l1["r"][0] == 0.8 and l1["r"][2] == 0.6
    assert l1["ra"][2] == round(REC[2] * 0.6, 2)
