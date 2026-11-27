"""Single resolver for the project folder, the data directory ($AMA_HOME) and the
guard marker (plan §0.3, §4.5 #48 #61, §10.1).

Stdlib only. `engine/paths.py` and `hooks/guard.py` both load this file by path,
so they always agree. Nothing here imports the engine package.
"""
import json
import os
import pathlib
import sys
import tempfile

APP = "ai-sdlc-method-analyzer"
REGISTRY_REL = ("references", "registry.yaml")


def project_root(env=None, cwd=None):
    """`${CLAUDE_PLUGIN_ROOT}` if set, else the cwd when it holds references/registry.yaml, else None."""
    env = os.environ if env is None else env
    plugin = env.get("CLAUDE_PLUGIN_ROOT")
    if plugin:
        return pathlib.Path(plugin)
    c = pathlib.Path(cwd) if cwd is not None else pathlib.Path.cwd()
    if c.joinpath(*REGISTRY_REL).is_file():
        return c
    return None


def default_data_dir(env=None, platform=None):
    """Per-user OS data folder (§0.3)."""
    env = os.environ if env is None else env
    platform = platform or sys.platform
    home = env.get("HOME") or env.get("USERPROFILE") or str(pathlib.Path.home())
    if platform.startswith("win"):
        base = env.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        return pathlib.PureWindowsPath(base) / APP if not sys.platform.startswith("win") else pathlib.Path(base) / APP
    if platform == "darwin":
        return pathlib.Path(home) / "Library" / "Application Support" / APP
    xdg = env.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return pathlib.Path(xdg) / APP


def data_dir(env=None, platform=None):
    env = os.environ if env is None else env
    v = env.get("AMA_HOME")
    return pathlib.Path(v) if v else default_data_dir(env, platform)


def is_inside(child, parent):
    try:
        c = pathlib.Path(os.path.realpath(child))
        p = pathlib.Path(os.path.realpath(parent))
    except (OSError, ValueError):
        return False
    return c == p or p in c.parents


# ------------------------------------------------------------------ guard marker

def marker_path(data):
    return pathlib.Path(data) / "guard" / "active.json"


def read_marker(data):
    """List of live-run entries; [] when the marker is absent, empty or unreadable."""
    p = marker_path(data)
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    runs = obj.get("runs") if isinstance(obj, dict) else None
    return [r for r in runs if isinstance(r, dict)] if isinstance(runs, list) else []


def write_marker(data, entries):
    p = marker_path(data)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"runs": entries}, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".active-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, p)


def fail_closed_runs(data):
    """Run ids that must close the guard (#61, #69): status `active` with a stage `running`
    while the marker is missing or empty. Runs that are failed, closed or waiting-external
    are ignored."""
    if read_marker(data):
        return []
    runs = pathlib.Path(data) / "runs"
    bad = []
    if not runs.is_dir():
        return bad
    for st in sorted(runs.glob("*/state.json")):
        try:
            s = json.loads(st.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if s.get("status") != "active":
            continue
        if any(isinstance(v, dict) and v.get("status") == "running" for v in (s.get("stages") or {}).values()):
            bad.append(s.get("run_id") or st.parent.name)
    return bad
