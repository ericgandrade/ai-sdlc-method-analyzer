"""Portable path notation and runtime locations (plan §0.3, §7.1, §10.1).

Stored forms:
  cache:<slug>/<posix-relpath>   a reference clone in $AMA_HOME/cache/refs/<slug>/
  target:<posix-relpath>         the run's snapshot, runs/<id>/target/
  run:<posix-relpath>            relative to the active run directory
  run:<source-run-id>/<relpath>  a declared read-only source run (#81)
  docs:<file>[#fragment]         a documentation file copied into runs/<id>/docs/

Project and data-directory resolution live in `hooks/amahome.py` (#61), loaded by
file path so the guard and the engine share one implementation.
"""
import importlib.util
import json
import pathlib
import re

from .common import EXIT_MISSING, EXIT_USAGE

# An absolute path anywhere inside a string: POSIX root, Windows drive, or home tilde.
# URLs pass, because `//` does not match `/[A-Za-z]`.
ABSOLUTE = re.compile(r"(^|[\s(\"';,=])(/[A-Za-z]|[A-Za-z]:\\|~/)")
RUN_ID = re.compile(r"^\d{8}-\d{6}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SCHEMES = ("cache:", "target:", "run:", "docs:")

_AMAHOME_FILE = pathlib.Path(__file__).resolve().parents[1] / "hooks" / "amahome.py"
_spec = importlib.util.spec_from_file_location("_ama_amahome", _AMAHOME_FILE)
amahome = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(amahome)


class NotPortable(ValueError):
    pass


class PathError(Exception):
    """A resolution failure carrying the engine exit code to use."""

    def __init__(self, message, code=EXIT_USAGE):
        super().__init__(message)
        self.code = code


def assert_portable(obj, where="$"):
    """Raise NotPortable if any string value (or key) inside obj embeds an absolute path."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_portable(k, f"{where}.{k}")
            assert_portable(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_portable(v, f"{where}[{i}]")
    elif isinstance(obj, str) and ABSOLUTE.search(obj):
        raise NotPortable(f"absolute path in {where}")


# ------------------------------------------------------------------ locations

def project_root(env=None, cwd=None):
    """The project (plugin root or clone). Exit 3 when neither is found."""
    p = amahome.project_root(env, cwd)
    if p is None:
        raise PathError("project not found: run from the repository root or set CLAUDE_PLUGIN_ROOT", EXIT_MISSING)
    return p


def data_dir(env=None, project=None, allow_inside_project=False, create=False):
    """$AMA_HOME or the OS default. Refused (exit 2) when inside the project folder."""
    d = pathlib.Path(amahome.data_dir(env))
    if project is None:
        project = amahome.project_root(env)
    if project is not None and amahome.is_inside(d, project) and not allow_inside_project:
        raise PathError("AMA_HOME is inside the project folder; choose a directory outside it", EXIT_USAGE)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def runs_dir(**kw):
    return data_dir(**kw) / "runs"


def reports_dir(**kw):
    return data_dir(**kw) / "reports"


def cache_dir(**kw):
    return data_dir(**kw) / "cache"


def refs_dir(**kw):
    return cache_dir(**kw) / "refs"


def _as_run_dir(run):
    """A run directory from a run id, or a path given as-is."""
    if isinstance(run, pathlib.PurePath):
        return pathlib.Path(run)
    if RUN_ID.match(str(run)):
        return runs_dir() / str(run)
    raise PathError(f"invalid run id: {run}", EXIT_USAGE)


run_dir = _as_run_dir


# ------------------------------------------------------------------ resolve / portable

def _subpath_from_registry(slug):
    try:
        from .registry import entries, load_registry
        reg = load_registry(project_root())
    except Exception:   # no project or unreadable registry: no subpath restriction known
        return None
    for e in entries(reg):
        if e.get("slug") == slug:
            return e.get("subpath")
    return None


def _join_confined(base, rel, label):
    rel = (rel or "").replace("\\", "/")
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        raise PathError(f"{label}: path escapes its root", EXIT_USAGE)
    parts = [x for x in rel.split("/") if x not in ("", ".")]
    if ".." in parts:
        raise PathError(f"{label}: path escapes its root", EXIT_USAGE)
    out = pathlib.Path(base).joinpath(*parts)
    if out.exists() and not amahome.is_inside(out, base):     # a symlink inside the tree pointing out
        raise PathError(f"{label}: path escapes its root", EXIT_USAGE)
    return out


def _declared_sources(rdir):
    try:
        s = json.loads((pathlib.Path(rdir) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return list(s.get("sources") or [])


def resolve(p, run=None, subpaths=None, refs=None):
    """Resolve a portable path to a filesystem Path.

    run: run id or run directory (needed for target:, run:, docs:).
    subpaths: optional {slug: subpath} override (defaults to the registry).
    refs: optional reference-cache base (default $AMA_HOME/cache/refs)."""
    if not isinstance(p, str) or not p.startswith(SCHEMES):
        raise PathError(f"not a portable path: {p!r}", EXIT_USAGE)
    scheme, rest = p.split(":", 1)
    if scheme == "cache":
        slug, _, rel = rest.partition("/")
        if not SLUG.match(slug):
            raise PathError(f"invalid slug in {p!r}", EXIT_USAGE)
        base = (pathlib.Path(refs) if refs is not None else refs_dir()) / slug
        sub = subpaths.get(slug) if subpaths is not None else _subpath_from_registry(slug)
        out = _join_confined(base, rel, p)
        if sub and rel:
            sroot = _join_confined(base, sub, p)
            if not (out == sroot or sroot in out.parents):
                raise PathError(f"{p}: outside the declared subpath {sub}", EXIT_USAGE)
        return out
    if run is None:
        raise PathError(f"{p}: needs a run", EXIT_USAGE)
    rdir = _as_run_dir(run)
    if scheme == "target":
        return _join_confined(rdir / "target", rest, p)
    if scheme == "docs":
        return _join_confined(rdir / "docs", rest.split("#", 1)[0], p)
    first, _, tail = rest.partition("/")
    if RUN_ID.match(first) and first != rdir.name:
        if first not in _declared_sources(rdir):
            raise PathError(f"{p}: {first} is not a declared source run", EXIT_USAGE)
        return _join_confined(rdir.parent / first, tail, p)
    return _join_confined(rdir, rest, p)


def _flavour(x):
    s = str(x)
    return pathlib.PureWindowsPath if ("\\" in s or re.match(r"^[A-Za-z]:", s)) else pathlib.PurePosixPath


def _rel_parts(path, base):
    """Parts of path below base, or None. Works for POSIX and Windows-style strings alike."""
    fp, fb = _flavour(path), _flavour(base)
    pp, bp = fp(str(path)).parts, fb(str(base)).parts
    win = pathlib.PureWindowsPath in (fp, fb)
    norm = (lambda t: [s.lower() for s in t]) if win else list
    if len(pp) < len(bp) or norm(pp[:len(bp)]) != norm(bp):
        return None
    return list(pp[len(bp):])


def portable(path, run=None, refs=None):
    """The stored form of a filesystem path. Raises PathError when it lies under no known root.

    run: run id or run directory; refs: reference-cache base (default $AMA_HOME/cache/refs)."""
    refs = refs if refs is not None else refs_dir()
    candidates = []
    if run is not None:
        rdir = run if isinstance(run, pathlib.PurePath) or not RUN_ID.match(str(run)) else _as_run_dir(run)
        rd = str(rdir)
        sep = "\\" if _flavour(rd) is pathlib.PureWindowsPath else "/"
        candidates += [(rd + sep + "target", "target:"), (rd + sep + "docs", "docs:"), (rd, "run:"),
                       (str(_flavour(rd)(rd).parent), "runs")]
    candidates.append((str(refs), "cache:"))
    for base, scheme in candidates:
        parts = _rel_parts(path, base)
        if parts is None:
            continue
        if scheme == "runs":
            if parts and RUN_ID.match(parts[0]):
                return "run:" + "/".join(parts)
            continue
        if scheme == "cache:" and not parts:
            continue
        return scheme + "/".join(parts)
    raise PathError("path lies under no portable root", EXIT_USAGE)
