"""Task 4.2: the PreToolUse guard, fed stdin JSON fixtures."""
import ast
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUARD = ROOT / "hooks" / "guard.py"
RID = "20261127-101500-tiny"
SRC = "20261126-090000-tiny"

_spec = importlib.util.spec_from_file_location("_test_guard", GUARD)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


@pytest.fixture
def home():
    return pathlib.Path(os.environ["AMA_HOME"])


def make_run(home, rid=RID, running=(), done=(), status="active", python="python3", sources=(),
             mode="folder", marker=True, outputs=None):
    from engine import state
    table = state.stage_table(mode if mode in state.MODES else "folder")
    for k in table:
        table[k]["status"] = "done" if k in done else ("running" if k in running else table[k]["status"])
    for k, v in (outputs or {}).items():
        table[k]["declared_outputs"] = v
    rd = home / "runs" / rid
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "state.json").write_text(json.dumps({"run_id": rid, "status": status, "python": python, "mode": mode,
                                               "sources": list(sources), "stages": table}), encoding="utf-8")
    if marker:
        m = home / "guard" / "active.json"
        m.parent.mkdir(parents=True, exist_ok=True)
        entries = json.loads(m.read_text())["runs"] if m.exists() else []
        entries.append({"run_id": rid, "started": "x", "state_path": f"runs/{rid}/state.json", "pid": 1, "host": "h"})
        m.write_text(json.dumps({"runs": entries}), encoding="utf-8")
    return rd


def decide(tool, env=None, cwd=None, **tool_input):
    e = dict(os.environ)
    e.update(env or {})
    hook = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or ROOT), "hook_event_name": "PreToolUse"}
    return guard.decide(json.dumps(hook), env=e)


def bash(cmd, **kw):
    return decide("Bash", command=cmd, **kw)[0]


# ------------------------------------------------------------------ outside a run

def test_without_a_marker_everything_is_allowed(home):
    assert bash("rm -rf runs") == 0
    assert decide("Write", file_path=str(ROOT / "README.md"))[0] == 0
    assert decide("WebFetch", url="https://example.org")[0] == 0


def test_waiting_external_run_is_not_fail_closed(home):
    make_run(home, running=("S07b",), status="waiting-external", marker=False)
    assert bash("git status") == 0


def test_orphaned_running_stage_fails_closed(home):
    make_run(home, running=("S05",), marker=False)
    code, msg = decide("Bash", command="python3 -m engine state list")
    assert code == 2 and "engine state list" in msg
    assert decide("Write", file_path=str(home / "runs" / RID / "trace.md"))[0] == 2
    assert decide("Read", file_path=str(ROOT / "README.md"))[0] == 0


def test_corrupt_marker_fails_closed(home):
    (home / "guard").mkdir(parents=True)
    (home / "guard" / "active.json").write_text("{not json", encoding="utf-8")
    assert bash("python3 -m engine state list") == 2


@pytest.mark.parametrize("stdin, active, expected", [("not json", True, 2), ("[]", True, 2),
                                                     ("not json", False, 0)])
def test_subprocess_fail_closed_exits_2_never_1(home, stdin, active, expected):
    if active:
        make_run(home)
    r = subprocess.run([sys.executable, str(GUARD)], input=stdin, capture_output=True, text=True,
                       env=dict(os.environ), cwd=ROOT)
    assert r.returncode == expected


def test_subprocess_allows_and_denies(home):
    make_run(home)
    for cmd, code in [("python3 -m engine state next --run " + RID, 0), ("ls", 2)]:
        hook = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(ROOT)})
        r = subprocess.run([sys.executable, str(GUARD)], input=hook, capture_output=True, text=True,
                           env=dict(os.environ), cwd=ROOT)
        assert r.returncode == code, r.stderr


def test_guard_keeps_old_python_syntax():
    for f in (GUARD, ROOT / "hooks" / "amahome.py"):
        ast.parse(f.read_text(encoding="utf-8"), feature_version=(3, 8))


def test_subcommand_list_matches_the_engine():
    from engine import cli
    assert guard.SUBCOMMANDS == frozenset(cli.COMMANDS)


# ------------------------------------------------------------------ Bash while active

