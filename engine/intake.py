"""Intake, isolation, inventory, shuffle and estimate (plan §7.5, §6.5).

`intake` snapshots the target into runs/<id>/target/ (folder, git) or runs/<id>/docs/
(docs), or verifies a cached reference (reference). User strings arrive only through
run:requests/intake/intake-request.json, which is deleted after reading on success and
failure alike (#77, #88). No absolute path is ever persisted.
"""
import hashlib
import html.parser
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import threading
import time

from . import paths
from .common import CRITERIA, EXIT_GATE, EXIT_INTEGRITY, EXIT_MISSING, EXIT_OFFLINE, EXIT_OK, EXIT_USAGE
from .jsonio import normalized_bytes, read_json, write_json

SKIP_COPY = {".git", "node_modules", "__pycache__", ".venv", "venv"}
SIZE_WARN_BYTES = 200 * 1024 * 1024
TEXT_EXT = {".md", ".mdc", ".markdown", ".yaml", ".yml", ".toml", ".txt", ".json", ".csv", ".xml"}
INVENTORY_EXT = TEXT_EXT | {".mdx", ".py", ".sh", ".bash", ".ps1", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".rb",
                            ".go", ".rs", ".java", ".html", ".htm", ".css", ".cfg", ".ini", ".sql"}
SELF_SCORE_WORDS = ("score", "scorecard", "benchmark", "evaluation", "rubric", "ranking")
REQUEST = "run:requests/intake/intake-request.json"
STALL_DEFAULT = 120
GIT_AUTH_HELP = (
    "git could not authenticate or stalled. 1) For SSH, load the key into an agent with `ssh-add <key>` "
    "(BatchMode is on, so a passphrase-protected key works only when loaded); for HTTPS, configure a "
    "credential helper. 2) Verify with `GIT_TERMINAL_PROMPT=0 git ls-remote <url>` (PowerShell: "
    "`$env:GIT_TERMINAL_PROMPT=0; git ls-remote <url>`). 3) Retry.")


class IntakeError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ walking and hashing

def _is_venv(d):
    return (pathlib.Path(d) / "pyvenv.cfg").exists()


def walk(root, skip_build=False):
    """Yield (relposix, Path, kind) under root, never following symlinks. kind: file | link.
    skip_build excludes dist/ and build/ directories (used only with a declared shipped root)."""
    root = pathlib.Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dp = pathlib.Path(dirpath)
        keep = []
        for d in sorted(dirnames):
            full = dp / d
            if full.is_symlink():
                yield full.relative_to(root).as_posix(), full, "link"
            elif d in SKIP_COPY or _is_venv(full) or (skip_build and d in ("dist", "build")):
                continue
            else:
                keep.append(d)
        dirnames[:] = keep
        for f in sorted(filenames):
            full = dp / f
            yield full.relative_to(root).as_posix(), full, ("link" if full.is_symlink() else "file")


def skip_build_for(shipped_root):
    """dist/ and build/ are skipped for T0 and inventory only when a declared shipped root lies outside them."""
    if not shipped_root:
        return False
    first = pathlib.PurePosixPath(shipped_root.rstrip("/")).parts[:1]
    return not (first and first[0] in ("dist", "build"))


def file_sha(p):
    return hashlib.sha256(normalized_bytes(pathlib.Path(p).read_bytes())).hexdigest()


def tree_hash(root):
    """`tree:<sha256>` over sorted `relpath  sha256(LF-normalized bytes)` lines; links as `link:<kind>`."""
    lines = []
    root = pathlib.Path(root)
    for rel, full, kind in walk(root):
        lines.append(f"{rel}  {file_sha(full) if kind == 'file' else 'link'}")
    return "tree:" + hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def _link_kind(link, src_root):
    try:
        target = pathlib.Path(os.path.realpath(link))
    except OSError:
        return "broken"
    if not target.exists():
        return "broken"
    return "internal" if paths.amahome.is_inside(target, src_root) else "external"


