"""Leak gate (plan §7.14): private terms, home paths, emails, credential shapes,
URLs with userinfo, and CC BY-SA text.

Output hygiene (#50): hits are printed as `location:line: pattern-id`, where the
id is index-based (`deny#<n>`, `builtin:<name>`, `ccbysa:shingle`,
`ccbysa:quote`). No term, no regex source and no matched text is printed,
except with `--show` on an interactive TTY outside CI.

Pattern sources below are assembled from fragments on purpose, so this file
does not match its own built-in patterns.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

from .common import EXIT_OK, EXIT_LEAK, EXIT_MISSING, EXIT_USAGE

SKIP_DIRS = {".git", ".venv", "venv", ".cache", "__pycache__", "node_modules", ".pytest_cache", "dist"}
DEFAULT_DENYLIST = ".leakcheck/denylist.txt"
DEFAULT_ALLOWLIST = ".leakcheck/allowlist.txt"
DEFAULT_CCBYSA_CORPUS = ".cache/refs/agile-v"
CCBYSA_CITATION = "cache:" + "agile-v/"
# Standard licence texts are not the CC BY-SA work itself; they are excluded from the corpus.
LICENCE_FILES = ("LICENSE", "LICENCE", "COPYING", "NOTICE")
SHINGLE = 12
QUOTE_MIN_WORDS = 5
CORPUS_EXT = {".md", ".mdc", ".markdown", ".txt", ".yaml", ".yml", ".toml", ".json", ".csv", ".xml",
              ".py", ".sh", ".js", ".ts", ""}

_H = "Us" + "ers"
_E = "@"
BUILTINS = [
    ("home-path", re.compile("/(?:" + _H + "|home)/[A-Za-z0-9._-]+")),
    ("home-path-win", re.compile(r"[A-Za-z]:\\" + _H + r"\\")),
    ("email", re.compile(r"(?<![\w.+-])([A-Za-z0-9._%+-]+)" + _E + r"([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")),
    ("github-token", re.compile("gh" + r"p_[A-Za-z0-9]{20,}")),
    ("github-pat", re.compile("github" + r"_pat_[A-Za-z0-9_]{20,}")),
    ("gitlab-token", re.compile("gl" + r"pat-[A-Za-z0-9_-]{20,}")),
    ("slack-token", re.compile("xo" + r"x[bp]-[A-Za-z0-9-]{10,}")),
    ("aws-key", re.compile("AK" + r"IA[0-9A-Z]{16}")),
    ("private-key", re.compile("-----" + "BEGIN " + r"(?:[A-Z]+ )*PRIVATE KEY-----")),
    ("url-userinfo", re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@\"'<>]+(?::[^/\s@\"'<>]*)?" + _E + r"[A-Za-z0-9.-]+")),
]
# Non-personal addresses that are part of normal git practice.
_EMAIL_OK_LOCAL = {"noreply", "git"}
_EMAIL_OK_DOMAIN_SUFFIX = ("users.noreply.github.com",)


def quiet_mode(args):
    return bool(os.environ.get("CI")) or getattr(args, "ci", False) or not sys.stdout.isatty()


# ---------------------------------------------------------------- denylist

def parse_denylist(text):
    """Return a list of (index, compiled regex). Index is the 1-based line number."""
    entries = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"\s+#.*$", "", line)
        if line.startswith("cs:"):
            entries.append((n, re.compile(r"(?<!\w)" + re.escape(line[3:].strip()) + r"(?!\w)")))
        elif line.startswith("re:"):
            entries.append((n, re.compile(line[3:].strip())))
        else:
            term = line[3:] if line.startswith("ci:") else line
            entries.append((n, re.compile(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", re.IGNORECASE)))
    return entries


def load_denylist(path):
    return parse_denylist(pathlib.Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- matching

def _email_ok(m):
    local, domain = m.group(1).lower(), m.group(2).lower()
    return local in _EMAIL_OK_LOCAL or domain.endswith(_EMAIL_OK_DOMAIN_SUFFIX)


def scan_line(line, deny):
    """Yield pattern ids that hit this line."""
    for name, rx in BUILTINS:
        for m in rx.finditer(line):
            if name == "email" and _email_ok(m):
                continue
            if name == "url-userinfo" and m.group(0).split("://", 1)[1].startswith("git" + _E):
                continue
            yield f"builtin:{name}"
            break
    for idx, rx in deny:
        if rx.search(line):
            yield f"deny#{idx}"


def scan_text(text, deny):
    """Return [(line_no, pattern_id, line_text)]."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for pid in scan_line(line, deny):
            hits.append((n, pid, line))
    return hits


