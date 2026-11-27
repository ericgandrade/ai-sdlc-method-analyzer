"""Shipped baseline checks (Task 1.6), parameterized by round."""
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

from engine import baseline, stats
from engine.paths import assert_portable
from engine.registry import entries, load_registry, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUNDS = baseline.rounds(ROOT)
NINE = ["ai-dlc", "agile-v", "bmad", "addyosmani", "superpowers", "kiro", "mattpocock", "spec-kit", "openspec"]

A1 = {  # Appendix A.1: reconciled vectors, recorded U, scorers
    "ai-dlc": ([2, 4, 3, 5, 4, 4, 3, 4, 3, 3, 2, 3, 5, 3, 2, 3], 3.1, ["S-B", "S-C"]),
    "agile-v": ([3, 2, 3, 5, 4, 4, 3, 2, 3, 4, 3, 2, 4, 4, 5, 2], 3.6, ["S-B", "S-D"]),
    "bmad": ([5, 4, 3, 4, 4, 4, 3, 3, 3, 3, 2, 2, 4, 3, 2, 3], 2.7, ["S-A", "S-D"]),
    "addyosmani": ([2, 3, 5, 3, 3, 2, 2, 2, 2, 2, 3, 3, 5, 3, 4, 0], 2.9, ["S-A", "S-C"]),
    "superpowers": ([2, 2, 4, 4, 4, 4, 2, 3, 2, 2, 1, 0, 5, 2, 4, 2], 2.3, ["S-A", "S-C"]),
    "kiro": ([4, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 1, 3, 3, 2, 2], 2.7, ["S-B", "S-D"]),
    "mattpocock": ([2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 1, 1, 4, 3, 3, 2], 2.8, ["S-A", "S-D"]),
    "spec-kit": ([4, 3, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1, 3, 2, 5, 0], 2.6, ["S-B", "S-C"]),
    "openspec": ([3, 4, 3, 2, 2, 2, 2, 0, 1, 2, 1, 1, 2, 2, 2, 0], 2.6, ["S-B", "S-D"]),
}
A3_L4 = {"ai-dlc": 57, "agile-v": 48, "bmad": 53, "addyosmani": 51, "superpowers": 40, "kiro": 33,
         "mattpocock": 35, "spec-kit": 33, "openspec": 27}
A3_L3 = {"ai-dlc": "A3", "agile-v": "A3", "bmad": "A2", "addyosmani": "A2", "superpowers": "A3", "kiro": "A3",
         "mattpocock": "A3", "spec-kit": "A2", "openspec": "A1"}
A3_L2 = {"ai-dlc": 69.8, "agile-v": 73.2, "bmad": 68.4, "addyosmani": 59.0, "superpowers": 56.0, "kiro": 45.4,
         "mattpocock": 45.4, "spec-kit": 45.0, "openspec": 38.8}

pytestmark = pytest.mark.skipif(not ROUNDS, reason="no baseline round present")


def rd(r):
    return baseline.round_dir(ROOT, r)


def load(r, rel):
    return json.loads((rd(r) / rel).read_text(encoding="utf-8"))


def json_files(r):
    return sorted(rd(r).rglob("*.json"))


def test_current_round_exists():
    assert baseline.current_round(ROOT) in ROUNDS


@pytest.mark.parametrize("r", ROUNDS)
def test_nine_slugs(r):
    assert sorted(load(r, "l1.json")) == sorted(NINE)
    assert sorted(p.stem for p in (rd(r) / "lenses").glob("*.json")) == sorted(NINE)
    assert sorted(p.stem for p in (rd(r) / "audits").glob("*.json")) == sorted(NINE)
    assert sorted(p.name for p in (rd(r) / "scorecards").iterdir()) == sorted(NINE)


@pytest.mark.parametrize("r", ROUNDS)
def test_l1_vectors_and_u(r):
    l1 = load(r, "l1.json")
    for slug, (vec, u, scorers) in A1.items():
        assert l1[slug]["scores"] == vec, slug
        assert l1[slug]["U_recorded"] == u, slug
        assert l1[slug]["scorers"] == scorers, slug
        assert len(l1[slug]["u"]) == 16 and len(l1[slug]["pairs"]) == 16


