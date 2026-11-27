"""leakcheck --ccbysa boundaries, --run and --public (plan §7.14; Task 2.17)."""
import pathlib

import pytest

from engine import leakcheck, state
from engine.cli import main

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Synthetic stand-in for a CC BY-SA file: 20 distinct invented words.
WORDS = ("amber basalt cobalt dune ember fjord garnet harbor indigo jasper "
         "kestrel lagoon marble nectar onyx prairie quartz raven sierra tundra").split()


@pytest.fixture
def corpus(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "skill.md").write_text(" ".join(WORDS) + "\n")
    return leakcheck.build_corpus(d)


def test_twelve_word_shingle_hits(corpus):
    text = "Our note: " + " ".join(WORDS[3:15]) + " and more of our own.\n"
    assert [h[1] for h in leakcheck.scan_shingles(text, corpus)] == ["ccbysa:shingle"]


def test_eleven_words_do_not_hit(corpus):
    text = "Our note: " + " ".join(WORDS[3:14]) + " and more of our own.\n"
    assert leakcheck.scan_shingles(text, corpus) == []


@pytest.fixture
def runs(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)
    a = "20261127-101500-zephyrkit"
    b = "20261127-111500-tiny"
    state.init(a, "folder", "zephyrkit", name="Zephyr Kit")
    state.init(b, "folder", "tiny")
    return a, b


def test_run_scan_outputs_and_report_not_the_snapshot(runs, capfd):
    from engine import paths
    a, b = runs
    rd = paths.runs_dir() / b
    (rd / "target").mkdir()
    (rd / "target" / "secret.md").write_text("mail " + "someone" + "@" + "example.org\n")
    assert main(["leakcheck", "--run", b, "--ci"]) == 0           # the private snapshot is input, not output
    rep = paths.reports_dir() / b
    rep.mkdir(parents=True)
    (rep / "report.md").write_text("contact " + "someone" + "@" + "example.org\n")
    assert main(["leakcheck", "--run", b, "--ci"]) == 5
    assert "report:report.md" in capfd.readouterr().out
    assert main(["leakcheck", "--run", "20261127-000000-nope"]) == 3


def test_public_flags_other_runs_private_targets_by_id_only(runs, capfd):
    from engine import paths
    a, b = runs
    (paths.runs_dir() / b / "analysis.md").write_text("This compares against zephyrkit and ZEPHYR KIT.\n")
    assert main(["leakcheck", "--run", b, "--ci"]) == 0
    capfd.readouterr()
    assert main(["leakcheck", "--run", b, "--public", "--ci"]) == 5
    cap = capfd.readouterr()
    assert "private#" in cap.out + cap.err
    assert "zephyr" not in (cap.out + cap.err).lower()


def test_public_skips_registry_references(monkeypatch):
    monkeypatch.chdir(ROOT)
    state.init("20261127-101500-bmad", "reference", "bmad")
    assert leakcheck.private_terms() == []
