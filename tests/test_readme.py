"""README.md follows the publication plan (Task 7.1, plan §11)."""
import json
import pathlib
import re

from engine import cli, common
from engine.paths import assert_portable

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n")
RESULTS = json.loads((ROOT / "baseline" / "rounds" / "2026-11" / "derived" / "results.json").read_text(encoding="utf-8"))

HEADINGS = ["What it is", "Prerequisites", "Quick start", "The menu, walked through", "Scenario R",
            "The 16 criteria", "The lenses", "Methodology and fairness", "The baseline", "Privacy and security",
            "How to add a reference", "Pointing it at your own method", "How to cite",
            "Licences and third parties", "Troubleshooting", "Limitations"]
PRIVACY = ("Your source never leaves your machine except to the model provider your agent host already uses; "
           "the tool adds no network calls, no telemetry and no uploads.")


def _section(title):
    return README.split(f"\n## {title}\n", 1)[1].split("\n## ", 1)[0]


def _rows(text):
    return [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in text.splitlines() if line.startswith("| ") and not line.startswith("|---")]


def test_headings_in_order_and_limitations_last():
    assert re.findall(r"^## (.+)$", README, re.M) == HEADINGS


def test_privacy_sentence_opens_quick_start_and_privacy():
    for title in ("Quick start", "Privacy and security"):
        assert _section(title).strip().startswith(PRIVACY)


def test_criteria_table_equals_common():
    rows = [r for r in _rows(_section("The 16 criteria")) if re.fullmatch(r"C\d+", r[0]) and len(r) == 4]
    assert [r[0] for r in rows] == common.CRITERIA
    assert [r[1] for r in rows] == common.CRITERION_NAMES
    assert [int(r[3]) for r in rows] == common.PROFILES["baseline"]


def test_profiles_table_equals_common():
    rows = [r for r in _rows(_section("The 16 criteria")) if re.fullmatch(r"C\d+", r[0]) and len(r) == 5]
    for i, name in enumerate(("equal", "startup", "regulated", "autonomous"), start=1):
        assert [float(r[i]) for r in rows] == [float(w) for w in common.PROFILES[name]]


def test_baseline_table_equals_results():
    rows = {r[0].strip("`"): r for r in _rows(_section("The baseline")) if r[0].startswith("`") and len(r) == 10}
    bench = {s for s, v in RESULTS.items() if v["benchmark"]}
    assert len(bench) == 9 and set(rows) == bench
    for slug, r in rows.items():
        v = RESULTS[slug]
        assert r[1] == v["name"]
        assert r[5] == f'{v["L1"]["baseline"]:.1f} ± {v["U"]["baseline"]:.1f}'
        assert r[6] == f'{v["L2"]["baseline"]:.1f}'
        assert r[7] == v["L3"]
        assert r[8] == f'{v["L4_coverage"]}%'
        t3 = v["L5"]["T3"]
        assert r[9] == ("n/a (closed)" if t3 is None else f"{t3:,}")


def test_links_exist():
    for target in re.findall(r"\]\(([^)#:]+)\)", README):
        assert (ROOT / target).exists(), target
    assert "docs/report/index.html" in README


def test_quick_start_commands_exist():
    implemented = set(cli.IMPLEMENTED)
    for cmd in re.findall(r"(?:python3|py -3) -m engine ([a-z-]+)", README):
        assert cmd in implemented, cmd


def test_v02_items_are_marked():
    menu = _section("The menu, walked through")
    assert "v0.2" in menu and "S16b" in menu
    assert "v0.2" in README.split("\n## ", 1)[0]


def test_no_absolute_paths():
    assert_portable(README)
