"""`engine fetch`: clone references at their registry pins, download registry docs pages,
and prime the tokenizer (plan §7.4). One of the only two network commands.

Clones land in $AMA_HOME/cache/refs/<slug>/, never inside the project. git runs with
the user's own environment (credential helper, SSH agent) and never prompts. Nothing
from a fetched source is ever executed: git does not transfer hooks, and the engine
only reads files.
"""
import datetime
import hashlib
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

from . import paths
from .common import EXIT_GATE, EXIT_INTEGRITY, EXIT_MISSING, EXIT_OFFLINE, EXIT_OK, EXIT_USAGE
from .jsonio import read_json, write_json

USER_AGENT = "ai-sdlc-method-analyzer-fetch"
CREDENTIAL_URL = re.compile(r"^[a-z][a-z0-9+.-]*://[^/@\s]*@", re.I)
TOKENIZER = "o200k_base"


class FetchError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def offline(args=None):
    return bool(getattr(args, "offline", False)) or os.environ.get("AMA_OFFLINE") == "1"


def has_credentials(url):
    """True for URLs that embed userinfo (user and token before the host). SSH scp-style git remotes are allowed."""
    return bool(CREDENTIAL_URL.match(url or ""))


def git_env():
    e = dict(os.environ)
    e["GIT_TERMINAL_PROMPT"] = "0"
    e.setdefault("GCM_INTERACTIVE", "never")
    ssh = e.get("GIT_SSH_COMMAND")
    e["GIT_SSH_COMMAND"] = (ssh + " -o BatchMode=yes") if ssh else "ssh -o BatchMode=yes"
    return e


