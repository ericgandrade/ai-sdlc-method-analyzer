"""§10.1: `engine setup` merges host settings and records exactly what it added."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

from engine import setup as S

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def data():
    return pathlib.Path(os.environ["AMA_HOME"])


def proj(tmp_path, name="clone", settings=None):
    p = tmp_path / name
    (p / ".claude").mkdir(parents=True)
    if settings is not None:
        (p / ".claude" / "settings.local.json").write_text(
            settings if isinstance(settings, str) else json.dumps(settings), encoding="utf-8")
    return p


def settings(p):
    return json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))


FOREIGN = {"model": "x", "permissions": {"allow": ["Bash(make test)"], "deny": ["Read(./secret)"],
                                          "additionalDirectories": ["/other"]}, "env": {"A": "1"}}


def test_merge_keeps_foreign_keys_and_rules(tmp_path, data):
    p = proj(tmp_path, settings=FOREIGN)
    S.setup(p, data)
    s = settings(p)
    assert s["model"] == "x" and s["env"] == {"A": "1"} and s["permissions"]["deny"] == ["Read(./secret)"]
    assert s["permissions"]["allow"][0] == "Bash(make test)"
    assert "/other" in s["permissions"]["additionalDirectories"] and str(data) in s["permissions"]["additionalDirectories"]
    assert "Bash(python3 -m engine *)" in s["permissions"]["allow"]
    assert (p / ".claude" / "settings.local.json.bak").exists()


def test_rerun_is_idempotent(tmp_path, data):
    p = proj(tmp_path)
    S.setup(p, data)
    first = settings(p)
    S.setup(p, data)
    assert settings(p) == first
    for k, v in first["permissions"].items():
        assert len(v) == len(set(v))


def test_only_plain_strings_are_inserted(tmp_path, data):
    p = proj(tmp_path, settings=FOREIGN)
    S.setup(p, data)
    s = settings(p)
    assert set(s) == set(FOREIGN)
    assert set(s["permissions"]) == set(FOREIGN["permissions"])
    for k in ("allow", "additionalDirectories"):
        assert all(isinstance(x, str) for x in s["permissions"][k])


def test_remove_deletes_exactly_the_recorded_strings(tmp_path, data):
    p = proj(tmp_path, settings=FOREIGN)
    S.setup(p, data)
    S.remove(p, data)
    assert settings(p) == FOREIGN


def test_preexisting_identical_rule_is_not_ours(tmp_path, data):
    pre = {"permissions": {"allow": ["Bash(python3 -m engine *)"]}}
    p = proj(tmp_path, settings=pre)
    S.setup(p, data)
    S.remove(p, data)
    assert settings(p) == pre


def test_invalid_json_is_untouched(tmp_path, data):
    p = proj(tmp_path, settings="{broken")
    with pytest.raises(S.SetupError) as e:
        S.setup(p, data)
    assert e.value.code == 1
    assert (p / ".claude" / "settings.local.json").read_text() == "{broken"


def test_non_string_array_is_refused(tmp_path, data):
    p = proj(tmp_path, settings={"permissions": {"allow": [{"x": 1}]}})
    with pytest.raises(S.SetupError):
        S.setup(p, data)


def test_check_ok_then_stale_path(tmp_path, data):
    p = proj(tmp_path)
    assert S.check(p, data) == ["engine setup has not been run for this clone"]
    S.setup(p, data)
    assert S.check(p, data, env={}) == []
    other = tmp_path / "moved-home"
    rec = json.loads((data / "setup-record.json").read_text())
    (other).mkdir()
    (other / "setup-record.json").write_text(json.dumps(rec))
    assert any("re-run" in m for m in S.check(p, other, env={}))


def test_check_detects_missing_rules(tmp_path, data):
    p = proj(tmp_path)
    S.setup(p, data)
    s = settings(p)
    s["permissions"]["allow"] = []
    (p / ".claude" / "settings.local.json").write_text(json.dumps(s))
    assert S.check(p, data, env={})


def test_check_detects_pythonsafepath(tmp_path, data):
    p = proj(tmp_path)
    S.setup(p, data)
    assert any("PYTHONSAFEPATH" in m for m in S.check(p, data, env={"PYTHONSAFEPATH": "1"}))


def test_two_clones_keep_separate_records(tmp_path, data):
    a, b = proj(tmp_path, "a"), proj(tmp_path, "b")
    S.setup(a, data)
    S.setup(b, data)
    rec = json.loads((data / "setup-record.json").read_text())
    assert len(rec["projects"]) == 2
    S.remove(a, data)
    assert S.check(b, data, env={}) == []
    assert settings(a).get("permissions", {}).get("allow", []) == []


def test_refused_while_a_run_is_active(tmp_path, data):
    p = proj(tmp_path)
    (data / "guard").mkdir(parents=True)
    (data / "guard" / "active.json").write_text(json.dumps({"runs": [{"run_id": "20261127-101500-x"}]}))
    with pytest.raises(S.SetupError):
        S.setup(p, data)


def test_rules_have_no_relative_or_foreign_bash(tmp_path, data):
    want = S.desired(data, "py -3")
    bash = [r for r in want["allow"] if r.startswith("Bash(")]
    assert bash == ["Bash(py -3 -m engine *)"]


def test_cli_check_exit_3_without_setup(data):
    r = subprocess.run([sys.executable, "-m", "engine", "setup", "--check"], cwd=ROOT, capture_output=True,
                       text=True, env=dict(os.environ))
    assert r.returncode == 3 and "engine setup" in r.stdout


def test_committed_settings_are_portable():
    from engine.paths import assert_portable
    for f in (ROOT / ".claude" / "settings.json", ROOT / "hooks" / "hooks.json"):
        assert_portable(json.loads(f.read_text(encoding="utf-8")))
