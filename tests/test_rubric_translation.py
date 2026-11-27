"""The English rubric is a faithful structural mirror of the frozen Portuguese original (Task 1.3)."""
import pathlib, re
from engine.common import FEATURE_NAMES, GROUPS

ROOT = pathlib.Path(__file__).resolve().parents[1]
PT = (ROOT / "methodology/rubric-v2.0.pt.md").read_text(encoding="utf-8")
EN = (ROOT / "methodology/rubric-v2.0.en.md").read_text(encoding="utf-8")
NOTICE = ("Translation of rubric-v2.0.pt.md (sha256 8d5b63ea…). "
          "Non-normative: the Portuguese original prevails.")


def rows(text):
    return [l for l in text.splitlines() if l.startswith("|") and not re.match(r"^\|[-| ]+\|$", l)]


def sections(text):
    parts = re.split(r"^## ", text, flags=re.M)
    return [len(rows(p)) for p in parts]


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def ids(text, pattern):
    return [cells(l)[0] for l in rows(text) if re.fullmatch(pattern, cells(l)[0].split(" ")[0])]


def test_notice_first_line():
    assert EN.splitlines()[0] == NOTICE


def test_feature_ids():
    pt, en = ids(PT, r"F\d+"), ids(EN, r"F\d+")
    assert pt == en and len(en) == 34


def test_autonomy_levels():
    assert ids(PT, r"A[0-5]") == ids(EN, r"A[0-5]") == [f"A{i}" for i in range(6)]


def test_token_measures():
    t = lambda text: [c.split(" ")[0] for c in ids(text, r"T[0-3]")]
    assert t(PT) == t(EN) == ["T1", "T2", "T3", "T0"]


def test_rows_per_section():
    assert sections(PT) == sections(EN)


def test_feature_names_and_groups():
    group_of = {i: g for g, r in GROUPS.items() for i in r}
    frows = [cells(l) for l in rows(EN) if re.fullmatch(r"F\d+", cells(l)[0])]
    for i, row in enumerate(frows):
        assert row[0] == f"F{i + 1}"
        assert row[1] == group_of[i + 1], row
        assert row[2] == FEATURE_NAMES[i], row
