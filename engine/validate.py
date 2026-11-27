"""`engine validate <kind> [file]`: the registry rules (plan §3.1) and a JSON Schema subset
(plan §7.6) applied to the documentation-grade schemas in `engine/schemas/`.

Supported keywords: type, required, properties, additionalProperties, enum, items,
minItems, maxItems, minimum, maximum, pattern, oneOf (on scalar types). Anything
else in a schema is a schema error, so a schema never silently means less than it says.
"""
import json
import pathlib
import re
import sys

from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK, EXIT_USAGE
from .miniyaml import MiniYamlError

SCHEMA_DIR = pathlib.Path(__file__).resolve().parent / "schemas"
METHODOLOGY_SHA256 = "a6e3953725b67db0189e188c1495ee9b54975e48f65c28baaa01f459b69cf9a4"
KEYWORDS = {"type", "required", "properties", "additionalProperties", "enum", "items", "minItems",
            "maxItems", "minimum", "maximum", "pattern", "oneOf", "description", "title", "$schema", "$id"}
_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


class SchemaError(Exception):
    pass


def schema_names():
    return sorted(p.name[:-len(".schema.json")] for p in SCHEMA_DIR.glob("*.schema.json"))


def load_schema(name):
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(obj, schema, where="$"):
    """Return a list of error strings; empty when obj conforms."""
    errors = []
    unknown = set(schema) - KEYWORDS
    if unknown:
        raise SchemaError(f"unsupported keyword(s) at {where}: {sorted(unknown)}")
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_TYPES[x](obj) for x in types):
            return [f"{where}: expected {'|'.join(types)}"]
    if "enum" in schema and obj not in schema["enum"]:
        errors.append(f"{where}: {obj!r} not in {schema['enum']}")
    if "oneOf" in schema:
        n = sum(1 for s in schema["oneOf"] if not validate(obj, s, where))
        if n != 1:
            errors.append(f"{where}: must match exactly one of oneOf (matched {n})")
    if _TYPES["number"](obj):
        if "minimum" in schema and obj < schema["minimum"]:
            errors.append(f"{where}: {obj} < minimum {schema['minimum']}")
        if "maximum" in schema and obj > schema["maximum"]:
            errors.append(f"{where}: {obj} > maximum {schema['maximum']}")
    if isinstance(obj, str) and "pattern" in schema and not re.search(schema["pattern"], obj):
        errors.append(f"{where}: does not match {schema['pattern']}")
    if isinstance(obj, list):
        if "minItems" in schema and len(obj) < schema["minItems"]:
            errors.append(f"{where}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(obj) > schema["maxItems"]:
            errors.append(f"{where}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, v in enumerate(obj):
                errors += validate(v, schema["items"], f"{where}[{i}]")
    if isinstance(obj, dict):
        for k in schema.get("required", []):
            if k not in obj:
                errors.append(f"{where}: missing {k}")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for k, v in obj.items():
            if k in props:
                errors += validate(v, props[k], f"{where}.{k}")
            elif extra is False:
                errors.append(f"{where}: unexpected property {k}")
            elif isinstance(extra, dict):
                errors += validate(v, extra, f"{where}.{k}")
    return errors


# ------------------------------------------------------------------ rules a schema cannot express

def scorecard_rules(card):
    """Cross-field constraints of the scorecard block (plan §7.6). Errors only."""
    errors = []
    if card.get("methodology_sha256") != METHODOLOGY_SHA256:
        errors.append("methodology_sha256 is not the frozen methodology hash")
    for c in CRITERIA:
        cell = (card.get("scores") or {}).get(c)
        if not isinstance(cell, dict):
            continue
        s, r, ra = cell.get("s"), cell.get("r", 1.0), cell.get("ra")
        if isinstance(s, int) and isinstance(r, (int, float)) and ra is not None and abs(ra - round(s * r, 2)) > 1e-9:
            errors.append(f"{c}: ra must equal round(s*r, 2) = {round(s * r, 2)}")
        if cell.get("ev") == "S" and isinstance(s, int) and s > 2:
            errors.append(f"{c}: evidence S caps the score at 2")
    return errors


def lenses_rules(lenses):
    errors = []
    lim = str(lenses.get("evidence_limit", ""))
    for f, cell in (lenses.get("L4") or {}).items():
        if isinstance(cell, dict) and cell.get("v") == "NA" and not lim.startswith("D"):
            errors.append(f"{f}: 'NA' is allowed only when evidence_limit starts with D")
    return errors


RULES = {"scorecard": scorecard_rules, "lenses": lenses_rules}


def check(kind, obj):
    """Schema plus cross-field rules for one kind."""
    errors = validate(obj, load_schema(kind))
    if not errors and kind in RULES:
        errors += RULES[kind](obj)
    return errors


# ------------------------------------------------------------------ CLI

def configure(p):
    p.add_argument("kind", help="registry, or a schema name: " + ", ".join(schema_names()))
    p.add_argument("file", nargs="?", help="JSON file to validate (not for registry)")
    p.add_argument("--root", default=".")
    p.add_argument("--no-files", action="store_true", help="registry: skip checks that need baseline/ files")


def _registry(args):
    from . import registry
    try:
        reg = registry.load_registry(args.root)
    except MiniYamlError as e:
        print(f"validate registry: {e}", file=sys.stderr)
        return EXIT_GATE
    except OSError:
        print("validate registry: references/registry.yaml not found", file=sys.stderr)
        return EXIT_USAGE
    errors = registry.validate(reg, args.root, check_files=not args.no_files)
    for e in errors:
        print(f"validate registry: {e}", file=sys.stderr)
    if errors:
        return EXIT_GATE
    print(f"validate registry: {len(registry.entries(reg))} entries valid")
    return EXIT_OK


def run(args):
    if args.kind == "registry":
        return _registry(args)
    if args.kind not in schema_names():
        print(f"validate: unknown kind {args.kind}", file=sys.stderr)
        return EXIT_USAGE
    if not args.file:
        print("validate: a file is required", file=sys.stderr)
        return EXIT_USAGE
    p = pathlib.Path(args.file)
    if not p.exists():
        print("validate: file not found", file=sys.stderr)
        return EXIT_MISSING
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"validate {args.kind}: invalid JSON ({e})", file=sys.stderr)
        return EXIT_GATE
    errors = check(args.kind, obj)
    for e in errors:
        print(f"validate {args.kind}: {e}", file=sys.stderr)
    if errors:
        return EXIT_GATE
    print(f"validate {args.kind}: valid")
    return EXIT_OK