@pytest.mark.parametrize("r", ROUNDS)
def test_pairs_match_scorecards(r):
    l1 = load(r, "l1.json")
    for slug in NINE:
        a, b = (load(r, f"scorecards/{slug}/{s}.json") for s in l1[slug]["scorers"])
        assert l1[slug]["pairs"] == [[a["scores"][f"C{i}"]["s"], b["scores"][f"C{i}"]["s"]] for i in range(1, 17)]
        for card in (a, b):
            for cell in card["scores"].values():
                assert set(cell) == {"s", "conf", "ev"}   # cites and first_unmet are dropped


@pytest.mark.parametrize("r", ROUNDS)
def test_alpha_over_pairs(r):
    l1 = load(r, "l1.json")
    pairs = [tuple(p) for slug in NINE for p in l1[slug]["pairs"]]
    assert len(pairs) == 144
    assert abs(stats.alpha_ordinal(pairs) - 0.857) < 5e-4


@pytest.mark.parametrize("r", ROUNDS)
def test_lenses_match_appendix(r):
    from engine.common import CRITERIA, PROFILES
    l1 = load(r, "l1.json")
    for slug in NINE:
        lens = load(r, f"lenses/{slug}.json")
        assert sum(f["v"] for f in lens["L4"].values()) == lens["L4_total"] == A3_L4[slug], slug
        assert len(lens["L4"]) == 34
        assert lens["L3"]["level"] == A3_L3[slug], slug
        l2 = list(l1[slug]["scores"])
        for c, cell in lens["L2"].get("ceiling", {}).items():
            l2[CRITERIA.index(c)] = max(l2[CRITERIA.index(c)], cell["s"])
        assert stats.total(l2, PROFILES["baseline"]) == A3_L2[slug], slug


@pytest.mark.parametrize("r", ROUNDS)
def test_portable_everywhere(r):
    for p in json_files(r):
        assert_portable(json.loads(p.read_text(encoding="utf-8")), p.name)


@pytest.mark.parametrize("r", ROUNDS)
def test_cache_slugs_in_registry(r):
    slugs = {e["slug"] for e in entries(load_registry(ROOT))}
    for p in json_files(r):
        for slug in re.findall(r"cache:([a-z0-9-]+)/", p.read_text(encoding="utf-8")):
            assert slug in slugs, (p.name, slug)


@pytest.mark.parametrize("r", ROUNDS)
def test_analysis_names_are_slugs(r):
    d = rd(r) / "analyses"
    if d.exists():
        for p in d.iterdir():
            assert re.fullmatch(r"[a-z0-9-]+\.md", p.name), p.name


def test_registry_with_files():
    assert validate(load_registry(ROOT), ROOT, check_files=True) == []


def test_baseline_verify_cli():
    r = subprocess.run([sys.executable, "-m", "engine", "baseline", "verify"], cwd=ROOT)
    assert r.returncode == 0


def test_baseline_verify_detects_change(tmp_path):
    import shutil
    shutil.copytree(ROOT / "baseline", tmp_path / "baseline")
    rid = baseline.current_round(tmp_path)
    p = baseline.round_dir(tmp_path, rid) / "l1.json"
    p.write_bytes(p.read_bytes() + b" ")
    r = subprocess.run([sys.executable, "-m", "engine", "baseline", "verify", "--root", str(tmp_path)], cwd=ROOT,
                       capture_output=True)
    assert r.returncode == 4


def _leak(*extra):
    return subprocess.run([sys.executable, "-m", "engine", "leakcheck", "--path", "baseline", "--ci", *extra],
                          cwd=ROOT, capture_output=True, text=True)


def test_leakcheck_baseline_builtins():
    assert _leak().returncode == 0


def test_leakcheck_baseline_owner_denylist(tmp_path):
    deny = ROOT / ".leakcheck" / "denylist.txt"
    if not deny.exists():
        secret = os.environ.get("LEAK_DENYLIST", "")
        if not secret.strip():
            pytest.skip("owner denylist not available (local file or LEAK_DENYLIST)")
        deny = tmp_path / "denylist.txt"
        deny.write_text(secret + "\n", encoding="utf-8")
    assert _leak("--denylist", str(deny)).returncode == 0


def test_leakcheck_baseline_ccbysa():
    corpus = ROOT / ".cache" / "refs" / "agile-v"
    if not corpus.is_dir():
        pytest.skip("CC BY-SA corpus absent here; the CI leakcheck job enforces it")
    assert _leak("--ccbysa").returncode == 0