# ---------------------------------------------------------------- CC BY-SA

_WORD = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")


def _words_with_lines(text):
    out = []
    for n, line in enumerate(text.lower().splitlines(), 1):
        out.extend((w, n) for w in _WORD.findall(line))
    return out


def _shingle_key(words):
    return hashlib.blake2b(" ".join(words).encode(), digest_size=8).digest()


def build_corpus(root):
    root = pathlib.Path(root)
    keys = set()
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.suffix.lower() not in CORPUS_EXT or p.name.upper().startswith(LICENCE_FILES):
            continue
        text = _read_text(p.read_bytes())
        if text is None:
            continue
        ws = [w for w, _ in _words_with_lines(text)]
        for i in range(len(ws) - SHINGLE + 1):
            keys.add(_shingle_key(ws[i:i + SHINGLE]))
    return keys


def scan_shingles(text, corpus):
    wl = _words_with_lines(text)
    hits, last = [], -1
    for i in range(len(wl) - SHINGLE + 1):
        if _shingle_key([w for w, _ in wl[i:i + SHINGLE]]) in corpus:
            line = wl[i][1]
            if line != last:
                hits.append((line, "ccbysa:shingle", ""))
                last = line
    return hits


_QUOTES = [re.compile(r'"([^"\n]+)"'), re.compile("“([^”\n]+)”"),
           re.compile(r"(?<!\w)'([^'\n]+)'(?!\w)")]
_JSON_STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def _has_long_quote(s):
    for rx in _QUOTES:
        for m in rx.finditer(s):
            if len(_WORD.findall(m.group(1).lower())) >= QUOTE_MIN_WORDS:
                return True
    return False


def scan_quotes(text, is_json):
    """Quoted spans of 5+ words inside a unit that cites the CC BY-SA cache."""
    hits = []
    lines = text.splitlines()
    if is_json:
        for n, line in enumerate(lines, 1):
            for m in _JSON_STR.finditer(line):
                try:
                    s = json.loads('"' + m.group(1) + '"')
                except ValueError:
                    s = m.group(1)
                if CCBYSA_CITATION in s and _has_long_quote(s):
                    hits.append((n, "ccbysa:quote", ""))
                    break
        return hits
    start, block = 1, []
    for n, line in enumerate(lines + [""], 1):
        if line.strip():
            if not block:
                start = n
            block.append(line)
            continue
        if block:
            para = "\n".join(block)
            if CCBYSA_CITATION in para:
                quoted = _has_long_quote(para) or any(
                    b.lstrip().startswith(">") and len(_WORD.findall(b.lower())) >= QUOTE_MIN_WORDS for b in block)
                if quoted:
                    hits.append((start, "ccbysa:quote", ""))
            block = []
    return hits


# ---------------------------------------------------------------- sources

def _read_text(data):
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def _git(args, cwd, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    if check and r.returncode != 0:
        raise RuntimeError("git " + args[0] + " failed: " + r.stderr.decode(errors="replace").strip())
    return r.stdout


def git_toplevel(path):
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True)
    return pathlib.Path(r.stdout.strip()) if r.returncode == 0 else None


def load_allowlist(root):
    p = pathlib.Path(root) / DEFAULT_ALLOWLIST
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def _allowed(rel, allow):
    return any(rel == a.rstrip("/") or rel.startswith(a.rstrip("/") + "/") for a in allow)


