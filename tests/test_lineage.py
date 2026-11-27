"""lineage (plan §7.13; Task 2.15). Every fixture line is synthetic text written for this test."""
import pathlib

import pytest

from engine import lineage, paths, state
from engine.cli import main
from engine.jsonio import read_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
RID = "20261127-101500-tiny"

REF_LINES = [f"Synthetic reference step number {i} checks the widget ledger before moving on." for i in range(30)]
NEW_LINES = [f"Locally written guidance line {i} about the sample gadget workflow." for i in range(5)]
OTHER = [f"Unrelated fixture sentence {i} describing a teapot inventory." for i in range(40)]


def ref_doc(lines, name):
    return f"---\nname: {name}\ndescription: synthetic\n---\n" + "\n".join(lines) + "\n"


def target_doc():
    return "---\nname: widget-steps\n---\n" + "\n".join(REF_LINES[:20] + NEW_LINES) + "\n"


def test_normalize_drops_short_and_blank_lines():
    assert lineage.normalize("  Hello   World Again \n\nshort\n\tTabs\tand  spaces here\r") == [
        "hello world again", "tabs and spaces here"]


def test_twenty_plus_five_gives_ratio_080_against_the_right_file():
    refs = {"cache:alpha/skills/widget-steps/SKILL.md": ref_doc(REF_LINES, "widget-steps"),
            "cache:beta/docs/teapots.md": ref_doc(OTHER, "teapots")}
    out = lineage.lineage({"target:skills/widget-steps/SKILL.md": target_doc()}, refs)
    f = out["files"][0]
    best = f["matches"][0]
    assert best["ref"] == "cache:alpha/skills/widget-steps/SKILL.md"
    # 20 shared body lines of 25, plus the shared frontmatter name line ("---" is under 8 characters)
    assert f["lines"] == 26 and best["ratio"] == round(21 / 26, 4)
    assert out["hits"][0]["ref"] == best["ref"]


def test_ratio_is_exactly_080_without_frontmatter():
    refs = {"cache:alpha/a.md": "\n".join(REF_LINES), "cache:beta/b.md": "\n".join(OTHER)}
    out = lineage.lineage({"target:a.md": "\n".join(REF_LINES[:20] + NEW_LINES)}, refs)
    m = out["files"][0]["matches"]
    assert m[0] == {"ref": "cache:alpha/a.md", "ratio": 0.8, "seq_ratio": m[0]["seq_ratio"], "jaccard": round(20 / 35, 4)}
    assert all(x["ref"] != "cache:beta/b.md" for x in m)       # no shared line, not a candidate


def test_unrelated_files_are_below_01():
    refs = {"cache:beta/b.md": "\n".join(OTHER + REF_LINES[:1])}
    out = lineage.lineage({"target:a.md": "\n".join(REF_LINES[:20] + NEW_LINES)}, refs)
    assert out["files"][0]["matches"][0]["ratio"] < 0.1 and out["hits"] == []


def test_identifiers_from_frontmatter_skill_dirs_and_scripts():
    t = {"target:skills/widget-steps/SKILL.md": target_doc(), "target:scripts/check-widgets.sh": "echo synthetic check\n"}
    r = {"cache:alpha/skills/widget-steps/SKILL.md": ref_doc(REF_LINES, "widget-steps"),
         "cache:alpha/bin/check-widgets.sh": "echo synthetic check\n"}
    out = lineage.lineage(t, r)
    assert "name:widget-steps" in out["identifiers"]["target"]
    assert out["identifiers"]["shared"]["alpha"] == ["name:widget-steps", "script:check-widgets.sh", "skill:widget-steps"]


def test_cli_against_the_cache(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    state.init(RID, "folder", "tiny")
    t = state.run_path(RID) / "target" / "skills" / "widget-steps"
    t.mkdir(parents=True)
    (t / "SKILL.md").write_text(target_doc())
    ref = paths.refs_dir() / "bmad" / "skills" / "widget-steps"
    ref.mkdir(parents=True)
    (ref / "SKILL.md").write_text(ref_doc(REF_LINES, "widget-steps"))
    assert main(["lineage", "--run", RID]) == 0
    out = read_json(state.run_path(RID) / "lineage-pre.json")
    assert out["against"] == ["bmad"] and out["hits"][0]["ref"] == "cache:bmad/skills/widget-steps/SKILL.md"
    assert main(["lineage", "--run", RID, "--against", "nope"]) == 2
