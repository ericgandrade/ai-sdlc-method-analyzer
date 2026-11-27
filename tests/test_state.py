"""Run state, stages, gates, marker and privileged commands (plan §4.5, §6, §7.15; Task 2.4)."""
import datetime
import json
import pathlib
import subprocess
import sys

import pytest

from engine import paths, runlog, state
from engine.jsonio import read_json, write_json
from engine.state import StateError

ROOT = pathlib.Path(__file__).resolve().parents[1]
RID = "20261127-101500-tiny"


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)


def rd(rid=RID):
    return state.run_path(rid)


def put(rel, text="x\n", rid=RID):
    p = rd(rid) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def finish(stage, *outputs, rid=RID):
    st = state.load(rid)
    for d in st["stages"][stage]["declared_outputs"]:
        if (rd(rid) / d).is_file():
            continue
        put(d + "f.md" if d.endswith("/") else d, "{}\n" if d.endswith(".json") else "x\n", rid=rid)
    if st["stages"][stage]["status"] == "pending":
        state.start(rid, stage)
    return state.done(rid, stage, list(outputs))


def walk(stages, rid=RID):
    for s in stages:
        finish(s, rid=rid)


def names(rid=RID):
    return state.next_stages(rid)[1]


def test_init_writes_freeze_seed_and_marker():
    st = state.init(RID, "folder", "tiny")
    assert set(st["freeze"]) == {"methodology-v1.0.md", "evaluator-agent-v1.0.md", "rubric-v2.0.pt.md",
                                 "rulings-v1.md", "protocol-v1.md"}
    assert st["seed"] == 20261127 and st["cal_refs"] == ["addyosmani"]
    assert st["round_id"] == "0.1.0+2026-11" and st["comparison"] == "cross-round"
    assert [e["run_id"] for e in paths.amahome.read_marker(paths.data_dir())] == [RID]
    assert state.init("20261127-101501-x", "folder", "x", seed=7)["seed"] == 7


def test_init_cal_refs_rules():
    assert state.init(RID, "folder", "tiny", status="design-only")["cal_refs"] == ["mattpocock", "bmad"]
    st = state.init("20261127-101501-addyosmani", "reference", "addyosmani")
    assert st["cal_refs"] == ["mattpocock"] and "fallback" in st["cal_reason"]
    with pytest.raises(StateError):
        state.init("20261127-101502-tiny", "folder", "tiny", cal_refs=["tiny"])


def test_init_vendor_conflict_refused():
    with pytest.raises(StateError) as e:
        state.init(RID, "reference", "ai-dlc", scorer_model="nova-pro")
    assert "vendor conflict" in str(e.value)
    with pytest.raises(StateError):
        state.init("20261127-101501-ralph-loop-plugin", "reference", "ralph-loop-plugin")
    assert state.init("20261127-101502-ai-dlc", "reference", "ai-dlc", scorer_model="claude-x")


def test_next_follows_the_dependency_graph():
    state.init(RID, "folder", "tiny")
    assert names() == ["S00"]
    walk(["S00", "S01", "S02"])
    assert set(names()) == {"S03", "S04:S1", "S04:S2", "S13"}
    finish("S03")
    assert set(names()) == {"S04:S1", "S04:S2", "S13", "S08a"}


def test_start_sets_running_and_done_clears_it():
    state.init(RID, "folder", "tiny")
    assert state.start(RID, "S00")["stages"]["S00"]["status"] == "running"
    st = state.done(RID, "S00")
    assert st["stages"]["S00"]["status"] == "done" and st["stages"]["S00"]["finished"]
    with pytest.raises(StateError):
        state.start(RID, "S02")          # dependencies not done


def test_per_instance_stages_have_disjoint_outputs():
    st = state.init(RID, "folder", "tiny")
    a, b = (set(st["stages"][s]["declared_outputs"]) for s in ("S04:S1", "S04:S2"))
    assert a == {"sealed/S1/"} and b == {"sealed/S2/"} and not a & b


def test_done_refuses_missing_declared_outputs():
    state.init(RID, "folder", "tiny")
    walk(["S00"])
    state.start(RID, "S01")
    with pytest.raises(StateError) as e:
        state.done(RID, "S01")
    assert e.value.code == 3


def test_done_s07r_requires_r_independent():
    state.init(RID, "folder", "tiny", status="design-only")
    walk(["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S06"])
    state.start(RID, "S07r")
    with pytest.raises(StateError) as e:
        state.done(RID, "S07r")
    assert "r_independent" in str(e.value)
    put("r_independent.json", "{}\n")
    assert state.done(RID, "S07r")["stages"]["S07r"]["outputs"][0]["path"] == "run:r_independent.json"


