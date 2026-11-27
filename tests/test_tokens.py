"""Static token counts, lens L5 (plan §7.8; Task 2.9)."""
import json
import os
import pathlib
import shutil
import sys

import pytest

from engine import baseline as bl
from engine import paths, tokens
from engine.jsonio import read_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
TINY = ROOT / "tests" / "fixtures" / "tiny-method"
A4 = {"ai-dlc": (12342, 37720, 96496, 3185959), "agile-v": (1758, 2842, 25403, 662512),
      "bmad": (1813, 2008, 41183, 515146), "addyosmani": (2338, 3893, 32577, 199401),
      "superpowers": (1245, 3820, 16282, 226283), "mattpocock": (575, 1278, 10562, 172428),
      "spec-kit": (942, 2739, 32240, 983534), "openspec": (634, 3584, 13998, 1065039)}
# The reference round followed one symlink (mattpocock AGENTS.md -> CLAUDE.md, 1,039 tokens);
# this engine never follows symlinks (§7.5), so that T0 is lower by exactly that file.
SYMLINK_GAP = {"mattpocock": 1039}


@pytest.fixture
def fallback():
    return tokens.Counter(force_fallback=True)


def lens(entries_by_tier, root="cache:tiny"):
    return {"host": "Claude Code", "L5": {"T1": entries_by_tier.get("T1", []), "T2": entries_by_tier.get("T2", []),
                                          "T3": entries_by_tier.get("T3", []), "T0_root": root}}


def resolver(base):
    def r(p):
        return paths.resolve(p, subpaths={}, refs=base)
    return r


@pytest.fixture
def refs(tmp_path):
    base = tmp_path / "refs"
    shutil.copytree(TINY, base / "tiny")
    return base


def test_chars4_exact_counts(refs, fallback):
    plan = (refs / "tiny" / "skills" / "plan" / "SKILL.md").read_text()
    readme = (refs / "tiny" / "README.md").read_text()
    row = tokens.count_method(lens({"T2": [{"path": "cache:tiny/README.md", "frontmatter_only": False}],
                                    "T3": [{"path": "cache:tiny/skills/plan/SKILL.md", "frontmatter_only": False}]}),
                              resolver(refs), fallback)
    assert row["T2"] == len(readme) // 4 and row["T3"] == len(plan) // 4
    assert row["tokenizer"] == "chars/4" and row["comparable"] is False


def test_crlf_normalized(refs, fallback):
    f = refs / "tiny" / "README.md"
    lf = len(f.read_text()) // 4
    f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    row = tokens.count_method(lens({"T2": [{"path": "cache:tiny/README.md", "frontmatter_only": False}]}),
                              resolver(refs), fallback)
    assert row["T2"] == lf


def test_frontmatter_only_counts_the_yaml_block(refs, fallback):
    f = refs / "tiny" / "skills" / "plan" / "SKILL.md"
    yaml = "name: tiny-plan\ndescription: Write a short plan with testable acceptance criteria before any code."
    assert tokens.frontmatter(f.read_text()) == yaml
    f.write_bytes(b"\xef\xbb\xbf" + f.read_bytes())          # a BOM is tolerated
    row = tokens.count_method(lens({"T1": [{"path": "cache:tiny/skills/plan/SKILL.md", "frontmatter_only": True}]}),
                              resolver(refs), fallback)
    assert row["T1"] == len(yaml) // 4
    assert tokens.frontmatter("no frontmatter\n") == "" and tokens.frontmatter("---\n---\nx") == ""


def test_duplicates_counted_once_and_missing_listed(refs, fallback):
    e = {"path": "cache:tiny/README.md", "frontmatter_only": False}
    row = tokens.count_method(lens({"T2": [e, dict(e), {"path": "cache:tiny/nope.md", "frontmatter_only": False}]}),
                              resolver(refs), fallback)
    assert row["T2"] == len((refs / "tiny" / "README.md").read_text()) // 4
    assert row["missing"] == ["cache:tiny/nope.md"] and row["files"]["T2"] == 1


def test_closed_type_gives_nulls(refs, fallback):
    row = tokens.count_method(lens({}), resolver(refs), fallback, closed=True)
    assert [row[t] for t in ("T1", "T2", "T3", "T0")] == [None] * 4 and row["measurable"] is False


def test_t0_skips_lockfiles_and_build_with_shipped_root(refs, fallback):
    tiny = refs / "tiny"
    base = tokens.count_t0(tiny, fallback)[0]
    (tiny / "package-lock.json").write_text('{"lockfileVersion": 3}' * 50)
    (tiny / "docs" / "build").mkdir(parents=True)
    (tiny / "docs" / "build" / "page.md").write_text("generated " * 40)
    assert tokens.count_t0(tiny, fallback)[0] == base + len("generated " * 40) // 4
    assert tokens.count_t0(tiny, fallback, shipped_root="skills/")[0] == base


@pytest.mark.skipif(sys.platform.startswith("win"), reason="symlinks need privileges on Windows")
def test_t0_never_follows_symlinks(refs, fallback):
    tiny = refs / "tiny"
    base = tokens.count_t0(tiny, fallback)[0]
    (tiny / "AGENTS.md").symlink_to(tiny / "README.md")
    assert tokens.count_t0(tiny, fallback)[0] == base


def test_hello_world_o200k():
    tiktoken = pytest.importorskip("tiktoken")
    cache = paths.cache_dir() / "tiktoken"
    os.environ["TIKTOKEN_CACHE_DIR"] = str(cache)
    try:
        enc = tiktoken.get_encoding("o200k_base")
    except Exception:
        pytest.skip("o200k_base could not be loaded (no network to prime it)")
    assert len(enc.encode("Hello, world!")) == 4


def _expected(slug):
    t1, t2, t3, t0 = A4[slug]
    return (t1, t2, t3, t0 - SYMLINK_GAP.get(slug, 0))


def test_shipped_tokens_json_equals_a4_or_is_explained():
    rounds = bl.rounds(ROOT)
    p = bl.round_dir(ROOT) / "tokens.json"
    if not p.exists():
        pytest.skip("tokens.json not shipped in this round")
    data = read_json(p)
    assert data["tokenizer"] == "tiktoken o200k_base"
    for slug in A4:
        r = data["methods"][slug]
        assert (r["T1"], r["T2"], r["T3"], r["T0"]) == _expected(slug), slug
    assert data["methods"]["kiro"]["T0"] is None
    notes = read_json(bl.round_dir(ROOT) / "MANIFEST.json")["notes"]["tokens"]
    assert "mattpocock" in notes and "1,039" in notes


@pytest.mark.needs_cache
def test_baseline_recount_equals_a4():
    try:
        refs = paths.refs_dir()
    except paths.PathError:
        pytest.skip("no data directory")
    if not all((refs / s).is_dir() for s in A4):
        pytest.skip("reference cache not populated (run engine fetch --all)")
    count = tokens.Counter()
    if count.name != "tiktoken o200k_base":
        pytest.skip("tiktoken o200k_base not installed or not primed")
    out = tokens.baseline(ROOT, count=count)
    for slug in A4:
        r = out["methods"][slug]
        assert (r["T1"], r["T2"], r["T3"], r["T0"]) == _expected(slug), slug
        assert r["missing"] == []
