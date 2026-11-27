from engine import md


def test_inline_marks():
    h = md.to_html("A **bold**, *italic* and `x<y` word.")
    assert "<strong>bold</strong>" in h
    assert "<em>italic</em>" in h
    assert "<code>x&lt;y</code>" in h


def test_escaping():
    h = md.to_html("<script>alert(1)</script> & more")
    assert "<script" not in h
    assert "&lt;script&gt;" in h and "&amp;" in h


def test_table_numeric_cells():
    h = md.to_html("| Method | Total | U |\n|---|---:|---|\n| a | 68.6 | ± no |\n| b | 1,039 | 3.1 |\n")
    assert '<th scope="col">Method</th>' in h
    assert "<thead>" in h
    assert '<td class="n">68.6</td>' in h
    assert '<td class="n">1,039</td>' in h
    assert "<td>a</td>" in h


def test_harvey_glyphs():
    h = md.to_html("Scores ◑⁺ 3 and ● 5 and ○ 0.")
    assert 'aria-label="3 of 5"><use href="#c3"/>' in h
    assert 'href="#c5"' in h and 'href="#c0"' in h
    assert "◑" not in h


def test_headings_are_demoted():
    h = md.to_html("# Top\n\n## Sub\n\ntext")
    assert "<h1" not in h and "<h2" not in h
    assert "<h3>Top</h3>" in h


def test_lists():
    h = md.to_html("- one\n- two\n\n1. first\n2. second")
    assert "<ul><li>one</li><li>two</li></ul>" in h
    assert "<ol><li>first</li><li>second</li></ol>" in h
