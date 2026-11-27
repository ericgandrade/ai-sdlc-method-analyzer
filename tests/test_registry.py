import pathlib, subprocess, sys
from engine.registry import load_registry, validate, entries, benchmark_slugs

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = load_registry(ROOT)
BY = {e["slug"]: e for e in entries(REG)}
NINE = ["ai-dlc", "agile-v", "bmad", "addyosmani", "superpowers", "kiro", "mattpocock", "spec-kit", "openspec"]


def test_counts():
    assert len(REG["references"]) == 11
    assert len(REG["variants"]) == 3
    assert all(e["status"] in ("scored", "to-score") for e in REG["references"])


def test_benchmark_set():
    assert benchmark_slugs(REG) == NINE
    assert BY["gsd"]["benchmark"] is False and BY["ralph"]["benchmark"] is False
    assert BY["gsd"]["status"] == BY["ralph"]["status"] == "to-score"


def test_conflict_variant():
    e = BY["ralph-loop-plugin"]
    assert e["status"] == "unscored-conflict" and e["conflict"]


def test_publisher_everywhere():
    assert all(e.get("publisher") for e in entries(REG))


def test_kiro_docs():
    k = BY["kiro"]
    assert k["type"] == "closed" and len(k["docs"]) == 36
    for d in k["docs"]:
        assert d["url"].startswith("https://kiro.dev/") and d["snapshot_date"] == "2026-11-26" and d["file"]


def test_unique_slugs_and_pins():
    slugs = [e["slug"] for e in entries(REG)]
    assert len(slugs) == len(set(slugs))
    for e in entries(REG):
        if e["type"] == "open":
            assert len(e["pin"]) == 40 and all(c in "0123456789abcdef" for c in e["pin"])


def test_licences():
    assert BY["agile-v"]["licence"] == "CC-BY-SA-4.0"
    assert BY["ai-dlc"]["licence"] == "MIT-0"
    assert BY["bmad"]["licence"] == "MIT" and BY["bmad"]["licence_api"] == "NOASSERTION"


def test_validator_passes_without_file_checks():
    assert validate(REG, ROOT, check_files=False) == []


def test_validator_rejects_bad_entries():
    bad = {"schema": 1, "references": [dict(BY["bmad"], pin="abc", benchmark=False),
                                       dict(BY["bmad"], type="weird")]}
    errs = validate(bad, ROOT, check_files=False)
    assert any("40-hex" in e for e in errs)
    assert any("duplicate" in e for e in errs)
    assert any("type not in" in e for e in errs)
    assert any("exactly 9" in e for e in errs)


def test_cli_validate_registry():
    r = subprocess.run([sys.executable, "-m", "engine", "validate", "registry", "--no-files"], cwd=ROOT)
    assert r.returncode == 0
