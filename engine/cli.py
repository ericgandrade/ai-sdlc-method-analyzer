"""Command-line entry point: `python -m engine <command> [options]`.

Each implemented command lives in its own module, which exposes
`configure(parser)` (adds the command's arguments) and `run(args) -> int`
(returns an exit code from `common`). Planned commands that are not built
yet are registered too, so `--help` lists the whole surface; they exit 2
with "not implemented".
"""
import argparse
import importlib
import sys

from .common import EXIT_USAGE

# command name -> module name (implemented commands)
IMPLEMENTED = {
    "leakcheck": "leakcheck",
    "hooks": "hooks",
    "verify-freeze": "freeze",
}

# command name -> one-line help (every command of plan §7, in plan order)
COMMANDS = {
    "fetch": "clone references at their pins (network)",
    "intake": "snapshot a target into a run (network for --mode git)",
    "isolate": "build sealed scorer folders",
    "inventory": "list a method's files with word counts",
    "shuffle": "seeded shuffle of lines",
    "validate": "validate a JSON or registry file against its schema",
    "scorecard": "extract and validate a scorecard's machine block",
    "calibration": "calibration deltas against the baseline",
    "reconcile": "reconcile two scorers' sheets",
    "alpha": "Krippendorff's alpha over pre-reconciliation ratings",
    "audit-scope": "select the cells the red team must contest",
    "apply-audit": "apply audit overrides",
    "tokens": "static token counts (L5)",
    "consolidate": "totals and uncertainty per profile",
    "rank": "ranking per profile",
    "sensitivity": "weight sensitivity and P(first)",
    "superiority": "superiority test (methodology section 9)",
    "ranges": "documentation-only floor, centre and ceiling",
    "lineage": "lineage similarity between methods",
    "fitgap": "fit-gap and roadmap data",
    "leakcheck": "scan for private terms, secrets and CC BY-SA text",
    "state": "run state: init, next, start, done, fail, close, ...",
    "baseline": "verify or promote the shipped baseline",
    "verify-freeze": "verify the SHA-256 freeze records",
    "setup": "write or check host settings",
    "tty-check": "report whether this terminal is interactive",
    "log": "append to a run's engine-owned log",
    "answers": "append owner answers to a run",
    "estimate": "read-only cost estimate for a source",
    "adjudication": "request or import a person's adjudication",
    "hooks": "install the git pre-push leak scan",
    "report": "render the HTML and Markdown report",
    "slides": "render the slide deck",
    "read": "print a file under the snapshot or the cache",
    "list": "list files with word counts",
    "convert": "convert documentation to text",
    "git-log": "read-only git log",
    "git-show": "read-only git show",
    "git-ls": "read-only git ls-tree",
    "build-plugin": "copy briefs into dist/plugin/",
}


def _not_implemented(args):
    print(f"engine {args.command}: not implemented", file=sys.stderr)
    return EXIT_USAGE


def build_parser():
    parser = argparse.ArgumentParser(prog="python -m engine",
                                     description="Deterministic engine of ai-sdlc-method-analyzer.")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True
    for name, help_text in COMMANDS.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        module_name = IMPLEMENTED.get(name)
        if module_name:
            module = importlib.import_module(f".{module_name}", __package__)
            module.configure(p)
            p.set_defaults(func=module.run)
        else:
            p.add_argument("rest", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
            p.set_defaults(func=_not_implemented)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)