DENIED = [
    "python .cache/refs/x/run.py", "bash runs/r/target/install.sh", "node target/x.js", "npm test", "npx x",
    "curl https://example.org", "wget https://example.org", "git push", "make", "perl -e 1",
    "python3 -c 1", "python -m engine state list",
    "find . -exec rm {} \\;", "find . -execdir x", "find . -ok x", "find . -delete", "find . -fprint x",
    "python3 -m engine list run:x > /tmp/out", "python3 -m engine list run:x >> f",
    "python3 -m engine list run:x 2> f", "python3 -m engine list run:x &> f",
    "python3 -m engine read target:a <<EOF", "python3 -m engine list run:x\nrm -rf y",
    "python3 -m engine list run:x\rrm -rf y", "pdftotext in.pdf out.txt",
    "git -c core.pager=x -C cache:a log", "git diff --output=x", "git diff --ext-diff",
    "PYTHONPATH=runs/r/target python3 -m engine tokens", "python3 -m engine notacommand",
    "cd /tmp && python3 -m engine state list", "python3 -m engine x; rm y", "`cmd`", "echo $(id)",
    "python3 -m engine", "python3 engine", "FOO=1 python3 -m engine state list",
    f"python3 -m engine state close --run {RID} --abort", f"python3 -m engine state close --run {RID} --force",
    f"python3 -m engine state reset --run {RID}", f"python3 -m engine adjudication import --run {RID} f.md",
    f"python3 -m engine baseline promote --run {RID}", "python3 -m engine setup",
    "python3 -m engine setup --check", "python3 -m engine report --run x --copy-to exported",
]


@pytest.mark.parametrize("cmd", DENIED)
def test_bash_denied_while_active(home, cmd):
    make_run(home)
    assert bash(cmd) == 2


ALLOWED = [
    f"python3 -m engine state next --run {RID}",
    '"python3" -m engine inventory --root "cache:a b/c"',
    "python3 -m engine read \"cache:x/Library/Application Support/y.md\"",
    f"python3 -m engine state close --run {RID}",
    "python3 -m engine log append --run x --text-request run:requests/log/log-entry.json",
]


@pytest.mark.parametrize("cmd", ALLOWED)
def test_bash_allowed_while_active(home, cmd):
    make_run(home)
    assert bash(cmd) == 0


def test_guard_path_in_a_command_is_denied(home):
    make_run(home)
    assert bash(f'python3 -m engine read "{home / "guard" / "active.json"}"') == 2


def test_cwd_must_be_the_project_root(home, tmp_path):
    make_run(home)
    assert bash("python3 -m engine state list", cwd=tmp_path) == 2
    assert bash("python3 -m engine state list", cwd=home / "runs" / RID) == 2


def test_recorded_interpreter_is_matched_exactly(home):
    make_run(home, python="py -3")
    assert bash("py -3 -m engine state list") == 0
    assert bash("python3 -m engine state list") == 2


def test_pythonpath_must_equal_the_plugin_root(home):
    make_run(home)
    env = {"CLAUDE_PLUGIN_ROOT": str(ROOT)}
    assert bash(f'"PYTHONPATH={ROOT}" python3 -m engine tokens --run {RID}', env=env) == 0
    assert bash("PYTHONPATH=runs/r/target python3 -m engine tokens", env=env) == 2
    assert bash(f"PYTHONPATH={ROOT} python3 -m engine tokens") == 2         # no plugin root set


def test_terminal_refusal_prints_the_command(home, monkeypatch):
    make_run(home)
    code, msg = decide("Bash", command=f"python3 -m engine state reset --run {RID}")
    assert code == 2 and f"python3 -m engine state reset --run {RID}" in msg
    monkeypatch.setenv("MSYSTEM", "MINGW64")
    assert "PowerShell" in decide("Bash", command=f"python3 -m engine state reset --run {RID}")[1]


def test_copy_to_allowed_for_exports_allow(home, tmp_path):
    make_run(home)
    out = tmp_path / "exported"
    (home / "config.json").write_text(json.dumps({"exports": {"allow": [str(out)]}}), encoding="utf-8")
    assert bash(f'python3 -m engine report --run {RID} --copy-to "{out}"') == 0
    assert bash(f'python3 -m engine report --run {RID} --copy-to "{tmp_path / "other"}"') == 2


def test_web_tools_denied_while_active(home):
    make_run(home)
    assert decide("WebFetch", url="https://example.org")[0] == 2
    assert decide("Task", prompt="x")[0] == 0


# ------------------------------------------------------------------ writes while active

def w(home, rel, tool="Write", rid=RID):
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return decide(tool, **{key: str(home / "runs" / rid / rel)})[0]


@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit", "NotebookEdit"])
def test_declared_output_of_running_stage_only(home, tool):
    make_run(home, running=("S03",), done=("S00", "S01", "S02"))
    assert w(home, "trace.md", tool) == 0
    assert w(home, "lenses.json", tool) == 2
    assert w(home, "state.json", tool) == 2


