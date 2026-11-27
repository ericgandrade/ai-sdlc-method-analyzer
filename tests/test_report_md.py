import html as h
import re

from engine import report_md, report_model
from report_util import BASE, html, inputs


def test_no_html_tags():
    for src, d in ((None, "2026-01-01"), (BASE, "2026-11-27")):
        doc = report_md.render(inputs(src, d) if src else inputs())
        assert report_md.check(doc) == []
        assert not re.search(r"<[A-Za-z/!]", doc)


def test_same_section_order():
    doc = report_md.render(inputs())
    titles = re.findall(r"^## (.+)$", doc, flags=re.M)
    expected = [report_model.TITLES[s] for s in report_model.ORDER if s not in ("header", "footer")]
    assert titles == expected


def test_numbers_equal_the_html():
    doc_h, doc_m = html(), report_md.render(inputs())
    cells = re.findall(r'<td class="n">(.*?)</td>', doc_h)
    nums = {h.unescape(re.sub(r"<[^>]+>", "", c)) for c in cells}
    missing = [x for x in nums if x not in doc_m]
    assert not missing, missing[:10]
    for t, u in re.findall(r'aria-label="([\d.]+) ± ([\d.]+)"', doc_h):
        assert f"{t} ± {u}" in doc_m


def test_harvey_glyphs_with_numbers():
    doc = report_md.render(inputs())
    assert "◕ 4" in doc and "● 5" in doc
