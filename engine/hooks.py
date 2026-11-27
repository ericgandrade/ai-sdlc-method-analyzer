"""Git hook management (plan §7.14 "Pre-push behaviour", #51).

`engine hooks install [--maintainer]` sets `core.hooksPath=.githooks`.
`--maintainer` requires the owner denylist and sets `ama.maintainer=true`.

`engine hooks pre-push <remote> [<url>]` is what `.githooks/pre-push` runs. It
reads git's pre-push lines from stdin and scans every commit reachable from a
pushed ref that is not on any remote, plus commit messages.
"""
import pathlib
import subprocess
import sys

from . import leakcheck
from .common import EXIT_GATE, EXIT_LEAK, EXIT_MISSING, EXIT_OK, EXIT_USAGE

ZERO = "0" * 40


def _git_config(repo, key):
    r = subprocess.run(["git", "config", "--get", key], cwd=repo, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def is_maintainer(repo):
    return _git_config(repo, "ama.maintainer").lower() == "true"


def install(repo, maintainer=False):
    repo = pathlib.Path(repo)
    if maintainer and not (repo / leakcheck.DEFAULT_DENYLIST).exists():
        print("hooks install --maintainer: the owner denylist .leakcheck/denylist.txt is missing", file=sys.stderr)
        return EXIT_MISSING
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo, check=True)
    if maintainer:
        subprocess.run(["git", "config", "ama.maintainer", "true"], cwd=repo, check=True)
    print("hooks: core.hooksPath=.githooks" + (" (maintainer)" if maintainer else ""))
    return EXIT_OK


def pushed_shas(stdin_text):
    """Local shas of git's pre-push stdin lines, skipping branch deletions."""
    shas = []
    for line in stdin_text.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[1] == ZERO:      # malformed, or a branch deletion
            continue
        shas.append(parts[1])
    return shas


def pre_push(repo, stdin_text):
    repo = pathlib.Path(repo)
    deny_path = repo / leakcheck.DEFAULT_DENYLIST
    deny = []
    if deny_path.exists():
        deny = leakcheck.load_denylist(deny_path)
    elif is_maintainer(repo):
        print("pre-push: refused. This is a maintainer clone (ama.maintainer=true) and "
              ".leakcheck/denylist.txt is missing.", file=sys.stderr)
        return EXIT_GATE
    else:
        print("pre-push: notice: no local denylist; the denylist scan runs in CI and on the "
              "maintainer's clone. Built-in patterns still run.", file=sys.stderr)
    corpus_dir = repo / leakcheck.DEFAULT_CCBYSA_CORPUS
    corpus = None
    if corpus_dir.is_dir():
        corpus = leakcheck.build_corpus(corpus_dir)
    else:
        print("pre-push: warning: CC BY-SA corpus absent; shingle detector skipped locally "
              "(CI enforces it).", file=sys.stderr)
    shas = pushed_shas(stdin_text)
    commits = leakcheck.unpushed_commits(repo, shas) if shas else []
    objects = leakcheck.iter_commit_objects(repo, commits, only_new_from=shas)
    hits = leakcheck.scan_objects(objects, deny, corpus=corpus, quotes=True)
    leakcheck.report(hits, show=False, out=sys.stderr)
    if hits:
        print("pre-push: refused (leak gate).", file=sys.stderr)
        return EXIT_LEAK
    print(f"pre-push: {len(commits)} commit(s) scanned, clean.", file=sys.stderr)
    return EXIT_OK


def configure(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    i = sub.add_parser("install", help="set core.hooksPath=.githooks")
    i.add_argument("--maintainer", action="store_true", help="require the owner denylist; set ama.maintainer")
    pp = sub.add_parser("pre-push", help="run by .githooks/pre-push")
    pp.add_argument("remote", nargs="?")
    pp.add_argument("url", nargs="?")


def run(args):
    repo = leakcheck.git_toplevel(".")
    if repo is None:
        print("hooks: not a git repository", file=sys.stderr)
        return EXIT_USAGE
    if args.action == "install":
        return install(repo, args.maintainer)
    return pre_push(repo, sys.stdin.read())
