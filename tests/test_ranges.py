"""ranges, documentation-only (plan §7.13; Task 2.14). The vectors are invented for the test."""
import pathlib

import pytest

from engine import ranges, state
from engine.cli import main
from engine.common import FEATURES
from engine.jsonio import read_json, write_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
RID = "20261127-101500-docsy"
C = [f"C{i}" for i in range(1, 17)]
FLOOR = [2, 2, 3, 2, 3, 2, 1, 2, 2, 2, 1, 1, 3, 2, 2, 1]
CEIL = [3, 3, 4, 3, 4, 3, 2, 2, 3, 3, 2, 2, 4, 3, 3, 2]
DOCS = {"name": "Docs sample", "evidence": "D", "type_declaration": "closed", "L1_floor": FLOOR, "L1_ceiling": CEIL,
        "conf": {c: ("M" if i % 2 else "L") for i, c in enumerate(C)}, "L3": "A2",
        "L4": {f: {"v": "NA" if f == "F21" else 1, "cite": "docs:a.md#p1"} for f in FEATURES},
        "not_assessable": [], "needed": []}


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)


def docs_run(docs=DOCS):
    state.init(RID, "docs", "docsy")
    write_json(state.run_path(RID) / "docs-only.json", docs)


def bench():
    res = read_json(ROOT / "baseline" / "rounds" / "2026-11" / "derived" / "results.json")
    return {m: e["L1"] for m, e in res.items() if e["benchmark"]}


def test_golden_floor_centre_ceiling():
    rng, mid, u = ranges.compute(DOCS, bench())
    assert rng["floor"]["totals"]["baseline"] == 40.6
    assert rng["ceiling"]["totals"]["baseline"] == 59.4
    assert rng["centre"]["totals"]["baseline"] == 50.0
    assert all(rng["centre"]["totals"][p] == round((rng["floor"]["totals"][p] + rng["ceiling"]["totals"][p]) / 2, 1)
               for p in rng["centre"]["totals"])
    assert u[0] == 1.0 and u[1] == 0.5


def test_positions_against_the_nine_references():
    rng, _, _ = ranges.compute(DOCS, bench())
    assert len(rng["against"]) == 9
    # baseline: floor 40.6 is above openspec only (38.8); ceiling 59.4 is below ai-dlc, agile-v, bmad
    assert rng["floor"]["position"]["baseline"] == 9
    assert rng["ceiling"]["position"]["baseline"] == 4
    assert rng["centre"]["position"]["baseline"] == 6


def test_cap_violation_gives_exit_1(capsys):
    docs_run(dict(DOCS, type_declaration="open-unread"))      # cap 3, ceiling has 4s
    assert main(["ranges", "--run", RID]) == 1
    assert "cap" in capsys.readouterr().err


def test_no_cell_may_be_5_and_conf_is_never_h():
    bad = dict(DOCS, L1_ceiling=[5] + CEIL[1:], conf=dict(DOCS["conf"], C2="H"))
    msgs = ranges.cap_violations(bad)
    assert any("C1" in m for m in msgs) and any("conf C2" in m for m in msgs)


def test_cli_writes_range_into_results(capsys):
    docs_run()
    assert main(["ranges", "--run", RID]) == 0
    e = read_json(state.run_path(RID) / "results.json")["docsy"]
    assert e["range"]["centre"]["totals"]["baseline"] == 50.0 and e["L4_na"] == ["F21"]
    assert "centre 50.0" in capsys.readouterr().out