def copy_tree(src, dest, accept_large=False, interactive=False):
    """Complete copy (#53): everything except .git, node_modules, __pycache__ and virtual envs.
    Symlinks are recorded, never followed or copied as content."""
    src, dest = pathlib.Path(src), pathlib.Path(dest)
    items = list(walk(src))
    size = sum(f.stat().st_size for _, f, k in items if k == "file")
    if size > SIZE_WARN_BYTES:
        print(f"intake: warning: the copy is {size // (1024 * 1024)} MB (over 200 MB)", file=sys.stderr)
        ok = accept_large or (interactive and input("Continue? [y/N] ").strip().lower() == "y")
        if not ok:
            raise IntakeError("copy over 200 MB not confirmed (set accept_large in the request to continue)")
    links, n = [], 0
    for rel, full, kind in items:
        if kind == "link":
            links.append({"path": rel, "kind": _link_kind(full, src)})
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full, out)
        n += 1
    dest.mkdir(parents=True, exist_ok=True)
    return links, n, size


# ------------------------------------------------------------------ detection

def self_score_candidates(root):
    """Prior-score files (path words) and README sections that report a score (§5.2 step 3)."""
    out = []
    for rel, full, kind in walk(root):
        if kind != "file":
            continue
        low = rel.lower()
        if any(w in low for w in SELF_SCORE_WORDS):
            out.append(rel)
        elif pathlib.PurePosixPath(low).name.startswith("readme") and full.suffix.lower() in (".md", ".markdown", ""):
            text = full.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"^#{1,6}\s+(.*\bscor(?:e|es|ing)\b.*)$", text, re.I | re.M):
                out.append(f"{rel}#{slugify(m.group(1))}")
    return sorted(set(out))


_CID = re.compile(r"\bC(1[0-6]|[1-9])\b")
_FID = re.compile(r"\bF(3[0-4]|[12][0-9]|[1-9])\b")


def rubric_ids(root, min_distinct=5):
    """Files citing at least `min_distinct` distinct criterion (C1–C16) or feature (F1–F34) IDs."""
    files, cs, fs = [], set(), set()
    for rel, full, kind in walk(root):
        if kind != "file" or full.suffix.lower() not in INVENTORY_EXT:
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        c = {f"C{m}" for m in _CID.findall(text)}
        f = {f"F{m}" for m in _FID.findall(text)}
        if len(c) >= min_distinct or len(f) >= min_distinct:
            files.append(rel)
            cs |= c
            fs |= f
    key = lambda s: int(s[1:])
    return {"revised_against_rubric": bool(files), "files": files,
            "criteria": sorted(cs, key=key), "features": sorted(fs, key=key)}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ------------------------------------------------------------------ docs conversion