def _git(args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=git_env(),
                       stdin=subprocess.DEVNULL, shell=False)
    if check and r.returncode != 0:
        raise FetchError(f"git {args[0]} failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
    return r


def head(dest):
    r = _git(["-C", str(dest), "rev-parse", "HEAD"], check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def clone_at_pin(url, pin, dest):
    """Clone (blob-less) if absent, fetch the pin, detach at it, verify HEAD (exit 4 on mismatch)."""
    if has_credentials(url):
        raise FetchError("URL embeds credentials; configure a git credential helper instead", EXIT_USAGE)
    dest = pathlib.Path(dest)
    if dest.exists() and head(dest) == pin:
        return "cached"
    if not (dest / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git(["-c", "core.autocrlf=false", "-c", "core.eol=lf", "clone", "-q", "--filter=blob:none",
              "--no-checkout", url, str(dest)])
    _git(["-C", str(dest), "config", "core.autocrlf", "false"])
    _git(["-C", str(dest), "config", "core.eol", "lf"])
    r = _git(["-C", str(dest), "fetch", "-q", "origin", pin], check=False)
    if r.returncode != 0:
        raise FetchError(f"pin {pin[:12]} not fetchable from {url}", EXIT_INTEGRITY)
    r = _git(["-C", str(dest), "-c", "advice.detachedHead=false", "checkout", "-q", "--detach", pin], check=False)
    if r.returncode != 0:
        raise FetchError(f"checkout of pin {pin[:12]} failed", EXIT_INTEGRITY)
    got = head(dest)
    if got != pin:
        raise FetchError(f"HEAD {str(got)[:12]} does not equal the pin {pin[:12]}", EXIT_INTEGRITY)
    return "fetched"


def fetch_docs(slug, docs, out_root, today=None, opener=None):
    """Download each docs[] page as is (no link following) into <out_root>/<slug>/<date>/ with a MANIFEST."""
    today = today or datetime.date.today().isoformat()
    d = pathlib.Path(out_root) / slug / today
    d.mkdir(parents=True, exist_ok=True)
    pages, failed = [], 0
    open_ = opener or urllib.request.urlopen
    for page in docs:
        url, name = page["url"], page["file"]
        if not url.startswith(("https://", "http://")) or "/" in name or "\\" in name or name.startswith("."):
            raise FetchError(f"{slug}: refusing docs entry {name!r}", EXIT_USAGE)
        rec = {"url": url, "file": name, "snapshot_date": page.get("snapshot_date"),
               "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with open_(req, timeout=60) as resp:
                data = resp.read()
            (d / name).write_bytes(data)
            rec.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), status="ok")
        except Exception as e:          # network errors are recorded per page, never fatal for the others
            rec.update(sha256=None, bytes=0, status=f"error: {type(e).__name__}")
            failed += 1
        pages.append(rec)
    write_json(d / "MANIFEST.json", {"slug": slug, "fetch_date": today, "pages": pages,
                                     "note": "live pages fetched on fetch_date; the registry snapshot_date "
                                             "snapshot is not reproducible"})
    return d, failed


def docs_present(slug, out_root):
    base = pathlib.Path(out_root) / slug
    for m in sorted(base.glob("*/MANIFEST.json"), reverse=True):
        if all(p.get("status") == "ok" for p in read_json(m).get("pages", [])):
            return True
    return False


def prime_tokenizer(cache):
    os.environ["TIKTOKEN_CACHE_DIR"] = str(pathlib.Path(cache) / "tiktoken")
    try:
        import tiktoken
    except ImportError:
        return "absent"
    pathlib.Path(os.environ["TIKTOKEN_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)
    tiktoken.get_encoding(TOKENIZER)
    return "primed"


def tokenizer_present(cache):
    d = pathlib.Path(cache) / "tiktoken"
    return d.is_dir() and any(d.iterdir())


# ------------------------------------------------------------------ CLI

def configure(p):
    p.add_argument("--slug", action="append", default=[], help="reference slug (repeatable)")
    p.add_argument("--all", action="store_true", help="every registry reference (variants only by --slug)")
    p.add_argument("--docs", action="store_true", help="also download docs[] pages")
    p.add_argument("--tokenizer", action="store_true", help="prime the tiktoken o200k_base cache")
    p.add_argument("--offline", action="store_true", help="verify the cache only; exit 6 if anything is missing")
    p.add_argument("--root", default=None, help="project root (default: resolved project)")


def _select(reg, args):
    from .registry import entries
    refs = list(reg.get("references") or [])
    by = {e["slug"]: e for e in entries(reg)}
    if args.all:
        return refs
    out = []
    for s in args.slug:
        if s not in by:
            raise FetchError(f"unknown slug {s}", EXIT_USAGE)
        out.append(by[s])
    return out


def run(args):
    from .registry import load_registry
    try:
        root = pathlib.Path(args.root) if args.root else paths.project_root()
        reg = load_registry(root)
        sel = _select(reg, args)
        cache = paths.cache_dir(project=root)
        if not sel and not args.tokenizer:
            print("fetch: nothing selected (use --slug, --all or --tokenizer)", file=sys.stderr)
            return EXIT_USAGE
        for e in sel:
            if has_credentials(e.get("url")):
                raise FetchError(f"{e['slug']}: URL embeds credentials", EXIT_USAGE)
        if offline(args):
            missing = [e["slug"] for e in sel if e.get("type") in ("open", "closed") and e.get("url")
                       and head(cache / "refs" / e["slug"]) != e.get("pin")]
            if args.docs:
                missing += [f"docs:{e['slug']}" for e in sel if e.get("docs") and not docs_present(e["slug"], cache / "docs")]
            if args.tokenizer and not tokenizer_present(cache):
                missing.append("tokenizer")
            if missing:
                print(f"fetch: offline and missing from the cache: {', '.join(missing)}", file=sys.stderr)
                return EXIT_OFFLINE
            print(f"fetch: offline; {len(sel)} reference(s) present and verified")
            return EXIT_OK
        failed = 0
        for e in sel:
            if e.get("type") in ("open", "closed") and e.get("url"):
                how = clone_at_pin(e["url"], e["pin"], cache / "refs" / e["slug"])
                print(f"fetch: {e['slug']} {how} at {e['pin'][:12]}")
            if args.docs and e.get("docs"):
                d, n = fetch_docs(e["slug"], e["docs"], cache / "docs")
                failed += n
                print(f"fetch: {e['slug']} docs: {len(e['docs']) - n}/{len(e['docs'])} page(s)")
        if args.tokenizer:
            st = prime_tokenizer(cache)
            if st == "absent":
                print("fetch: notice: tiktoken is not installed; token counts fall back to chars/4 and are "
                      "marked approx. and not comparable with the baseline")
            else:
                print(f"fetch: tokenizer {TOKENIZER} primed")
        return EXIT_MISSING if failed else EXIT_OK
    except (FetchError, paths.PathError) as e:
        print(f"fetch: {e}", file=sys.stderr)
        return e.code