def test_tampered_output_resets_downstream():
    state.init(RID, "folder", "tiny")
    walk(["S00", "S01", "S02", "S03", "S08a"])
    put("trace.md", "edited\n")
    _, ready, reset = state.next_stages(RID)
    assert "S03" in reset and "S08a" in reset
    assert "S03" in ready and "S08a" not in ready


def test_same_file_rewritten_by_a_later_stage_is_not_tampering():
    state.init(RID, "folder", "tiny")
    walk(["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S06", "S07", "S08a"])
    put("lenses.json", "with L2\n")
    finish("S08b")
    assert state.next_stages(RID)[2] == []


def assess_to(stage, rid=RID, design=False):
    order = ["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S06"] + (["S07r"] if design else []) + \
            ["S07", "S08a", "S08b", "S09", "S10", "S11", "S12", "S13", "S14"]
    walk(order[:order.index(stage) + 1], rid=rid)


def test_menu1_run_closes_at_s14():
    state.init(RID, "folder", "tiny")
    assess_to("S12")
    with pytest.raises(StateError):
        state.close(RID)
    walk(["S13", "S14"])
    st, msg = state.close(RID)
    assert st["status"] == "closed" and "complete" in msg
    assert paths.amahome.read_marker(paths.data_dir()) == []


def test_docs_run_closes_at_d3():
    st = state.init(RID, "docs", "tiny", type_="docs")
    assert st["stages"]["D2"]["status"] == "skipped" and st["stages"]["S13"]["status"] == "skipped"
    walk(["S00", "S01", "S02", "D1", "D3"])
    assert state.close(RID)[0]["status"] == "closed"


def test_reference_run_closes_at_s12():
    state.init(RID, "reference", "superpowers")
    assess_to("S12")
    assert state.close(RID)[0]["status"] == "closed"


def test_closed_run_cannot_be_reopened():
    state.init(RID, "docs", "tiny", type_="docs")
    walk(["S00", "S01", "S02", "D1", "D3"])
    state.close(RID)
    for fn in (lambda: state.start(RID, "S00"), lambda: state.resume(RID), lambda: state.next_stages(RID),
               lambda: state.retry(RID, "S07", "G5")):
        with pytest.raises(StateError) as e:
            fn()
        assert "never reopened" in str(e.value)


def closed_assessment(rid):
    state.init(rid, "folder", rid.split("-", 2)[2])
    assess_to("S14", rid=rid)
    state.close(rid)


def test_compare_reads_two_closed_runs_and_closes_at_s17():
    a, b = "20261127-090000-alpha", "20261127-090100-beta"
    closed_assessment(a)
    closed_assessment(b)
    cid = "20261127-110000-compare"
    st = state.init(cid, "compare", None or "compare", sources=[a, b])
    assert st["sources"] == [a, b] and set(st["stages"]) == {"S00", "C1", "S16", "S16b", "S17"}
    put(f"x", rid=a)  # source runs stay readable through run:<source-id>/…
    assert paths.resolve(f"run:{a}/analysis.md", run=cid) == rd(a) / "analysis.md"
    walk(["S00", "C1", "S16", "S16b"], rid=cid)
    with pytest.raises(StateError):
        state.close(cid)
    finish("S17", rid=cid)
    assert state.close(cid)[0]["status"] == "closed"


def test_compare_refuses_open_source():
    state.init(RID, "folder", "tiny")
    with pytest.raises(StateError):
        state.init("20261127-110000-compare", "compare", "compare", sources=[RID])


# ---------------------------------------------------------------- retry (#84)

def drift(instance, value=True):
    write_json(rd() / "calibration.json", {"drift": value, "refs": {"addyosmani": {
        "reconciled_total": 57.6, "raw_totals": [57.0, 58.0], "threshold": 2.9, "drift": value,
        "per_scorer": {instance: {"total": 40.0, "delta_reconciled": -17.6, "delta_raw": -17.5,
                                  "agreement_exact_reconciled": 0.4, "agreement_exact_raw": 0.4, "drift": value}}}}})


def test_retry_g2_needs_recorded_drift_and_is_bounded():
    state.init(RID, "folder", "tiny")
    walk(["S00", "S01", "S02", "S04:S1", "S04:S2"])
    with pytest.raises(StateError):
        state.retry(RID, "S04:S1", "G2")          # no calibration.json
    drift("S1", False)
    with pytest.raises(StateError):
        state.retry(RID, "S04:S1", "G2")          # recorded, but no drift
    drift("S1")
    st, opened = state.retry(RID, "S04:S1", "G2")
    assert opened == "S04:S1r"
    assert st["stages"]["S04:S1r"]["declared_outputs"] == ["sealed/S1r/"]
    assert "S04:S1r" in st["stages"]["S05"]["deps"] and "S04:S1" not in st["stages"]["S05"]["deps"]
    assert state.active_instances(st) == ["S1r", "S2"]
    with pytest.raises(StateError):
        state.retry(RID, "S04:S1", "G2")          # one replacement per instance
    drift("S2")
    assert state.retry(RID, "S04:S2", "G2")[1] == "S04:S2r"
    assert "retry G2" in (rd() / "log.md").read_text()


