"""Task 4.8: dry run of menu option 1 on tests/fixtures/tiny-method/, S00 to S14, then close.

Engine stages run for real, through the CLI. Agent stages are **simulated**: their outputs come from
fixtures (the run-min scorecards, lenses-example.json) or are written by this test, the way the brief's
output contract says. Every Bash call and every agent write goes through hooks/guard.py first, with the
run's marker live, and must be allowed: the replay of the run gives zero denials.
"""
import importlib.util
import json
import os
import pathlib
import shlex
import shutil

import pytest

from engine import cli, state
from engine.common import CRITERIA
from engine.validate import check

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RID = "20261127-101500-tiny"
_spec = importlib.util.spec_from_file_location("_dry_guard", ROOT / "hooks" / "guard.py")
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

SCHEMA_OF = {"target.json": "target", "reconciled.json": "reconciled", "alpha.json": "alpha",
             "calibration.json": "calibration", "audit_scope.json": "audit-scope", "redteam.json": "redteam",
             "lenses.json": "lenses", "lens-audit.json": "lens-audit", "tokens.json": "tokens",
             "results.json": "results", "state.json": "state"}


class Run:
    def __init__(self, home):
        self.home, self.rd, self.calls, self.denials = home, home / "runs" / RID, [], []

    def _guard(self, tool, **ti):
        hook = {"tool_name": tool, "tool_input": ti, "cwd": str(ROOT), "hook_event_name": "PreToolUse"}
        code, msg = guard.decide(json.dumps(hook), env=dict(os.environ))
        self.calls.append({"tool": tool, **ti})
        if code != 0:
            self.denials.append((tool, ti, msg))

    def eng(self, *argv):
        self._guard("Bash", command="python3 -m engine " + " ".join(shlex.quote(a) for a in argv))
        code = cli.main(list(argv))
        assert code == 0, argv

    def write(self, rel, content):
        p = self.rd / rel
        self._guard("Write", file_path=str(p))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else json.dumps(content, indent=2), encoding="utf-8")

    def read(self, rel):
        self._guard("Read", file_path=str(self.rd / rel))
        return (self.rd / rel).read_text(encoding="utf-8")

    def stage(self, s, *outputs):
        self.eng("state", "start", "--run", RID, "--stage", s, "--host", "dry-run", "--model", "simulated")
        return lambda: self.eng("state", "done", "--run", RID, "--stage", s, *(["--outputs", *outputs] if outputs else []))


def lenses(l2=None):
    obj = json.loads((FIX / "lenses-example.json").read_text(encoding="utf-8"))
    text = json.dumps(obj).replace("cache:tiny/", "target:")
    obj = json.loads(text)
    if l2 is False:
        obj["L2"] = None
    return obj


@pytest.fixture
def run(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)
    return Run(pathlib.Path(os.environ["AMA_HOME"]))


