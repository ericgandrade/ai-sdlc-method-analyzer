"""Scorecard machine block: extract and check (plan §7.6, §7.7; Task 2.7)."""
import json
import pathlib
import subprocess
import sys

import pytest

from engine import scorecard
from engine.scorecard import ScorecardError

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARD = ROOT / "tests" / "fixtures" / "run-min" / "sealed" / "S1" / "target.md"


def test_extract_takes_the_last_json_block(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("```json\n{\"first\": 1}\n```\n\ntext\n\n```json\n{\"last\": 2}\n```\n")
    assert scorecard.extract(f) == {"last": 2}
    assert scorecard.extract(CARD)["scorer"] == "S1"


def test_extract_cli(tmp_path):
    out = tmp_path / "c.json"
    r = subprocess.run([sys.executable, "-m", "engine", "scorecard", "extract", str(CARD), "-o", str(out)],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and json.loads(out.read_text())["method"] == "tiny"


def test_no_block_is_an_error(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("no block\n")
    with pytest.raises(ScorecardError):
        scorecard.extract(f)


def mutate(tmp_path, fn):
    card = scorecard.extract(CARD)
    fn(card)
    f = tmp_path / "c.md"
    f.write_text("```json\n" + json.dumps(card) + "\n```\n")
    return f


def check(f, *extra):
    return subprocess.run([sys.executable, "-m", "engine", "scorecard", "check", str(f), *extra], cwd=ROOT,
                          capture_output=True, text=True)


def test_check_valid_fixture():
    assert check(CARD).returncode == 0


def test_schema_failure_on_missing_c7(tmp_path):
    r = check(mutate(tmp_path, lambda c: c["scores"].pop("C7")))
    assert r.returncode == 1 and "C7" in r.stderr


def test_s_evidence_with_3_is_an_error(tmp_path):
    def f(c):
        c["scores"]["C3"].update(ev="S", s=3)
    assert check(mutate(tmp_path, f)).returncode == 1


def test_caps_warn_by_default_and_fail_with_type(tmp_path):
    def f(c):
        c["scores"]["C2"].update(ev="D", s=4)
    p = mutate(tmp_path, f)
    r = check(p)
    assert r.returncode == 0 and "warning" in r.stdout
    assert check(p, "--type", "open").returncode == 1
    assert check(p, "--type", "closed").returncode == 0
