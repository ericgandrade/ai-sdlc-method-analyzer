"""`lineage` (plan §7.13, stage S13): similarity between the target and cached references.

1. Normalize lines: strip, collapse whitespace, lowercase; drop blank lines and lines under 8 characters.
2. Find candidate reference files by shared normalized-line count (inverted index over the references).
3. For the top 3 candidates: identical-line ratio = |target lines found in the candidate| / |target lines|,
   `difflib.SequenceMatcher(None, a, b).ratio()` and the normalized-line Jaccard.
4. Collect identifiers: frontmatter `name:` values, skill directory names and script basenames.

Writes `lineage-pre.json` for the lineage detector, with hits sorted by ratio. Similarity is a lead,
never a conclusion: the detector confirms or rejects each hit (§5.11).
"""
import difflib
import re
import sys
from collections import defaultdict

from . import paths
from .common import EXIT_MISSING, EXIT_OK, EXIT_USAGE
from .intake import walk
from .jsonio import read_json, write_json
from .tokens import FRONTMATTER, TEXT_EXT, read_text

SCRIPT_EXT = {".sh", ".bash", ".py", ".js", ".mjs", ".cjs", ".ts", ".ps1"}
LINE_MIN = 8
TOP = 3
NAME = re.compile(r"^name:\s*['\"]?([^'\"\n#]+?)['\"]?\s*$", re.M)


def normalize(text):
    out = []
    for line in text.split("\n"):
        s = " ".join(line.split()).lower()
        if len(s) >= LINE_MIN:
            out.append(s)
    return out


def corpus(root, prefix):
    """{portable name: text} for every text or script file under root (symlinks never followed)."""
    out = {}
    for rel, full, kind in walk(root):
        if kind == "file" and full.suffix.lower() in TEXT_EXT | SCRIPT_EXT:
            out[f"{prefix}{rel}"] = read_text(full)
    return out


def identifiers(files):
    ids = set()
    for name, text in files.items():
        rel = name.split(":", 1)[1].split("/", 1)[1] if name.startswith("cache:") else name.split(":", 1)[-1]
        parts = rel.split("/")
        m = FRONTMATTER.match(text)
        if m and m.group(1):
            ids |= {f"name:{v.strip()}" for v in NAME.findall(m.group(1))}
        if parts[-1] == "SKILL.md" and len(parts) > 1:
            ids.add(f"skill:{parts[-2]}")
        if "." + parts[-1].rsplit(".", 1)[-1].lower() in SCRIPT_EXT:
            ids.add(f"script:{parts[-1]}")
    return ids


def _slug_of(name):
    return name[len("cache:"):].split("/", 1)[0] if name.startswith("cache:") else None


def lineage(target_files, ref_files, min_ratio=0.5):
    tnorm = {n: normalize(t) for n, t in sorted(target_files.items())}
    rnorm = {n: normalize(t) for n, t in sorted(ref_files.items())}
    rsets = {n: set(v) for n, v in rnorm.items()}
    index = defaultdict(set)
    for n, lines in rsets.items():
        for line in lines:
            index[line].add(n)
    files = []
    for n, lines in tnorm.items():
        if not lines:
            continue
        shared = defaultdict(int)
        for line in set(lines):
            for r in index.get(line, ()):
                shared[r] += 1
        cands = sorted(shared, key=lambda r: (-shared[r], r))[:TOP]
        matches = []
        for r in cands:
            found = sum(1 for line in lines if line in rsets[r])
            tset = set(lines)
            matches.append({"ref": r, "ratio": round(found / len(lines), 4),
                            "seq_ratio": round(difflib.SequenceMatcher(None, lines, rnorm[r]).ratio(), 4),
                            "jaccard": round(len(tset & rsets[r]) / len(tset | rsets[r]), 4)})
        matches.sort(key=lambda m: (-m["ratio"], m["ref"]))
        files.append({"file": n, "lines": len(lines), "matches": matches})
    hits = sorted(({"file": f["file"], **f["matches"][0]} for f in files if f["matches"]
                   and f["matches"][0]["ratio"] >= min_ratio), key=lambda h: (-h["ratio"], h["file"]))
    tid = identifiers(target_files)
    by_slug = defaultdict(dict)
    for n, t in ref_files.items():
        by_slug[_slug_of(n) or "other"][n] = t
    shared_ids = {s: sorted(tid & identifiers(fs)) for s, fs in sorted(by_slug.items())}
    return {"min_ratio": min_ratio, "files": files, "hits": hits,
            "identifiers": {"target": sorted(tid), "shared": {s: v for s, v in shared_ids.items() if v}}}


def configure(p):
    p.add_argument("--run", required=True)
    p.add_argument("--against", default="all", help="all, or comma-separated reference slugs")
    p.add_argument("--min-ratio", type=float, default=0.5)


def run(args):
    from . import state
    from .registry import entries, load_registry
    try:
        st = state.load(args.run)
    except state.StateError as e:
        print(f"lineage: {e}", file=sys.stderr)
        return e.code
    rd = state.run_path(args.run)
    rec = read_json(rd / "target.json") if (rd / "target.json").exists() else {}
    root = rec.get("root", "target:")
    if root == "target:":
        tdir, prefix = rd / "target", "target:"
    elif root.startswith("cache:"):
        tdir, prefix = paths.refs_dir() / root[len("cache:"):], f"{root}/"
    else:
        tdir, prefix = rd / "docs" / "text", "run:docs/text/"
    if not tdir.is_dir():
        print("lineage: the target snapshot is missing (run intake first)", file=sys.stderr)
        return EXIT_MISSING
    own = (st.get("target") or {}).get("slug")
    slugs = [e["slug"] for e in entries(load_registry(paths.project_root()))]
    if args.against != "all":
        want = [s for s in args.against.split(",") if s]
        unknown = sorted(set(want) - set(slugs))
        if unknown:
            print(f"lineage: unknown slugs {unknown}", file=sys.stderr)
            return EXIT_USAGE
        slugs = want
    refs = {}
    used = []
    for s in sorted(set(slugs) - {own}):
        d = paths.refs_dir() / s
        if d.is_dir():
            refs.update(corpus(d, f"cache:{s}/"))
            used.append(s)
    out = lineage(corpus(tdir, prefix), refs, args.min_ratio)
    out["against"] = used
    write_json(rd / "lineage-pre.json", out)
    print(f"lineage: {len(out['hits'])} hit(s) at ratio >= {args.min_ratio} against {len(used)} reference(s)")
    return EXIT_OK
