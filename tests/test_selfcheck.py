import pytest

from engine import report_html, report_model
from report_util import BASE, html


@pytest.fixture(scope="module")
def good():
    return html()


def test_reports_pass(good):
    assert report_html.selfcheck(good, private=False) == []
    assert report_html.selfcheck(html(BASE, "2026-11-27"), private=False) == []


def inject(doc, snippet):
    return doc.replace('<section id="panorama">', snippet + '<section id="panorama">', 1)


@pytest.mark.parametrize("snippet, needle", [
    ("<script>x()</script>", "script"),
    ('<p onclick="x()">a</p>', "on*"),
    ('<img src="https://example.com/x.png" alt="">', "external"),
    ('<a href="http://example.com/">x</a>', "external"),
    ('<a href="javascript:x()">x</a>', "javascript"),
    ('<svg class="hb" viewBox="0 0 16 16"><use href="#c1"/></svg>', "aria-label"),
    ('<table><tr><td>x</td></tr></table>', "thead"),
    ("<h1>second</h1>", "<h1>"),
])
def test_violations_fail(good, snippet, needle):
    errs = report_html.selfcheck(inject(good, snippet), private=False)
    assert any(needle in e for e in errs), errs


def test_footer_links_are_allowed(good):
    assert '<a href="https://github.com/' in good.split("<footer")[1]


def test_size_limit(good):
    big = inject(good, "<p>" + "x" * (6 * 1024 * 1024) + "</p>")
    assert any("5 MB" in e for e in report_html.selfcheck(big, private=False))


def test_private_target_needs_banner(good):
    assert any("banner" in e for e in report_html.selfcheck(good, private=True))
    with_banner = inject(good, f'<div class="banner">{report_model.PRIVATE_BANNER}</div>')
    assert report_html.selfcheck(with_banner, private=True) == []
    assert any("banner" in e for e in report_html.selfcheck(with_banner, private=False))


def test_limitations_must_be_last(good):
    doc = good.replace("</section>\n<footer", '</section>\n<section id="extra"><h2>x</h2></section>\n<footer', 1)
    assert any("last section" in e for e in report_html.selfcheck(doc, private=False))


def test_private_entry_renders_banner():
    from report_util import inputs, THEME
    from engine import theme
    inp = inputs()
    inp["results"]["fixture-method"]["private"] = True
    doc = report_html.render(inp, theme.load(THEME))
    assert report_html.selfcheck(doc, private=True) == []
