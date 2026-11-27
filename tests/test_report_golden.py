"""Golden report (plan §8.7). Regenerate only with
`python -m engine report --from tests/fixtures/report-run --date 2026-01-01 --theme themes/neutral.css --update-golden`
plus a reviewer's eye check, and record it in CHANGELOG.md."""
import difflib

import pytest

from engine import report_html, report_md
from report_util import ROOT, html, inputs

GOLDEN = ROOT / "tests" / "golden"


def _compare(actual, name):
    expected = (GOLDEN / name).read_bytes().decode("utf-8")
    if actual != expected:
        diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), f"golden/{name}", "actual",
                                         lineterm=""))
        pytest.fail(f"{name} differs from the golden file:\n" + "\n".join(diff[:80]))


def test_html_golden_and_selfcheck():
    doc = html()
    assert report_html.selfcheck(doc, private=False) == []
    _compare(doc, "report.html")


def test_md_golden():
    doc = report_md.render(inputs())
    assert report_md.check(doc) == []
    _compare(doc, "report.md")
