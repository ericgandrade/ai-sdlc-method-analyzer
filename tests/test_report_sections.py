import re

from engine import report_model
from report_util import BASE, html


def order(doc):
    return re.findall(r'<(?:section|header|footer) id="(?:s-)?([a-z-]+)"', doc)


def test_all_14_sections_in_order_with_target_and_fitgap():
    assert order(html()) == report_model.ORDER


def test_baseline_only_omits_superiority_fitgap_and_decisions():
    doc = html(BASE, "2026-11-27")
    ids = order(doc)
    assert "fitgap" not in ids and "decisions" not in ids
    assert "Superiority test" not in doc
    assert ids[-2:] == ["limitations", "footer"]
    assert ids == [s for s in report_model.ORDER if s not in ("fitgap", "decisions")]


def test_superiority_table_present_with_target():
    doc = html()
    assert "Superiority test: Fixture Method" in doc
    assert "S7 Krippendorff α" in doc and "Comparable" in doc


def test_limitations_is_last_section():
    for doc in (html(), html(BASE, "2026-11-27")):
        assert re.findall(r'<section id="([^"]+)"', doc)[-1] == "limitations"


def test_report_builder_key_message_is_used():
    doc = html()
    assert "Fixture Method sits in the technical-tie group" in doc


def test_baseline_numbers_come_from_json():
    doc = html(BASE, "2026-11-27")
    assert "AWS AI-DLC 68.6" in doc            # leader KPI
    assert 'aria-label="68.6 ± 3.1"' in doc   # band