@pytest.mark.parametrize("rel", ["state.json", "log.md", "owner-answers.md", "results.json", "ranking.json",
                                 "reconcile-pre.json", "calibration.json", "alpha.json", "pristine/trace.md"])
def test_engine_owned_files_never_writable(home, rel):
    make_run(home, running=("S03",), outputs={"S03": [rel]})
    assert w(home, rel) == 2


def test_writes_outside_runs_denied(home):
    make_run(home, running=("S03",))
    assert decide("Write", file_path=str(ROOT / "baseline" / "x.json"))[0] == 2
    assert decide("Write", file_path=str(ROOT / "README.md"))[0] == 2
    assert decide("Edit", file_path=str(home / "guard" / "active.json"))[0] == 2


def test_per_instance_sealed_scope(home):
    make_run(home, running=("S04:S1",), done=("S00", "S01", "S02"))
    assert w(home, "sealed/S1/target.md") == 0
    assert w(home, "sealed/S2/target.md") == 2


def test_sealed_after_done_and_r_independent_after_s07r(home):
    make_run(home, done=("S04:S1", "S07r"), running=("S08a",))
    assert w(home, "sealed/S1/target.md") == 2
    assert w(home, "r_independent.json") == 2


def test_request_folders(home):
    make_run(home, running=("S01",), done=("S00",))
    assert w(home, "requests/intake/intake-request.json") == 0
    assert w(home, "requests/log/log-entry.json") == 0
    make_run(home, rid="20261127-101501-tiny", done=("S00", "S01"), running=("S03",))
    assert w(home, "requests/intake/intake-request.json", rid="20261127-101501-tiny") == 2
    assert w(home, "requests/log/log-entry.json", rid="20261127-101501-tiny") == 0


def test_report_folder_only_during_s16(home):
    make_run(home, mode="compare", running=("S16",))
    assert decide("Write", file_path=str(home / "reports" / RID / "report.html"))[0] == 0
    make_run(home, rid="20261127-101501-tiny", mode="compare", running=("S17",))
    assert decide("Write", file_path=str(home / "reports" / "20261127-101501-tiny" / "x.md"))[0] == 2


def test_source_runs_are_read_only(home):
    make_run(home, rid=SRC, status="closed", marker=False)
    make_run(home, mode="compare", sources=[SRC], running=("C1",))
    assert decide("Read", file_path=str(home / "runs" / SRC / "results.json"))[0] == 0
    assert decide("Write", file_path=str(home / "runs" / SRC / "results.json"))[0] == 2


def test_two_concurrent_runs(home):
    make_run(home, running=("S03",))
    make_run(home, rid="20261127-101501-tiny", running=("S13",))
    assert w(home, "trace.md") == 0
    assert w(home, "lineage.md", rid="20261127-101501-tiny") == 0
    assert w(home, "lineage.md") == 2


# ------------------------------------------------------------------ reads while active

def r(home, rel, tool="Read"):
    key = "file_path" if tool == "Read" else "path"
    return decide(tool, **{key: str(home / "runs" / RID / rel)})[0]


def test_reads_in_active_run_project_and_cache(home, tmp_path):
    make_run(home, running=("S08a",))
    assert r(home, "trace.md") == 0
    assert decide("Read", file_path=str(ROOT / "rules" / "fairness.md"))[0] == 0
    assert decide("Grep", path=str(home / "cache" / "refs" / "x"), pattern="a")[0] == 0
    assert decide("Read", file_path=str(tmp_path / "elsewhere.txt"))[0] == 2
    make_run(home, rid="20261127-000000-other", status="closed", marker=False)
    assert decide("Read", file_path=str(home / "runs" / "20261127-000000-other" / "results.json"))[0] == 2


def test_s07r_read_denial(home):
    make_run(home, running=("S07r",), done=("S06",))
    for rel in ("reconciled.json", "reconcile-pre.json", "sealed/S1/target.md", "sealed/S2/target.json",
                "pristine/reconciled.json"):
        assert r(home, rel) == 2, rel
    assert r(home, "reconciled-blind.json") == 0
    assert r(home, "boundary.md") == 0
    assert r(home, "", tool="Grep") == 2
    assert r(home, "sealed", tool="Glob") == 2
    assert r(home, "target", tool="Grep") == 0


def test_s07r_denial_only_while_running(home):
    make_run(home, done=("S06",))
    assert r(home, "reconciled.json") == 0