def iter_path_files(target):
    """Yield (display path, bytes) for a file or directory. In a git work tree
    only tracked and untracked-but-not-ignored files are scanned."""
    target = pathlib.Path(target)
    if target.is_file():
        yield target.as_posix(), target.read_bytes()
        return
    top = git_toplevel(target)
    allow = load_allowlist(top) if top else []
    if top is not None:
        out = _git(["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "."], cwd=target)
        for rel in sorted({r for r in out.decode().split("\0") if r}):
            p = target / rel
            full_rel = p.resolve().relative_to(top.resolve()).as_posix()
            if _allowed(full_rel, allow) or full_rel == DEFAULT_DENYLIST or not p.is_file():
                continue
            yield p.relative_to(target).as_posix() if target != pathlib.Path(".") else rel, p.read_bytes()
        return
    for p in sorted(target.rglob("*")):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(target).parts):
            yield p.relative_to(target).as_posix(), p.read_bytes()


def _blob_reader(repo):
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read(sha):
        proc.stdin.write(sha.encode() + b"\n")
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) < 3:
            return b""
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        return data

    return proc, read


def iter_commit_objects(repo, commits, include_index=False, only_new_from=None):
    """Yield (display, bytes) for every blob in the trees of `commits` (each blob
    once) and every commit message; optionally the index too.

    With `only_new_from=<revs>`, blobs are limited to those reachable from
    <revs> and not from any remote (`git rev-list --objects ... --not --remotes`),
    so content that is already public is not re-scanned on every push."""
    allow = load_allowlist(repo)
    seen = set()
    new_blobs = None
    if only_new_from is not None:
        new_blobs = {}
        if only_new_from:
            out = _git(["rev-list", "--objects", "--filter=object:type=blob", "--filter-provided-objects",
                        *only_new_from, "--not", "--remotes"], cwd=repo, check=False).decode()
            for row in out.splitlines():
                parts = row.split(" ", 1)
                if len(parts) == 2:
                    new_blobs.setdefault(parts[0], parts[1])
    proc, read = _blob_reader(repo)
    try:
        if include_index:
            for row in _git(["ls-files", "-s", "-z"], cwd=repo).decode().split("\0"):
                if not row:
                    continue
                meta, path = row.split("\t", 1)
                sha = meta.split()[1]
                if sha in seen or _allowed(path, allow) or path == DEFAULT_DENYLIST:
                    continue
                seen.add(sha)
                yield f"index:{path}", read(sha)
        for c in commits:
            yield f"{c[:10]}:message", _git(["log", "-1", "--format=%B", c], cwd=repo)
            for row in _git(["ls-tree", "-r", "-z", c], cwd=repo).decode().split("\0"):
                if not row:
                    continue
                meta, path = row.split("\t", 1)
                kind, sha = meta.split()[1], meta.split()[2]
                if kind != "blob" or sha in seen or _allowed(path, allow) or path == DEFAULT_DENYLIST:
                    continue
                if new_blobs is not None and sha not in new_blobs:
                    continue
                seen.add(sha)
                yield f"{c[:10]}:{path}", read(sha)
    finally:
        proc.stdin.close()
        proc.wait()


def unpushed_commits(repo, revs=("HEAD",)):
    out = _git(["rev-list", *revs, "--not", "--remotes"], cwd=repo, check=False).decode()
    return [c for c in out.split() if c]


def all_commits(repo):
    return [c for c in _git(["rev-list", "--all"], cwd=repo).decode().split() if c]


# ---------------------------------------------------------------- driver

def _safe_display(display, deny):
    """A location string that itself matches a pattern is replaced by a hash."""
    if list(scan_line(display, deny)):
        return "path#" + hashlib.sha1(display.encode()).hexdigest()[:10]
    return display


