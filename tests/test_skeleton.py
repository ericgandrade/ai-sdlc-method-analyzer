import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_versions_agree():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    text = (ROOT / "pyproject.toml").read_text()
    assert f'version = "{plugin["version"]}"' in text

def test_gitignore_private_dirs():
    gi = (ROOT / ".gitignore").read_text().split()
    for entry in ("runs/", "reports/", ".cache/", ".leakcheck/denylist.txt"):
        assert entry in gi

def test_pins_exact():
    assert (ROOT / "requirements-tokens.txt").read_text().strip() == "tiktoken==0.14.0"
    assert "pytest==8.3.4" in (ROOT / "requirements-dev.txt").read_text()
