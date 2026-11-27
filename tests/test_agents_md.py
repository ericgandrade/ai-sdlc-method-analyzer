"""AGENTS.md: the fallback for non-Claude hosts (Task 5.1)."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8").replace("\r\n", "\n")
SKILL = (ROOT / ".claude" / "skills" / "analyze" / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n")


def _menu(text):
    blocks = re.findall(r"```\n(AI SDLC Method Analyzer.*?)```", text, re.S)
    assert len(blocks) == 1
    return blocks[0]


def _stage_ids(text):
    part = re.split(r"\n## ", text.split("\n## Stage", 1)[1], maxsplit=1)[0]
    ids = set()
    for line in part.splitlines():
        if line.startswith("| ") and not line.startswith("| Stage") and not line.startswith("|---"):
            ids.update(s.strip() for s in line.split("|")[1].split(","))
    return ids


def test_menu_is_verbatim():
    assert _menu(AGENTS) == _menu(SKILL)
    for opt in ("1  Assess a method from a local folder", "6  Fit-gap and roadmap", "q  Quit"):
        assert opt in AGENTS


def test_stage_table_covers_every_stage():
    skill_ids = _stage_ids(SKILL)
    assert {"S00", "S07", "S17", "D3", "C1", "F1"} <= skill_ids
    assert skill_ids - {"S04:S1r", "S04:S2r"} <= _stage_ids(AGENTS)


def test_new_session_per_role():
    assert "new session" in AGENTS.lower()
    assert "**New session per role.**" in AGENTS
    assert "--isolation fresh-session" in AGENTS
    assert "prompt-only" in AGENTS


def test_briefs_named_exist():
    for role in set(re.findall(r"`([a-z-]+)`", AGENTS)):
        if role in ("intake-pinner", "path-tracer", "l1-scorer", "reconciler", "red-team-auditor", "adjudicator",
                    "lens-evaluator", "lens-auditor", "lineage-detector", "dense-analyst", "fitgap-writer",
                    "report-builder", "report-reviewer", "docs-only-assessor"):
            assert (ROOT / ".claude" / "agents" / f"{role}.md").is_file()
    assert len(list((ROOT / ".claude" / "agents").glob("*.md"))) == 14
