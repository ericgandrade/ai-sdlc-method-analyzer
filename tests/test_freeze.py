import hashlib, pathlib, shutil, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
FROZEN = {"methodology/methodology-v1.0.md": "a6e3953725b67db0189e188c1495ee9b54975e48f65c28baaa01f459b69cf9a4",
          "methodology/evaluator-agent-v1.0.md": "aa3a1f7072ac9200c08135e2f2f773226268870973fc7b908e793a972c31857a",
          "methodology/rubric-v2.0.pt.md": "8d5b63ea22847d44bb2f60a8fb9f55f7f87d30d68af6cac76d79bebd51057b84"}

def test_hashes():
    for f, h in FROZEN.items():
        assert hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == h

def test_verify_freeze_ok():
    assert subprocess.run([sys.executable, "-m", "engine", "verify-freeze"], cwd=ROOT).returncode == 0

def test_verify_freeze_detects_change(tmp_path):
    shutil.copytree(ROOT / "methodology", tmp_path / "methodology")
    p = tmp_path / "methodology/methodology-v1.0.md"; p.write_bytes(p.read_bytes() + b" ")
    r = subprocess.run([sys.executable, "-m", "engine", "verify-freeze", "--root", str(tmp_path)], cwd=ROOT)
    assert r.returncode == 4

def test_verify_freeze_single_file():
    r = subprocess.run([sys.executable, "-m", "engine", "verify-freeze", "--file", "methodology/rubric-v2.0.pt.md"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0

def test_verify_freeze_print():
    r = subprocess.run([sys.executable, "-m", "engine", "verify-freeze", "--print"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert FROZEN["methodology/methodology-v1.0.md"] in r.stdout

def test_gitattributes_keeps_bytes():
    assert "methodology/*.md -text" in (ROOT / ".gitattributes").read_text()


def test_pathmap_covers_frozen_paths():
    import re
    pathmap = (ROOT / "methodology/PATHMAP.md").read_text(encoding="utf-8")
    table = "\n".join(l for l in pathmap.splitlines() if l.startswith("|"))
    found = set()
    for f in FROZEN:
        text = (ROOT / f).read_text(encoding="utf-8")
        found |= set(re.findall(r"docs/research/[\w/.*-]+|anexos/[\w.-]+", text))
    assert found
    for path in sorted(found):
        assert f"`{path}`" in table, path
    assert "I-inv unavailable" in pathmap


def test_every_freeze_record_exists_and_matches():
    from engine import freeze
    recs = freeze.records(ROOT)
    names = {r[0] for r in recs}
    assert {"methodology-v1.0.md", "evaluator-agent-v1.0.md", "rubric-v2.0.pt.md", "rubric-v2.0.en.md",
            "rulings-v1.md", "protocol-v1.md"} <= names
    for name, sha, _, _ in recs:
        assert (ROOT / "methodology" / name).exists(), name
    assert freeze.verify(ROOT) == []
