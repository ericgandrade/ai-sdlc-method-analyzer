"""The committed sample `docs/report/index.html` is the baseline-only report (Task 3.8). Regenerate with
`python -m engine report --baseline-only --date 2026-11-27`, then copy report.html to docs/report/index.html
and report.md to docs/report/report.md."""
from engine import report_html, report_md
from report_util import BASE, ROOT, html, inputs

SAMPLE = ROOT / "docs" / "report"


def test_sample_passes_selfcheck_and_size():
    doc = (SAMPLE / "index.html").read_bytes()
    assert len(doc) <= report_html.MAX_BYTES
    assert report_html.selfcheck(doc.decode("utf-8"), private=False) == []


def test_sample_is_current():
    assert (SAMPLE / "index.html").read_bytes().decode("utf-8") == html(BASE, "2026-11-27")
    assert (SAMPLE / "report.md").read_bytes().decode("utf-8") == report_md.render(inputs(BASE, "2026-11-27"))
