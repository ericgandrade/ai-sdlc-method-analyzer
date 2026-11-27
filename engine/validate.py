"""`engine validate <kind>`. Only `registry` exists so far; JSON schemas arrive in Task 2.2."""
import sys

from .common import EXIT_GATE, EXIT_OK, EXIT_USAGE
from .miniyaml import MiniYamlError


def configure(p):
    p.add_argument("kind", choices=["registry"], help="what to validate")
    p.add_argument("--root", default=".")
    p.add_argument("--no-files", action="store_true", help="skip checks that need baseline/ files")


def run(args):
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