def test_retry_g4_opens_third_scorer_once():
    state.init(RID, "folder", "tiny")
    walk(["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S06"])
    write_json(rd() / "alpha.json", {"alpha": 0.6, "units": 32, "coders": 2, "ci90": [0.4, 0.8],
                                     "small_set": True, "gate": True})
    with pytest.raises(StateError):
        state.retry(RID, "S06", "G4")
    write_json(rd() / "alpha.json", {"alpha": 0.6, "units": 32, "coders": 2, "ci90": [0.4, 0.8],
                                     "small_set": True, "gate": False})
    st, opened = state.retry(RID, "S06", "G4")
    assert opened == "S06b:S3" and st["stages"]["S06b:S3"]["declared_outputs"] == ["sealed/S3/"]
    assert st["stages"]["S06"]["status"] == "pending" and "S06b:S3" in st["stages"]["S06"]["deps"]
    assert state.active_instances(st) == ["S1", "S2", "S3"]
    assert "S06b:S3" in names() and "S06" not in names()
    with pytest.raises(StateError):
        state.retry(RID, "S06", "G4")


@pytest.mark.parametrize("gate,stage,fname,bad", [
    ("G5", "S07", "redteam.json", {"final": [0] * 16, "changes": [], "contests": [], "completed": False}),
    ("G6", "S09", "lens-audit.json", {"checked": {"L4": 30}, "kept": {}, "overrides": {}}),
])
def test_retry_g5_g6_twice_then_refused(gate, stage, fname, bad):
    state.init(RID, "folder", "tiny")
    assess_to(stage)
    for _ in range(2):
        write_json(rd() / fname, bad)
        st, opened = state.retry(RID, stage, gate)
        assert opened == stage and st["stages"][stage]["status"] == "pending"
    with pytest.raises(StateError):
        state.retry(RID, stage, gate)


def test_retry_g7_reopens_report_stages():
    a = "20261127-090000-alpha"
    closed_assessment(a)
    cid = "20261127-110000-compare"
    state.init(cid, "compare", "compare", sources=[a])
    walk(["S00", "C1", "S16", "S16b", "S17"], rid=cid)
    write_json(rd(cid) / "review.json", {"verdict": "pass"})
    with pytest.raises(StateError):
        state.retry(cid, "S16", "G7")
    write_json(rd(cid) / "review.json", {"verdict": "fail"})
    st, _ = state.retry(cid, "S16", "G7")
    assert [st["stages"][s]["status"] for s in ("S16", "S16b", "S17")] == ["pending"] * 3


def test_s07b_activates_only_on_open_contests():
    state.init(RID, "folder", "tiny")
    walk(["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S06"])
    rt = {"final": [2] * 16, "changes": [], "completed": True,
          "contests": [{"c": "C4", "outcome": "to-adjudicator", "evidence": "target:a.md:1"}]}
    put("redteam.json", json.dumps(rt))
    finish("S07")
    assert state.load(RID)["stages"]["S07b"]["status"] == "pending"


# ---------------------------------------------------------------- TTY-only commands (#78)

def test_privileged_commands_refused_without_tty(monkeypatch):
    state.init(RID, "folder", "tiny")
    with pytest.raises(StateError) as e:
        state.reset(RID)
    assert "python3 -m engine state reset --run" in str(e.value)
    with pytest.raises(StateError):
        state.close(RID, force=True)
    from engine import baseline
    with pytest.raises(StateError):
        baseline.promote(RID, ROOT)
    from engine import adjudication
    with pytest.raises(StateError):
        adjudication.import_decisions(RID, "x.json")
    monkeypatch.setenv("MSYSTEM", "MINGW64")
    with pytest.raises(StateError) as e:
        state.reset(RID)
    assert "PowerShell" in str(e.value)


def test_privileged_commands_allowed_on_tty(monkeypatch):
    monkeypatch.setattr(state, "is_interactive", lambda: True)
    monkeypatch.setattr(state, "confirm", lambda prompt, expected: True)
    state.init(RID, "folder", "tiny")
    walk(["S00"])
    assert state.reset(RID)["stages"]["S00"]["status"] == "pending"
    assert state.close(RID, abort=True)[0]["status"] == "closed"