def scan_objects(objects, deny, corpus=None, quotes=False):
    """objects: iterable of (display, bytes). Returns [(display, line, id, text)]."""
    hits = []
    for display, data in objects:
        text = _read_text(data)
        shown = _safe_display(display, deny)
        if shown != display:
            hits.append((shown, 0, "path-match", ""))
        if text is None:
            continue
        found = scan_text(text, deny)
        if corpus is not None:
            found += scan_shingles(text, corpus)
        if quotes:
            found += scan_quotes(text, display.endswith(".json"))
        hits.extend((shown, n, pid, line) for n, pid, line in found)
    return hits


def report(hits, show=False, out=sys.stdout, err=sys.stderr):
    counts = {}
    for display, n, pid, text in hits:
        counts[pid] = counts.get(pid, 0) + 1
        line = f"{display}:{n}: {pid}"
        if show and text:
            line += f"  | {text.strip()[:160]}"
        print(line, file=out)
    if hits:
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        print(f"leakcheck: {len(hits)} hit(s): {summary}", file=err)
    else:
        print("leakcheck: no hits", file=err)


def configure(p):
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", help="scan a run (requires the run layer; not built yet)")
    mode.add_argument("--path", help="file or directory to scan")
    mode.add_argument("--staged-and-unpushed", action="store_true",
                      help="scan the index and every commit not on any remote")
    mode.add_argument("--git-history", action="store_true",
                      help="scan every blob of every commit on every ref, and commit messages")
    p.add_argument("--denylist", help="owner denylist file (never committed)")
    p.add_argument("--ccbysa", action="store_true", help="also run the CC BY-SA detectors")
    p.add_argument("--ccbysa-corpus", default=None, help=f"CC BY-SA corpus (default {DEFAULT_CCBYSA_CORPUS})")
    p.add_argument("--ccbysa-allow-missing", action="store_true",
                   help="warn and skip the shingle detector when the corpus is absent (pre-push only)")
    p.add_argument("--rev", action="append", default=None, help="revisions for --staged-and-unpushed")
    p.add_argument("--ci", action="store_true", help="CI output mode (ids only)")
    p.add_argument("--show", action="store_true", help="show excerpts (interactive TTY only)")


def run(args):
    if args.run:
        print("leakcheck --run: needs the run layer (Phase 2); not implemented", file=sys.stderr)
        return EXIT_USAGE
    deny = []
    if args.denylist:
        if not pathlib.Path(args.denylist).exists():
            print("leakcheck: denylist file not found", file=sys.stderr)
            return EXIT_MISSING
        try:
            deny = load_denylist(args.denylist)
        except re.error:
            print("leakcheck: a denylist regex does not compile", file=sys.stderr)
            return EXIT_USAGE
    corpus = None
    if args.ccbysa:
        cpath = pathlib.Path(args.ccbysa_corpus or DEFAULT_CCBYSA_CORPUS)
        if cpath.is_dir():
            corpus = build_corpus(cpath)
            if not corpus:
                print("leakcheck: CC BY-SA corpus is empty", file=sys.stderr)
                return EXIT_MISSING
        elif args.ccbysa_allow_missing:
            print("leakcheck: warning: CC BY-SA corpus absent; shingle detector skipped locally "
                  "(CI enforces it)", file=sys.stderr)
        else:
            print("leakcheck: CC BY-SA corpus absent; fetch it or pass --ccbysa-corpus", file=sys.stderr)
            return EXIT_MISSING
    if args.path:
        if not pathlib.Path(args.path).exists():
            print("leakcheck: path not found", file=sys.stderr)
            return EXIT_MISSING
        objects = iter_path_files(args.path)
    else:
        repo = git_toplevel(".")
        if repo is None:
            print("leakcheck: not a git repository", file=sys.stderr)
            return EXIT_USAGE
        if args.git_history:
            objects = iter_commit_objects(repo, all_commits(repo))
        else:
            revs = args.rev or ["HEAD"]
            objects = iter_commit_objects(repo, unpushed_commits(repo, revs), include_index=True, only_new_from=revs)
    hits = scan_objects(objects, deny, corpus=corpus, quotes=args.ccbysa)
    show = args.show and not quiet_mode(args) and sys.stdin.isatty()
    report(hits, show=show)
    return EXIT_LEAK if hits else EXIT_OK
