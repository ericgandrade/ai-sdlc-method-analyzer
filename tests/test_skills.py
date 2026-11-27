"""Task 4.7: the analyze skill (single /analyze entry), count-tokens and templates."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
MENU = """AI SDLC Method Analyzer — methodology v1.0 (a6e39537), rubric v2.0 (8d5b63ea)
Runs in progress: <list or "none">   [r] resume a run

1  Assess a method from a local folder
2  Assess a private git repository (cloned with your own git; credentials never stored)
3  Assess a method from documentation only (PDF/HTML/Markdown) → range: floor / centre / ceiling
4  Re-run or refresh a bundled reference at its pin
5  Compare assessed targets with the reference baseline and build the report
6  Fit-gap and roadmap for a target: what it can learn from the best of each reference
q  Quit"""
STAGES = ["S00", "S01", "S02", "S03", "S04:S1", "S04:S2", "S05", "S04:S1r", "S04:S2r", "S06b:S3", "S06", "S07r",
          "S07", "S07b", "S08a", "S08b", "S09", "S10", "S11", "S12", "S13", "S14", "S15", "S16", "S16b", "S17",
          "D1", "D2", "D3", "C1", "F1"]


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    head = text[4:].split("\n---\n", 1)[0]
    return {k.strip(): v.strip() for k, _, v in (line.partition(":") for line in head.splitlines())}, None


def test_skill_frontmatter():
    for p in SKILLS.glob("*/SKILL.md"):
        fields, _ = frontmatter(p)
        assert set(fields) == {"name", "description"} and fields["name"] == p.parent.name
        assert fields["description"].startswith("This skill should be used")


def test_single_analyze_entry():
    assert not (ROOT / ".claude" / "commands").exists()
    assert not (ROOT / "commands").exists()
    assert [p.parent.name for p in SKILLS.glob("*/SKILL.md")].count("analyze") == 1
    assert sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")) == ["analyze", "count-tokens"]


def test_menu_is_verbatim():
    text = (SKILLS / "analyze" / "SKILL.md").read_text(encoding="utf-8")
    assert "```\n" + MENU + "\n```" in text


def test_every_stage_is_mentioned():
    text = (SKILLS / "analyze" / "SKILL.md").read_text(encoding="utf-8")
    for s in STAGES:
        assert re.search(r"(?<![\w:])" + re.escape(s) + r"(?![\w])", text), s


def test_count_tokens_wraps_the_engine():
    text = (SKILLS / "count-tokens" / "SKILL.md").read_text(encoding="utf-8")
    assert "{PY} -m engine apply-audit --run {RUN}" in text and "{PY} -m engine tokens --run {RUN}" in text
    assert "not comparable" in text


def test_templates_exist():
    for t in ("scorecard", "analysis", "docs-only", "fitgap"):
        assert (ROOT / "templates" / f"{t}.md").is_file()
    sc = (ROOT / "templates" / "scorecard.md").read_text(encoding="utf-8")
    for h in ("## Default path trace (scenario R)", "## Scores", "## Search log", "## Machine-readable"):
        assert h in sc
