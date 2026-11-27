"""No-network guarantee (plan §0.3, §7.1; Task 2.18).

`socket.socket` is patched to record the attempt and raise. Every command of the CLI is then run
in-process on the fixtures. Only `fetch` and `intake --mode git` may need the network, and both
must exit 6 with `--offline`. Every other command must exit 0 or one of its documented codes
(§0.3) without touching a socket. Unbuilt commands exit 2 ("not implemented").
"""
import pathlib
import shutil
import socket

import pytest

from engine import cli, state
from engine.common import FEATURES
from engine.jsonio import write_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RID = "20261127-101500-tiny"
VEC = [2, 3, 3, 3, 2, 2, 2, 1, 2, 2, 2, 1, 3, 2, 3, 1]
DOCUMENTED = {0, 1, 2, 3, 4, 5, 6}
NETWORK = {"fetch", "intake"}


class Blocked(OSError):
    pass


@pytest.fixture
def no_socket(monkeypatch):
    attempts = []

    class NoSocket:
        def __init__(self, *a, **k):
            attempts.append(a)
            raise Blocked("network access attempted")

    monkeypatch.setattr(socket, "socket", NoSocket)
    monkeypatch.setattr(socket, "create_connection", NoSocket)
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)
    return attempts


def prepared_run():
    state.init(RID, "folder", "tiny")
    rd = state.run_path(RID)
    shutil.copytree(FIX / "run-min" / "sealed", rd / "sealed")
    shutil.copytree(FIX / "tiny-method", rd / "target")
    cells = {f"C{i + 1}": {"s": v, "conf": "M", "rule": "equal"} for i, v in enumerate(VEC)}
    write_json(rd / "reconciled.json", {"vector": VEC, "cells": cells, "route": {"agreed": True}})
    write_json(rd / "l1.final.json", {"vector": VEC, "r": None, "ra": None, "source": "reconciled.vector",
                                      "adjudicated": [], "boundary": []})
    write_json(rd / "lenses.json", {"L2": None, "L3": {"level": "A2", "conf": "M"},
                                    "L4": {f: {"v": 1} for f in FEATURES},
                                    "L5": {"T1": [], "T2": [], "T3": [], "T0_root": "target:"}})
    shutil.copy(rd / "lenses.json", rd / "lenses.final.json")
    write_json(rd / "redteam.json", {"final": VEC, "contests": [], "changes": [], "completed": True})
    return rd


def argv_for(name, tmp):
    leak = str(FIX / "leaks" / "near-miss.txt")
    card = str(FIX / "run-min" / "sealed" / "S1" / "target.md")
    table = {
        "fetch": ["fetch", "--slug", "bmad", "--offline"],
        "intake": ["intake", "--run", "20261127-121500-gitty", "--mode", "git", "--source",
                   "https://example.invalid/x.git", "--slug", "gitty", "--offline"],
        "isolate": ["isolate", "--run", RID],
        "inventory": ["inventory", "--root", "target:", "--run", RID],
        "shuffle": ["shuffle", "--seed", "1"],
        "validate": ["validate", "registry"],
        "scorecard": ["scorecard", "check", card],
        "calibration": ["calibration", "--run", RID],
        "reconcile": ["reconcile", "pre", "--run", RID],
        "alpha": ["alpha", "--run", RID],
        "audit-scope": ["audit-scope", "--run", RID],
        "apply-audit": ["apply-audit", "--run", RID],
        "tokens": ["tokens", "--run", RID],
        "consolidate": ["consolidate", "--run", RID],
        "rank": ["rank", "--run", RID],
        "sensitivity": ["sensitivity", "--run", RID, "--draws", "50"],
        "superiority": ["superiority", "--run", RID],
        "ranges": ["ranges", "--run", RID],
        "lineage": ["lineage", "--run", RID],
        "fitgap": ["fitgap", "--run", RID],
        "leakcheck": ["leakcheck", "--path", leak, "--ci"],
        "state": ["state", "next", "--run", RID],
        "baseline": ["baseline", "verify"],
        "verify-freeze": ["verify-freeze"],
        "tty-check": ["tty-check"],
        "log": ["log", "append", "--run", RID, "--text-request", "run:requests/log/none.json"],
        "answers": ["answers", "add", "--run", RID, "--request", "run:requests/log/none.json"],
        "estimate": ["estimate", "--source", str(FIX / "tiny-method")],
        "adjudication": ["adjudication", "request", "--run", RID],
        "hooks": ["hooks"],
    }
    return table.get(name, [name])


def run_cli(argv):
    try:
        return cli.main(argv)
    except SystemExit as e:                 # argparse usage errors
        return e.code if isinstance(e.code, int) else 2


@pytest.mark.parametrize("name", sorted(cli.COMMANDS))
def test_every_command_runs_without_the_network(name, no_socket, tmp_path, monkeypatch):
    if name == "intake":
        state.init("20261127-121500-gitty", "git", "gitty")
    prepared_run()
    if name == "fetch":
        monkeypatch.delenv("AMA_OFFLINE", raising=False)
    code = run_cli(argv_for(name, tmp_path))
    assert no_socket == [], f"{name} tried to open a socket"
    if name in NETWORK:
        assert code == 6
    else:
        assert code in DOCUMENTED, (name, code)


def test_analytic_chain_exits_0_offline(no_socket, tmp_path):
    prepared_run()
    for argv in (["consolidate", "--run", RID], ["rank", "--run", RID],
                 ["sensitivity", "--run", RID, "--draws", "50"], ["superiority", "--run", RID],
                 ["lineage", "--run", RID], ["fitgap", "--run", RID]):
        assert run_cli(argv) == 0, argv
    assert no_socket == []


def test_network_commands_respect_ama_offline(no_socket, monkeypatch):
    monkeypatch.setenv("AMA_OFFLINE", "1")
    assert run_cli(["fetch", "--slug", "bmad"]) == 6
    state.init("20261127-121500-gitty", "git", "gitty")
    assert run_cli(["intake", "--run", "20261127-121500-gitty", "--mode", "git", "--source",
                    "https://example.invalid/x.git", "--slug", "gitty"]) == 6
    assert no_socket == []
