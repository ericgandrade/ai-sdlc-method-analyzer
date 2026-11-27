import pytest
from engine.miniyaml import loads, MiniYamlError


def test_scalars_and_mapping():
    doc = loads('a: 1\nb: true\nc: false\nd: null\ne: "x: y"\nf: \'it\'\'s\'\ng: plain text  # comment\n')
    assert doc == {"a": 1, "b": True, "c": False, "d": None, "e": "x: y", "f": "it's", "g": "plain text"}


def test_nested_mapping_and_lists():
    text = """# header
schema: 1
refs:
  - slug: a
    tags: [x, y]
    docs: []
    nested:
      k: v
  - slug: b
    docs:
      - url: https://example.org/a#frag
        file: a.md
names:
  - one
  - two
"""
    doc = loads(text)
    assert doc["schema"] == 1
    assert doc["refs"][0] == {"slug": "a", "tags": ["x", "y"], "docs": [], "nested": {"k": "v"}}
    assert doc["refs"][1]["docs"] == [{"url": "https://example.org/a#frag", "file": "a.md"}]
    assert doc["names"] == ["one", "two"]


def test_list_at_same_indent_as_key():
    assert loads("a:\n- x\n- y\n") == {"a": ["x", "y"]}


@pytest.mark.parametrize("text", [
    "a:\t1\n",
    "a: &anchor 1\n",
    "a: *alias\n",
    "a: |\n  multi\n",
    "a: >\n  folded\n",
    "a: {b: 1}\n",
    "a: [[1], 2]\n",
    "a: 1\na: 2\n",
    "a:\n   b: 1\n",
    "a: \"open\n",
    "a:\n",
])
def test_rejected(text):
    with pytest.raises(MiniYamlError) as e:
        loads(text)
    assert "line " in str(e.value)
