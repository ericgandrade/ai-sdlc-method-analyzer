"""CITATION.cff, THIRD_PARTY_NOTICES.md and SECURITY.md (Task 7.2)."""
import json
import pathlib

from engine import miniyaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _text(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_citation_fields():
    cff = miniyaml.load(str(ROOT / "CITATION.cff"))
    plugin = json.loads(_text(".claude-plugin/plugin.json"))
    assert cff["title"] == "AI SDLC Method Analyzer"
    assert cff["version"] == plugin["version"]
    assert cff["date-released"] == "2026-11-27"
    assert cff["license"] == plugin["license"]
    assert cff["repository-code"].startswith("https://github.com/")
    assert cff["authors"] and "a6e39537" in cff["abstract"]


def test_notices_list_every_registry_entry_and_licence():
    reg = miniyaml.load(str(ROOT / "references" / "registry.yaml"))
    notices = _text("THIRD_PARTY_NOTICES.md")
    entries = reg["references"] + reg["variants"]
    assert len(entries) == 14
    for e in entries:
        assert f'`{e["slug"]}`' in notices, e["slug"]
        assert e["licence"] in notices, e["slug"]
        assert e["url"] in notices, e["slug"]
    assert "cited by path only, never quoted" in notices


def test_security_private_reporting():
    sec = _text("SECURITY.md")
    assert "Report a vulnerability" in sec and "privately" in sec
    assert "@" not in sec