def test_cli_reset_refused_with_devnull_stdin(tmp_path):
    state.init(RID, "folder", "tiny")
    import os
    r = subprocess.run([sys.executable, "-m", "engine", "state", "reset", "--run", RID], cwd=ROOT,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 1 and "interactive terminal" in r.stderr


def test_promote_refusals(monkeypatch, tmp_path):
    from engine import baseline
    monkeypatch.setattr(state, "is_interactive", lambda: True)
    rid = "20261127-120000-superpowers"
    state.init(rid, "reference", "superpowers")
    assess_to("S12", rid=rid)
    state.close(rid)
    write_json(rd(rid) / "target.json", {"pin": "0" * 40})
    with pytest.raises(baseline.PromoteError) as e:
        baseline.promote(rid, ROOT)
    assert "pin mismatch" in str(e.value)
    write_json(rd(rid) / "target.json", {"pin": "22f0b463e7a5e579904dd6211a520321035526f7"})
    with pytest.raises(baseline.PromoteError) as e:
        baseline.promote(rid, ROOT)
    assert "CHANGELOG" in str(e.value)


# ---------------------------------------------------------------- marker, stale, fail-closed

def test_stale_cleanup_marks_failed_and_resets_running():
    state.init(RID, "folder", "tiny")
    state.start(RID, "S00")
    data = paths.data_dir()
    entries = paths.amahome.read_marker(data)
    entries[0]["pid"] = 999999999
    paths.amahome.write_marker(data, entries)
    later = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=25)
    assert [e["run_id"] for e, _ in state.stale_entries(later)] == [RID]
    assert state.stale_entries() == []
    state.cleanup_stale(later)
    st = state.load(RID)
    assert st["status"] == "failed" and st["stages"]["S00"]["status"] == "pending"
    assert paths.amahome.read_marker(data) == []
    assert state.resume(RID)[0]["status"] == "active"
    assert [e["run_id"] for e in paths.amahome.read_marker(data)] == [RID]


def test_fail_closed_ignores_failed_closed_and_waiting():
    data = paths.data_dir()
    for i, status in enumerate(["active", "failed", "closed", "waiting-external"]):
        rid = f"20261127-10000{i}-r{i}"
        state.init(rid, "folder", f"r{i}")
        state.start(rid, "S00")
        st = state.load(rid)
        st["status"] = status
        state.save(st)
    paths.amahome.write_marker(data, [])
    assert paths.amahome.fail_closed_runs(data) == ["20261127-100000-r0"]
    state.marker_add(state.load("20261127-100000-r0"))
    assert paths.amahome.fail_closed_runs(data) == []


def test_waiting_external_leaves_marker_and_resume_rearms():
    state.init(RID, "folder", "tiny")
    state.set_waiting_external(RID)
    assert paths.amahome.read_marker(paths.data_dir()) == []
    assert state.stale_entries() == []
    state.resume(RID)
    assert state.load(RID)["status"] == "active"


def test_list_shows_runs(capsys):
    import argparse
    state.init(RID, "folder", "tiny")
    state._list(argparse.Namespace(cleanup=False))
    assert RID in capsys.readouterr().out


# ---------------------------------------------------------------- engine-owned logs (#85)

def test_log_append_and_answers_append_only():
    state.init(RID, "folder", "tiny")
    req = put("requests/log/log-entry.json", json.dumps({"type": "log-entry", "text": "dispatched S1"}))
    runlog.log_append(RID, "run:requests/log/log-entry.json")
    assert not req.exists()
    first = (rd() / "log.md").read_text()
    put("requests/log/log-entry.json", json.dumps({"type": "log-entry", "text": "dispatched S2"}))
    runlog.log_append(RID, "run:requests/log/log-entry.json")
    text = (rd() / "log.md").read_text()
    assert text.startswith(first) and "dispatched S2" in text
    (rd() / "log.md").write_text("rewritten\n")
    put("requests/log/log-entry.json", json.dumps({"type": "log-entry", "text": "x"}))
    with pytest.raises(runlog.LogError) as e:
        runlog.log_append(RID, "run:requests/log/log-entry.json")
    assert e.value.code == 4
    put("requests/log/answer.json", json.dumps({"type": "answer", "question": "Is X shipped?", "answer": "Yes"}))
    runlog.answers_add(RID, "run:requests/log/answer.json")
    assert "via orchestrator" in (rd() / "owner-answers.md").read_text()
    put("requests/intake/x.json", json.dumps({"type": "log-entry", "text": "x"}))
    with pytest.raises(runlog.LogError):
        runlog.log_append(RID, "run:requests/intake/x.json")


def test_state_json_validates_against_schema():
    from engine.validate import check
    st = state.init(RID, "folder", "tiny")
    assert check("state", st) == []
    assert check("state", read_json(rd() / "state.json")) == []