class _HTMLText(html.parser.HTMLParser):
    DROP = {"script", "style", "nav", "footer", "noscript", "template"}
    BLOCK = {"p", "div", "li", "tr", "br", "section", "article", "ul", "ol", "table", "pre", "blockquote", "dd", "dt"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.drop, self.heading, self.buf = [], 0, None, []

    def handle_starttag(self, tag, attrs):
        if tag in self.DROP:
            self.drop += 1
        elif not self.drop and re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.heading = tag
        elif not self.drop and tag in self.BLOCK:
            self._flush()
        elif not self.drop and tag in ("td", "th"):
            self.buf.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.DROP:
            self.drop = max(0, self.drop - 1)
        elif self.heading and tag == self.heading:
            title = " ".join("".join(self.buf).split())
            self.buf = []
            if title:
                self.out.append(f"<<{self.heading} {title}>>")
            self.heading = None
        elif tag in self.BLOCK:
            self._flush()

    def handle_data(self, data):
        if not self.drop:
            self.buf.append(data)

    def _flush(self):
        line = " ".join("".join(self.buf).split()).strip(" |")
        self.buf = []
        if line and not self.heading:
            self.out.append(line)

    def text(self):
        self._flush()
        return "\n".join(self.out) + "\n"


def html_to_text(s):
    p = _HTMLText()
    p.feed(s)
    p.close()
    return p.text()


def markdown_to_text(s):
    return re.sub(r"^(#{1,6})\s+(.*)$", lambda m: f"<<h{len(m.group(1))} {m.group(2).strip()}>>", s, flags=re.M)


def convert(path):
    """(text, pages) for a docs file. PDF needs pdftotext on PATH (exit 3 otherwise)."""
    p = pathlib.Path(path)
    suf = p.suffix.lower()
    if suf == ".pdf":
        exe = shutil.which("pdftotext")
        if not exe:
            raise IntakeError("pdftotext is not on PATH: export the PDF to text (or Markdown) and give that file instead",
                              EXIT_MISSING)
        r = subprocess.run([exe, "-layout", str(p), "-"], capture_output=True, shell=False, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            raise IntakeError("pdftotext failed on a docs file", EXIT_MISSING)
        pages = r.stdout.decode("utf-8", "replace").split("\f")
        if pages and not pages[-1].strip():
            pages = pages[:-1]
        return "".join(f"<<page {i}>>\n{t}" for i, t in enumerate(pages, 1)), len(pages)
    raw = p.read_bytes().decode("utf-8", "replace").replace("\r\n", "\n")
    if suf in (".html", ".htm"):
        return html_to_text(raw), 0
    if suf in (".md", ".markdown", ".mdx"):
        return markdown_to_text(raw), 0
    return raw, 0


# ------------------------------------------------------------------ git with a stall timeout (#79, #89)

class Stalled(Exception):
    pass


def stall_seconds():
    v = os.environ.get("AMA_GIT_STALL_SECONDS")
    if v:
        return float(v)
    try:
        return float(read_json(paths.data_dir() / "config.json").get("git_stall_seconds", STALL_DEFAULT))
    except (OSError, ValueError, AttributeError, paths.PathError):
        return STALL_DEFAULT


def run_with_stall(cmd, stall, env=None, cwd=None):
    """Run cmd; abort only when no stderr/stdout output arrives for `stall` seconds.
    Returns (returncode, captured stderr). Raises Stalled after killing the process."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                            env=env, cwd=cwd, shell=False)
    last = [time.monotonic()]
    err = []

    def pump(stream, keep):
        while True:
            chunk = stream.read1(256) if hasattr(stream, "read1") else stream.read(256)
            if not chunk:
                break
            last[0] = time.monotonic()
            if keep:
                err.append(chunk)

    threads = [threading.Thread(target=pump, args=(proc.stdout, False), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, True), daemon=True)]
    for t in threads:
        t.start()
    while proc.poll() is None:
        if time.monotonic() - last[0] > stall:
            proc.kill()
            proc.wait()
            raise Stalled()
        time.sleep(0.05)
    for t in threads:
        t.join(timeout=1)
    return proc.returncode, b"".join(err).decode("utf-8", "replace")


def git_clone(url, dest, ref=None):
    from .fetch import git_env, has_credentials
    if has_credentials(url):
        raise IntakeError("the URL embeds credentials; use a git credential helper instead", EXIT_USAGE)
    env = git_env()
    try:
        rc, err = run_with_stall(["git", "-c", "core.autocrlf=false", "clone", "--progress", url, str(dest)],
                                 stall_seconds(), env=env)
    except Stalled:
        shutil.rmtree(dest, ignore_errors=True)
        raise IntakeError("git clone stalled with no progress. " + GIT_AUTH_HELP, EXIT_MISSING)
    if rc != 0:
        shutil.rmtree(dest, ignore_errors=True)
        raise IntakeError("git clone failed. " + GIT_AUTH_HELP, EXIT_MISSING)
    if ref:
        r = subprocess.run(["git", "-C", str(dest), "-c", "advice.detachedHead=false", "checkout", "-q", ref],
                           capture_output=True, env=env, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            raise IntakeError(f"ref {ref!r} not found in the clone", EXIT_MISSING)
    r = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True, env=env,
                       stdin=subprocess.DEVNULL)
    return r.stdout.strip()


def git_head_and_dirty(folder):
    if not (pathlib.Path(folder) / ".git").exists() or shutil.which("git") is None:
        return None, False
    from .fetch import git_env
    h = subprocess.run(["git", "-C", str(folder), "rev-parse", "HEAD"], capture_output=True, text=True,
                       env=git_env(), stdin=subprocess.DEVNULL)
    s = subprocess.run(["git", "-C", str(folder), "status", "--porcelain"], capture_output=True, text=True,
                       env=git_env(), stdin=subprocess.DEVNULL)
    return (h.stdout.strip() or None), bool(s.stdout.strip())


# ------------------------------------------------------------------ intake

def _request(st, request):
    """Read and delete the intake request (always deleted, #88)."""
    from . import state
    if request != REQUEST:
        raise IntakeError(f"the intake request must be {REQUEST}", EXIT_USAGE)
    p = paths.resolve(request, run=state.run_path(st["run_id"]))
    try:
        if not p.exists():
            raise IntakeError("intake request not found", EXIT_MISSING)
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            raise IntakeError("intake request is not valid JSON")
        if not isinstance(obj, dict):
            raise IntakeError("intake request must be a JSON object")
        return obj
    finally:
        try:
            p.unlink()
        except OSError:
            pass


def _before_s01(st, rd):
    if st["stages"].get("S01", {}).get("status") == "done":
        raise IntakeError("intake is accepted only before S01 is done", EXIT_GATE)
    if (rd / "target.json").exists():
        raise IntakeError("this run already has a successful intake; start a new run", EXIT_GATE)


def intake(run_id, request=None, **cli):
    from . import state
    from .fetch import offline
    st = state.load(run_id)
    rd = state.run_path(run_id)
    try:
        req = _request(st, request) if request else {}
    except IntakeError:
        raise
    _before_s01(st, rd)
    opt = {**{k: v for k, v in cli.items() if v not in (None, False, [])}, **req}
    mode = opt.get("mode") or st["mode"]
    slug = opt.get("slug") or (st.get("target") or {}).get("slug")
    if mode not in ("folder", "git", "docs", "reference"):
        raise IntakeError(f"unknown intake mode {mode!r}", EXIT_USAGE)
    if mode != st["mode"]:
        raise IntakeError(f"run mode is {st['mode']}, intake asked for {mode}", EXIT_USAGE)
    if not slug or not paths.SLUG.match(slug):
        raise IntakeError("slug must be kebab-case", EXIT_USAGE)
    name = str(opt.get("name") or (st.get("target") or {}).get("name") or slug)
    ttype = opt.get("type") or (st.get("target") or {}).get("type") or "open"
    status = opt.get("status") or (st.get("target") or {}).get("status") or "implemented"
    rec = {"slug": slug, "name": name, "mode": mode, "type": ttype, "status": status, "dirty": False,
           "private": mode != "reference", "docs": [], "symlinks": []}
    if mode == "folder":
        src = pathlib.Path(str(opt.get("source") or ""))
        if not src.is_dir():
            raise IntakeError("source folder not found", EXIT_MISSING)
        print(f"intake: copying {src} (shown once, never stored)")
        tgt = rd / "target"
        if tgt.exists():
            shutil.rmtree(tgt)       # a retry after a failed intake starts clean (#94)
        links, n, size = copy_tree(src, tgt, accept_large=bool(opt.get("accept_large")),
                                   interactive=state.is_interactive())
        head, dirty = git_head_and_dirty(src)
        rec.update(root="target:", pin=tree_hash(tgt), git_head=head, dirty=dirty, symlinks=links, files=n, bytes=size)
    elif mode == "git":
        if offline(argparse_ns(opt)):
            raise IntakeError("network required but offline mode is on", EXIT_OFFLINE)
        url = str(opt.get("source") or "")
        tgt = rd / "target"
        if tgt.exists():
            shutil.rmtree(tgt)
        sha = git_clone(url, tgt, opt.get("ref"))
        rec.update(root="target:", pin=sha, git_head=sha, dirty=False)
    elif mode == "docs":
        files = opt.get("source") or []
        files = [files] if isinstance(files, str) else files
        if not files:
            raise IntakeError("docs mode needs at least one file", EXIT_MISSING)
        d = rd / "docs"
        d.mkdir(parents=True, exist_ok=True)
        hashes = []
        for f in files:
            p = pathlib.Path(str(f))
            if not p.is_file():
                raise IntakeError("a docs file was not found", EXIT_MISSING)
            shutil.copyfile(p, d / p.name)
            text, pages = convert(d / p.name)
            (d / "text").mkdir(exist_ok=True)
            (d / "text" / (p.name + ".txt")).write_text(text, encoding="utf-8", newline="\n")
            sha = hashlib.sha256((d / p.name).read_bytes()).hexdigest()
            hashes.append(sha)
            rec["docs"].append({"file": p.name, "sha256": sha, "pages": pages, "text": f"docs:text/{p.name}.txt"})
        rec.update(root="docs:", pin="docs:" + hashlib.sha256("\n".join(sorted(hashes)).encode()).hexdigest(),
                   type="docs" if ttype == "open" else ttype)
    else:
        from .fetch import head
        from .registry import entries, load_registry
        reg = {e["slug"]: e for e in entries(load_registry(paths.project_root()))}
        if slug not in reg:
            raise IntakeError(f"{slug} is not in the registry", EXIT_USAGE)
        e = reg[slug]
        cache = paths.refs_dir() / slug
        if not cache.is_dir():
            raise IntakeError(f"{slug} is not in the cache: run engine fetch --slug {slug}", EXIT_MISSING)
        if head(cache) != e["pin"]:
            raise IntakeError(f"cached {slug} is not at the registry pin", EXIT_INTEGRITY)
        rec.update(root=f"cache:{slug}", pin=e["pin"], type=e.get("type", ttype), name=e.get("name", name),
                   private=False)
    scan_root = {"target:": rd / "target", f"cache:{slug}": paths.refs_dir() / slug}.get(rec["root"], rd / "docs" / "text")
    rec["off_limits_candidates"] = self_score_candidates(scan_root)
    rec["rubric_ids"] = rubric_ids(scan_root)
    write_json(rd / "target.json", rec)
    return rec


def argparse_ns(opt):
    class NS:
        offline = bool(opt.get("offline"))
    return NS()


def verify_snapshot(run_id):
    """Gate G9 (§7.5): re-hash the snapshot against the intake pin. Exit 4 on a change."""
    from . import state
    rd = state.run_path(run_id)
    rec = read_json(rd / "target.json")
    if rec["root"] != "target:" or not rec["pin"].startswith("tree:"):
        return True
    if tree_hash(rd / "target") != rec["pin"]:
        raise IntakeError("the target snapshot changed since intake (gate G9)", EXIT_INTEGRITY)
    return True


# ------------------------------------------------------------------ isolate, inventory, shuffle, estimate

def isolate(run_id):
    from . import state
    st = state.load(run_id)
    rd = state.run_path(run_id)
    if not (rd / "target.json").exists():
        raise IntakeError("isolate needs a successful intake (target.json)", EXIT_MISSING)
    rec = read_json(rd / "target.json")
    for inst in state.active_instances(st):
        (rd / "sealed" / inst).mkdir(parents=True, exist_ok=True)
    root = rec["root"]
    lines = set()
    if (rd / "off_limits.txt").exists():
        lines |= {l.strip() for l in (rd / "off_limits.txt").read_text(encoding="utf-8").splitlines() if l.strip()}
    prefix = root if root.endswith(":") else root + "/"
    lines |= {prefix + c for c in rec.get("off_limits_candidates", [])}
    others = rd.parent
    lines |= {f"run:{p.name}/" for p in others.iterdir() if p.is_dir() and p.name != rd.name} if others.is_dir() else set()
    paths.assert_portable(sorted(lines))
    (rd / "off_limits.txt").write_text("".join(l + "\n" for l in sorted(lines)), encoding="utf-8", newline="\n")
    (rd / "audit_seed").write_text(f"{st['audit_seed']}\n", encoding="utf-8", newline="\n")
    return sorted(lines)


def inventory(root_path, skip_build=False):
    files, total = [], 0
    for rel, full, kind in walk(root_path, skip_build=skip_build):
        if kind != "file" or full.suffix.lower() not in INVENTORY_EXT:
            continue
        words = len(full.read_bytes().decode("utf-8", "replace").split())
        files.append({"path": rel, "words": words, "bytes": full.stat().st_size})
        total += words
    return {"files": files, "total_files": len(files), "total_words": total}


def shuffle(seed, items=None):
    items = list(items or CRITERIA)
    rng = random.Random(int(hashlib.sha256(str(seed).encode("utf-8")).hexdigest(), 16))
    rng.shuffle(items)
    return items


def estimate(root_path, docs=False):
    """Hypothesis ranges (§6.5) from the source inventory; never a measurement."""
    inv = inventory(root_path)
    chars = sum(f["bytes"] for f in inv["files"])
    approx_tokens = chars // 4
    if docs:
        sessions, hours = (3, 5), (0.5, 1.0)
    else:
        sessions = (11, 13)
        hours = (2.0, 5.0) if approx_tokens < 1_000_000 else (3.0, 6.0)
    return {"label": "hypothesis (coefficients uncalibrated until Phase 6)", "files": inv["total_files"],
            "words": inv["total_words"], "approx_tokens_chars4": approx_tokens,
            "sessions": list(sessions), "wall_hours": list(hours)}


# ------------------------------------------------------------------ CLI

def configure_intake(p):
    p.add_argument("--run", required=True)
    p.add_argument("--request", default=None, help=REQUEST)
    p.add_argument("--mode", choices=["folder", "git", "docs", "reference"])
    p.add_argument("--source", nargs="*", default=None)
    p.add_argument("--slug")
    p.add_argument("--name")
    p.add_argument("--type", dest="type_", choices=["open", "closed", "docs"])
    p.add_argument("--status", choices=["implemented", "design-only"])
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--ref")
    p.add_argument("--offline", action="store_true")


def run_intake(args):
    src = args.source
    if src is not None and args.mode in ("folder", "git") and len(src) == 1:
        src = src[0]
    try:
        rec = intake(args.run, args.request, mode=args.mode, source=src, slug=args.slug, name=args.name,
                     type=args.type_, status=args.status, ref=args.ref, offline=args.offline)
    except (IntakeError, paths.PathError) as e:
        print(f"intake: {e}", file=sys.stderr)
        return e.code
    except Exception as e:  # state errors carry a code too
        if hasattr(e, "code"):
            print(f"intake: {e}", file=sys.stderr)
            return e.code
        raise
    print(f"intake: {rec['slug']} pinned at {rec['pin'][:24]}… ({rec['root']}); "
          f"{len(rec['off_limits_candidates'])} self-score candidate(s); "
          f"revised against this rubric: {rec['rubric_ids']['revised_against_rubric']}"
          + ("; dirty working tree recorded (G1)" if rec.get("dirty") else ""))
    return EXIT_OK


def configure_isolate(p):
    p.add_argument("--run", required=True)


def run_isolate(args):
    try:
        lines = isolate(args.run)
    except (IntakeError, paths.PathError) as e:
        print(f"isolate: {e}", file=sys.stderr)
        return e.code
    print(f"isolate: sealed folders ready; {len(lines)} off-limits entr(y/ies)")
    return EXIT_OK


def _root_arg(s, run=None):
    if s.startswith(paths.SCHEMES):
        return paths.resolve(s, run=run)
    return pathlib.Path(s)


def configure_inventory(p):
    p.add_argument("--root", required=True, help="portable root (cache:<slug>, target:, run:…) or a folder")
    p.add_argument("--run", default=None)
    p.add_argument("--json", default=None, help="write the inventory to this run: path")
    p.add_argument("--shipped-root", default=None)


def run_inventory(args):
    try:
        root = _root_arg(args.root, args.run)
        if not root.is_dir():
            print("inventory: root not found", file=sys.stderr)
            return EXIT_MISSING
        inv = inventory(root, skip_build=skip_build_for(args.shipped_root))
        inv["root"] = args.root if args.root.startswith(paths.SCHEMES) else "."
        if args.json:
            from . import state
            write_json(paths.resolve(args.json, run=state.run_path(args.run)) if args.json.startswith("run:")
                       else args.json, inv)
    except (paths.PathError,) as e:
        print(f"inventory: {e}", file=sys.stderr)
        return e.code
    for f in inv["files"]:
        print(f"{f['words']:>8}  {f['path']}")
    print(f"{inv['total_words']:>8}  total ({inv['total_files']} files)")
    return EXIT_OK


def configure_shuffle(p):
    p.add_argument("--seed", required=True)
    p.add_argument("--items", default=None, help="comma-separated items (default C1..C16)")


def run_shuffle(args):
    for x in shuffle(args.seed, args.items.split(",") if args.items else None):
        print(x)
    return EXIT_OK


def configure_estimate(p):
    p.add_argument("--source", default=None, help="original folder or docs file(s), or target: with --run")
    p.add_argument("--run", default=None)
    p.add_argument("--request", default=None)
    p.add_argument("--docs", action="store_true")


def run_estimate(args):
    from . import state
    try:
        source, docs = args.source, args.docs
        if args.request:
            st = state.load(args.run)
            _before_s01(st, state.run_path(args.run))
            req = _request(st, args.request)
            source = req.get("source")
            docs = req.get("mode") == "docs"
            source = source[0] if isinstance(source, list) and source else source
            if docs and source:
                source = str(pathlib.Path(str(source)).parent)
        if not source:
            print("estimate: --source or --request is required", file=sys.stderr)
            return EXIT_USAGE
        root = _root_arg(str(source), args.run)
        if not root.is_dir():
            print("estimate: source not found", file=sys.stderr)
            return EXIT_MISSING
        est = estimate(root, docs=docs)
    except (IntakeError, paths.PathError, state.StateError) as e:
        print(f"estimate: {e}", file=sys.stderr)
        return e.code
    print(f"estimate ({est['label']}): {est['files']} files, {est['words']} words, "
          f"~{est['approx_tokens_chars4']} tokens (chars/4); sessions {est['sessions'][0]}-{est['sessions'][1]}, "
          f"wall time {est['wall_hours'][0]}-{est['wall_hours'][1]} h")
    return EXIT_OK
