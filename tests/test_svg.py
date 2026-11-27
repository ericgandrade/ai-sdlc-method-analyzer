import re

from engine import svg


def test_pie_edges():
    assert svg._pie(0) == ""
    assert svg._pie(1) == '<circle cx="8" cy="8" r="6.2" fill="currentColor"/>'


def test_pie_half_and_large_arc():
    half = svg._pie(0.5)
    assert "A6.2 6.2 0 0 1 8.00 14.20 Z" in half
    assert " 0 1 1 " in svg._pie(0.6)


def test_sprite_symbol_count():
    d = svg.svg_defs()
    ids = re.findall(r'<symbol id="([cfg]\d)"', d)
    assert len(ids) == 6 + 3 + 5
    assert sum(i.startswith("c") for i in ids) == 6
    assert sum(i.startswith("f") for i in ids) == 3
    assert sum(i.startswith("g") for i in ids) == 5


def test_ball_has_label():
    assert 'aria-label="4 of 5"' in svg.ball("c", 4, "4 of 5")


def test_band_range():
    b = svg.band(68.6, 3.1)
    m = re.search(r'<rect class="u" x="([\d.]+)" y="3" width="([\d.]+)"', b)
    x0, w = float(m.group(1)), float(m.group(2))
    assert x0 == 157.2
    assert round(x0 + w, 1) == 172.1
    assert 'aria-label="68.6 ± 3.1"' in b


def test_group_band():
    assert [svg.group_band(p) for p in (0, 12, 13, 37, 38, 62, 63, 87, 88, 100)] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
