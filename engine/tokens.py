"""`engine tokens` (plan §7.8): static token counts for lens L5.

T1, T2 and T3 are the sums over the lens file's three lists. T0 is every text file under the
method root (`cache:<slug>` or `target:`), as in the reference round; the lens `T0_root` is
recorded beside it. Dependency lockfiles are not method text and are skipped, and dist/ and
build/ are skipped when a shipped root is declared outside them (§7.5). Files are read as bytes, decoded as UTF-8 with errors="replace", and CRLF is
normalized to LF before counting. A `frontmatter_only` entry counts only its YAML block
(BOM tolerated). A (path, frontmatter_only) pair is counted once within a list. Missing
files are listed, never counted. Closed products give null for every T (R-NM).

The tokenizer is tiktoken o200k_base when it is importable and primed in
$AMA_HOME/cache/tiktoken; otherwise chars/4, which is marked not comparable.
"""
import os
import pathlib
import re
import sys

from . import paths
from .common import EXIT_GATE, EXIT_MISSING, EXIT_OK
from .intake import skip_build_for, walk
from .jsonio import read_json, write_json

TEXT_EXT = {".md", ".mdc", ".markdown", ".yaml", ".yml", ".toml", ".txt", ".json", ".csv", ".xml"}
FRONTMATTER = re.compile(r"\A\ufeff?---[ \t]*\n(?:(.*?)\n)?---[ \t]*(?:\n|\Z)", re.S)
LOCKFILES = {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock"}
TIKTOKEN_NAME = "tiktoken o200k_base"
FALLBACK_NAME = "chars/4"
BASELINE_TOKENIZER = TIKTOKEN_NAME
READING = ("T1, T2 and T3 are counted per list (not cumulative); frontmatter_only counts the YAML text between "
           "the --- delimiters, without the delimiter lines and the final newline; duplicate (path, "
           "frontmatter_only) pairs are counted once per list; T0 = every TEXT_EXT file under the method root, "
           "skipping .git, node_modules, __pycache__, virtual envs and dependency lockfiles, and dist/ and build/ "
           "when a shipped root is declared outside them")


def read_text(p):
    return pathlib.Path(p).read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def frontmatter(text):
    """The YAML text between the opening and closing --- lines (empty when there is none)."""
    m = FRONTMATTER.match(text)
    return (m.group(1) or "") if m else ""


class Counter:
    def __init__(self, force_fallback=False):
        self.enc = None
        if not force_fallback:
            self.enc = _tiktoken()
        self.name = TIKTOKEN_NAME if self.enc else FALLBACK_NAME

    def __call__(self, text):
        if self.enc is None:
            return len(text) // 4
        return len(self.enc.encode(text, disallowed_special=()))


def _tiktoken():
    try:
        cache = paths.cache_dir() / "tiktoken"
    except paths.PathError:
        return None
    if not cache.is_dir() or not any(cache.iterdir()):
        return None                     # not primed: never touch the network here
    os.environ["TIKTOKEN_CACHE_DIR"] = str(cache)
    try:
        import tiktoken
        return tiktoken.get_encoding("o200k_base")
    except Exception:
        return None


def count_list(entries, resolve, count):
    total, missing, seen, n = 0, [], set(), 0
    for e in entries or []:
        key = (e["path"], bool(e.get("frontmatter_only")))
        if key in seen:
            continue
        seen.add(key)
        try:
            p = resolve(e["path"])
        except paths.PathError:
            p = None
        if p is None or not p.is_file():
            missing.append(e["path"])
            continue
        text = read_text(p)
        total += count(frontmatter(text) if key[1] else text)
        n += 1
    return total, missing, n


def count_t0(root, count, shipped_root=None):
    total, n = 0, 0
    for rel, full, kind in walk(root, skip_build=skip_build_for(shipped_root)):
        if kind == "file" and full.suffix.lower() in TEXT_EXT and full.name not in LOCKFILES:
            total += count(read_text(full))
            n += 1
    return total, n


def count_method(lenses, resolve, count, closed=False, shipped_root=None, method_root=None):
    row = {"host": lenses.get("host"), "tokenizer": count.name, "comparable": count.name == BASELINE_TOKENIZER}
    l5 = lenses.get("L5") or {}
    if closed or l5.get("T1") is None:
        row.update(T1=None, T2=None, T3=None, T0=None, missing=[], measurable=False)
        return row
    missing, files = [], {}
    for t in ("T1", "T2", "T3"):
        row[t], miss, files[t] = count_list(l5.get(t), resolve, count)
        missing += miss
    root = method_root or l5.get("T0_root")
    row["T0"], row["T0_root"], row["lens_T0_root"] = None, root, l5.get("T0_root")
    if root:
        try:
            rp = resolve(root)
        except paths.PathError:
            rp = None
        if rp is not None and rp.is_dir():
            row["T0"], files["T0"] = count_t0(rp, count, shipped_root)
        else:
            missing.append(root)
    row.update(missing=sorted(set(missing)), files=files, measurable=True)
    return row


def baseline(root=None, slugs=None, count=None):
    from . import baseline as bl
    from .registry import entries, load_registry
    root = root or paths.project_root()
    count = count or Counter()
    reg = {e["slug"]: e for e in entries(load_registry(root))}
    d = bl.round_dir(root) / "lenses"
    methods = {}
    for f in sorted(d.glob("*.json")):
        slug = f.stem
        if slugs and slug not in slugs:
            continue
        e = reg.get(slug, {})
        methods[slug] = count_method(read_json(f), lambda p: paths.resolve(p), count,
                                     closed=e.get("type") == "closed", shipped_root=e.get("shipped_root"),
                                     method_root=f"cache:{slug}")
    return {"tokenizer": count.name, "reading": READING, "methods": methods}


def for_run(run_id, count=None):
    from . import state
    st = state.load(run_id)
    rd = state.run_path(run_id)
    src = rd / "lenses.final.json" if (rd / "lenses.final.json").exists() else rd / "lenses.json"
    if not src.exists():
        raise FileNotFoundError("lenses.final.json (run apply-audit first)")
    count = count or Counter()
    t = st.get("target") or {}
    rec = read_json(rd / "target.json") if (rd / "target.json").exists() else {}
    root = rec.get("root") if rec.get("root") in ("target:",) or str(rec.get("root", "")).startswith("cache:") else None
    row = count_method(read_json(src), lambda p: paths.resolve(p, run=rd), count, closed=t.get("type") == "closed",
                       method_root=root)
    out = {"tokenizer": count.name, "reading": READING, "methods": {t.get("slug", "target"): row}}
    write_json(rd / "tokens.json", out)
    return out


def configure(p):
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run")
    g.add_argument("--baseline", action="store_true")
    p.add_argument("--slug", action="append", default=None)
    p.add_argument("--out", default=None, help="--baseline: write the JSON here")


def run(args):
    try:
        if args.run:
            out = for_run(args.run)
        else:
            out = baseline(slugs=args.slug)
            if args.out:
                write_json(args.out, out)
    except FileNotFoundError as e:
        print(f"tokens: missing {e}", file=sys.stderr)
        return EXIT_MISSING
    except paths.PathError as e:
        print(f"tokens: {e}", file=sys.stderr)
        return e.code
    if out["tokenizer"] != BASELINE_TOKENIZER:
        print(f"tokens: warning: tokenizer is {out['tokenizer']} (approx.); counts are not comparable with the baseline")
    missing = 0
    for slug, r in out["methods"].items():
        missing += len(r["missing"])
        print(f"tokens: {slug}: T1 {r['T1']} T2 {r['T2']} T3 {r['T3']} T0 {r['T0']}"
              + (f"; {len(r['missing'])} missing" if r["missing"] else ""))
    return EXIT_GATE if missing and args.run else EXIT_OK
