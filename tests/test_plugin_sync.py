"""Task 4.7c: the plugin path reuses the project-scoped briefs and skills, so there is one copy."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def _resolve(field):
    value = PLUGIN[field]
    items = value if isinstance(value, list) else [value]
    assert all(isinstance(v, str) and v.startswith("./") for v in items)
    return [(ROOT / v).resolve() for v in items]


def test_component_paths_point_into_dot_claude():
    assert _resolve("agents") == [(ROOT / ".claude" / "agents").resolve()]
    assert _resolve("skills") == [(ROOT / ".claude" / "skills").resolve()]


def test_every_brief_and_skill_is_reachable_from_the_plugin():
    agents = {p.name for d in _resolve("agents") for p in d.glob("*.md")}
    skills = {p.parent.name for d in _resolve("skills") for p in d.glob("*/SKILL.md")}
    assert agents == {p.name for p in (ROOT / ".claude" / "agents").glob("*.md")} and len(agents) == 14
    assert skills == {"analyze", "count-tokens"}


def test_no_second_copy_and_hooks_by_default_location():
    assert not (ROOT / "agents").exists() and not (ROOT / "skills").exists() and not (ROOT / "dist" / "plugin").exists()
    assert "hooks" not in PLUGIN                    # hooks/hooks.json is loaded from its default location
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    cmd = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py" in cmd
    proj = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "$CLAUDE_PROJECT_DIR/hooks/guard.py" in proj["hooks"]["PreToolUse"][0]["hooks"][0]["command"]


def test_marketplace_points_at_this_repository():
    mk = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert [p["source"] for p in mk["plugins"]] == ["./"] and "version" not in mk["plugins"][0]
