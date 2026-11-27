"""JSON Schema subset and shipped schemas (plan §7.6; Task 2.2)."""
import copy
import json
import pathlib
import subprocess
import sys

import pytest

from engine import validate as v
from engine.common import CRITERIA

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
SHA = v.METHODOLOGY_SHA256

# one (schema, passing value, failing value) per keyword
CASES = {
    "type": ({"type": "integer"}, 3, "3"),
    "type-list": ({"type": ["string", "null"]}, None, 1),
    "type-bool-not-int": ({"type": "integer"}, 0, True),
    "required": ({"type": "object", "required": ["a"]}, {"a": 1}, {"b": 1}),
    "properties": ({"type": "object", "properties": {"a": {"type": "string"}}}, {"a": "x"}, {"a": 1}),
    "additionalProperties-false": ({"type": "object", "properties": {"a": {}}, "additionalProperties": False},
                                   {"a": 1}, {"a": 1, "b": 2}),
    "additionalProperties-schema": ({"type": "object", "additionalProperties": {"type": "integer"}}, {"x": 1}, {"x": "1"}),
    "enum": ({"enum": ["H", "M", "L"]}, "M", "X"),
    "items": ({"type": "array", "items": {"type": "integer"}}, [1, 2], [1, "2"]),
    "minItems": ({"type": "array", "minItems": 2}, [1, 2], [1]),
    "maxItems": ({"type": "array", "maxItems": 1}, [1], [1, 2]),
    "minimum": ({"type": "number", "minimum": 0.6}, 0.6, 0.59),
    "maximum": ({"type": "number", "maximum": 1.0}, 1.0, 1.01),
    "pattern": ({"type": "string", "pattern": "^[a-z]+$"}, "abc", "aBc"),
    "oneOf": ({"oneOf": [{"type": "integer", "enum": [0, 1, 2]}, {"type": "string", "enum": ["NA"]}]}, "NA", 3),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_keyword_pass_and_fail(name):
    schema, good, bad = CASES[name]
    assert v.validate(good, schema) == []
    assert v.validate(bad, schema) != []


def test_oneof_exactly_one():
    schema = {"oneOf": [{"type": "number"}, {"type": "integer"}]}
    assert v.validate(1.5, schema) == []
    assert v.validate(1, schema) != []          # matches both


def test_unknown_keyword_is_a_schema_error():
    with pytest.raises(v.SchemaError):
        v.validate(1, {"anyOf": []})


def test_every_shipped_schema_uses_only_the_subset():
    for name in v.schema_names():
        v.validate({}, v.load_schema(name))    # raises SchemaError on an unknown keyword


def card(**over):
    scores = {c: {"s": 2, "r": 1.0, "ra": 2.0, "conf": "M", "ev": "I", "first_unmet": "x", "cites": ["target:a.md:1"]}
              for c in CRITERIA}
    c = {"method": "tiny", "version": "0" * 40, "status": "implemented", "scorer": "S1",
         "methodology_sha256": SHA, "scores": scores}
    c.update(over)
    return c


def test_scorecard_valid():
    assert v.check("scorecard", card()) == []


def test_scorecard_missing_c7_fails():
    c = card()
    del c["scores"]["C7"]
    assert any("C7" in e for e in v.check("scorecard", c))


def test_scorecard_i_inv_fails():
    c = card()
    c["scores"]["C3"]["ev"] = "I-inv"
    assert v.check("scorecard", c)


def test_scorecard_s_evidence_caps_at_2():
    c = card()
    c["scores"]["C4"].update(ev="S", s=3, ra=3.0)
    assert any("evidence S" in e for e in v.check("scorecard", c))
    c["scores"]["C4"].update(s=2, ra=2.0)
    assert v.check("scorecard", c) == []


def test_scorecard_ra_and_r_range_and_hash():
    c = card()
    c["scores"]["C1"].update(s=4, r=0.8, ra=3.0)
    assert any("ra must equal" in e for e in v.check("scorecard", c))
    c["scores"]["C1"].update(ra=3.2)
    assert v.check("scorecard", c) == []
    c["scores"]["C1"]["r"] = 0.5
    assert v.check("scorecard", c)
    assert v.check("scorecard", card(methodology_sha256="0" * 64))


def test_lenses_example_passes():
    obj = json.loads((FIX / "lenses-example.json").read_text(encoding="utf-8"))
    assert v.check("lenses", obj) == []


def test_lenses_na_only_with_d_limit():
    obj = json.loads((FIX / "lenses-example.json").read_text(encoding="utf-8"))
    bad = copy.deepcopy(obj)
    bad["L4"]["F3"]["v"] = "NA"
    assert v.check("lenses", bad)
    bad["evidence_limit"] = "D (closed product)"
    assert v.check("lenses", bad) == []


def test_lenses_l2_null_and_design_l5():
    obj = json.loads((FIX / "lenses-example.json").read_text(encoding="utf-8"))
    obj["L2"] = None
    obj["basis"] = "design"
    obj["L5"] = {"T1": None, "T2": None, "T3": None, "reason": "not measurable (design)"}
    assert v.check("lenses", obj) == []


def test_lenses_missing_feature_fails():
    obj = json.loads((FIX / "lenses-example.json").read_text(encoding="utf-8"))
    del obj["L4"]["F34"]
    assert v.check("lenses", obj)


def test_baseline_lenses_conform():
    from engine import baseline
    d = baseline.round_dir(ROOT) / "lenses"
    for f in sorted(d.glob("*.json")):
        assert v.check("lenses", json.loads(f.read_text(encoding="utf-8"))) == [], f.name


def test_cli_validate_file(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps(card()))
    r = subprocess.run([sys.executable, "-m", "engine", "validate", "scorecard", str(f)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    bad = card()
    del bad["scores"]["C7"]
    f.write_text(json.dumps(bad))
    r = subprocess.run([sys.executable, "-m", "engine", "validate", "scorecard", str(f)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 1


def test_cli_validate_registry_still_works():
    r = subprocess.run([sys.executable, "-m", "engine", "validate", "registry"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