def test_dry_run_tiny_method(run, tmp_path):
    src = tmp_path / "tiny-method"
    shutil.copytree(FIX / "tiny-method", src)
    r = run
    r.eng("state", "init", "--run", RID, "--mode", "folder", "--slug", "tiny", "--python", "python3",
          "--scorer-model", "simulated-model")
    assert guard._load_amahome().read_marker(r.home), "state init arms the guard"

    done = r.stage("S00"); r.eng("verify-freeze"); done()

    done = r.stage("S01")
    r.write("requests/intake/intake-request.json", {"mode": "folder", "source": str(src), "slug": "tiny",
                                                     "name": "Tiny Method", "status": "implemented"})
    r.eng("intake", "--run", RID, "--request", "run:requests/intake/intake-request.json")
    r.eng("inventory", "--root", "target:", "--run", RID)
    r.write("boundary.md", "| path | reason | on R's path? |\n|---|---|---|\n| target:templates/ | kept: spec template | yes |\n")
    r.write("off_limits.txt", "")
    done()

    done = r.stage("S02", "off_limits.txt", "audit_seed"); r.eng("isolate", "--run", RID); done()

    done = r.stage("S03")
    r.read("target:README.md".replace("target:", "target/"))
    r.write("trace.md", "## Entry point\ntarget:README.md:5\n## Route for R\nsingle route\n## Steps\n"
            "1. plan target:skills/plan/SKILL.md:1\n## Reference host\nsimulated\n## Contestable readings\nnone\n")
    done()

    # S08a runs in parallel with S04-S07
    done_8a = r.stage("S08a"); r.write("lenses.json", lenses(l2=False)); done_8a()

    d1, d2 = r.stage("S04:S1"), r.stage("S04:S2")
    r.eng("shuffle", "--seed", "20261127-S1")
    for inst in ("S1", "S2"):     # S2 agrees with S1 except one cell one level lower, so gate G4 passes
        for f in ("cal-addyosmani.md", "target.md"):
            text = (FIX / "run-min" / "sealed" / "S1" / f).read_text(encoding="utf-8")
            if inst == "S2":
                text = text.replace('"scorer": "S1"', '"scorer": "S2"').replace(
                    '"target:skills/plan/SKILL.md:12"\n      ],\n      "conf": "M",\n      "ev": "I",\n'
                    '      "first_unmet": "synthetic",\n      "s": 1', '"target:skills/plan/SKILL.md:12"\n      ],\n'
                    '      "conf": "M",\n      "ev": "I",\n      "first_unmet": "synthetic",\n      "s": 0')
            r.write(f"sealed/{inst}/{f}", text)
    d1(); d2()

    done = r.stage("S05")
    for inst in ("S1", "S2"):
        r.eng("scorecard", "check", str(r.rd / "sealed" / inst / "target.md"))
    r.eng("calibration", "--run", RID)
    done()

    done = r.stage("S06", "alpha.json")
    r.eng("reconcile", "pre", "--run", RID)
    pre = json.loads(r.read("reconcile-pre.json"))
    cells, vec = {}, []
    for c in CRITERIA:
        cell = pre["cells"][c]
        s = cell["proposed"] if cell["proposed"] is not None else sorted(cell["scores"].values())[0]
        rule = "equal" if cell["diff"] == 0 else "lower" if cell["diff"] == 1 else "median-down"
        vec.append(s)
        cells[c] = {"s": s, "r": 1.0, "r_rule": "n/a", "conf": cell["conf_worst"], "rule": rule, "note": "simulated",
                    "cites": ["target:skills/plan/SKILL.md:1"]}
    r.write("reconciled.json", {"vector": vec, "r": [1.0] * 16, "ra": [float(v) for v in vec], "cells": cells,
                                "route": {"agreed": True, "route": "single route", "note": "simulated"}})
    r.write("reconciliation.md", "No written reconciliations (simulated).\n")
    r.eng("alpha", "--run", RID)
    done()

    done = r.stage("S07")
    r.eng("audit-scope", "--run", RID)
    r.write("redteam.json", {"final": vec, "final_r": [1.0] * 16, "r_independent": [1.0] * 16, "boundary": [],
                             "changes": [], "contests": [], "completed": True})
    r.write("audit-log.md", "No contests upheld (simulated).\n")
    done()
    assert state.load(RID)["stages"]["S07b"]["status"] == "skipped"

    done = r.stage("S08b"); r.write("lenses.json", lenses()); done()

    done = r.stage("S09")
    r.write("lens-audit.json", {"checked": {"L2": 1, "L3": 1, "L4": 34, "L5": 3}, "kept": {"L2": 1, "L3": 1, "L4": 34, "L5": 3},
                                "overrides": {}, "L5_corrections": {}, "L1_observations": [], "log": []})
    done()

    done = r.stage("S10"); r.eng("apply-audit", "--run", RID); r.eng("tokens", "--run", RID); done()
    done = r.stage("S11"); r.eng("consolidate", "--run", RID); done()
    done = r.stage("S12")
    r.eng("rank", "--run", RID); r.eng("sensitivity", "--run", RID, "--draws", "200")
    r.eng("superiority", "--run", RID)
    done()

    # every JSON the run produced is schema-valid
    checked = 0
    for p in sorted(r.rd.glob("*.json")):
        kind = SCHEMA_OF.get(p.name)
        if kind:
            assert check(kind, json.loads(p.read_text(encoding="utf-8"))) == [], p.name
            checked += 1
    assert checked == len(SCHEMA_OF), checked
    for f in ("results.json", "ranking.json", "sensitivity.json", "superiority.json", "tokens.json"):
        assert (r.rd / f).is_file(), f

    done = r.stage("S13"); r.eng("lineage", "--run", RID); r.write("lineage.md", "No lineage found (simulated).\n"); done()
    done = r.stage("S14"); r.write("analysis.md", "# Analysis (simulated)\n<!-- done:card -->\n"); done()
    r.write("requests/log/log-entry.json", {"type": "log-entry", "text": "dry run complete"})
    r.eng("log", "append", "--run", RID, "--text-request", "run:requests/log/log-entry.json")

    st = state.load(RID)
    assert all(v["status"] in ("done", "skipped") for v in st["stages"].values())
    r.eng("state", "close", "--run", RID)
    assert not guard._load_amahome().read_marker(r.home), "close releases the guard"
    assert r.denials == [], r.denials
    assert len([c for c in r.calls if c["tool"] == "Bash"]) > 40
