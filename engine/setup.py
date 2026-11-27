"""`engine setup [--check] [--remove]`: host access to $AMA_HOME without prompts (#59, #70, #80, #90).

Writes the git-ignored `.claude/settings.local.json` of this clone: the data directory as an
additional directory, plus allow rules scoped to it and the single engine Bash form. It merges
and never overwrites: only plain strings are appended, and the exact strings added are kept in
`$AMA_HOME/setup-record.json`, one entry per clone, so re-runs are idempotent and `--remove`
deletes exactly what setup added. The record is local and never copied into a run or report.
"""
import datetime
import json
import os
import pathlib
import shutil

from . import paths
from .common import EXIT_GATE, EXIT_MISSING, EXIT_OK

SETTINGS_REL = (".claude", "settings.local.json")
RECORD = "setup-record.json"
RELOAD = "Run setup, then open the folder (or reload the window / restart the session)."


class SetupError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def _rule_path(p):
    s = pathlib.Path(p).as_posix()
    return "/" + s if s.startswith("/") else "//" + s       # host syntax: //<absolute path>


def desired(data, python):
    d = _rule_path(data)
    allow = [f"Read({d}/{sub}/**)" for sub in ("runs", "reports", "cache")]
    allow += [f"{tool}({d}/{sub}/**)" for tool in ("Edit", "Write") for sub in ("runs", "reports")]
    allow.append(f"Bash({python} -m engine *)")
    return {"additionalDirectories": [str(data)], "allow": allow}


def _load_record(data):
    p = pathlib.Path(data) / RECORD
    if not p.exists():
        return {"projects": {}}
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        raise SetupError(f"{RECORD} in the data directory is not valid JSON; fix or delete it", EXIT_GATE)
    rec.setdefault("projects", {})
    return rec


def _save_record(data, rec):
    p = pathlib.Path(data) / RECORD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _key(project):
    return str(pathlib.Path(os.path.realpath(str(project))))


def _read_settings(f):
    if not f.exists():
        return {}
    try:
        obj = json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        raise SetupError(f"{'/'.join(SETTINGS_REL)} is not valid JSON; it was left untouched", EXIT_GATE)
    if not isinstance(obj, dict):
        raise SetupError(f"{'/'.join(SETTINGS_REL)} is not a JSON object; it was left untouched", EXIT_GATE)
    perms = obj.get("permissions", {})
    if not isinstance(perms, dict):
        raise SetupError("settings `permissions` is not an object; left untouched", EXIT_GATE)
    for k in ("additionalDirectories", "allow"):
        v = perms.get(k, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise SetupError(f"settings `permissions.{k}` is not a list of strings; left untouched", EXIT_GATE)
    return obj


def _write_settings(f, obj):
    for k in ("additionalDirectories", "allow"):     # schema shape check before writing
        v = obj.get("permissions", {}).get(k, [])
        assert isinstance(v, list) and all(isinstance(x, str) for x in v)
    if f.exists():
        shutil.copyfile(f, f.with_name(f.name + ".bak"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")


def _refuse_if_active(data):
    if paths.amahome.read_marker(data):
        raise SetupError("engine setup edits host settings and is refused while a run is active", EXIT_GATE)


def setup(project, data, python="python3"):
    _refuse_if_active(data)
    f = pathlib.Path(project).joinpath(*SETTINGS_REL)
    obj = _read_settings(f)
    rec = _load_record(data)
    key = _key(project)
    prev = rec["projects"].get(key, {}).get("added", {})
    want = desired(data, python)
    perms = obj.setdefault("permissions", {})
    added = {}
    for k in ("additionalDirectories", "allow"):
        cur = perms.setdefault(k, [])
        stale = [s for s in prev.get(k, []) if s not in want[k]]
        cur[:] = [s for s in cur if s not in stale]
        ours = [s for s in prev.get(k, []) if s in want[k] and s in cur]
        for s in want[k]:
            if s not in cur:
                cur.append(s)
                ours.append(s)
        added[k] = [s for s in want[k] if s in ours]
    _write_settings(f, obj)
    rec["projects"][key] = {"settings_file": "/".join(SETTINGS_REL), "added": added, "python": python,
                            "data_dir": str(data),
                            "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _save_record(data, rec)
    return added


def check(project, data, env=None):
    """[] when the settings are in place, else the list of problems (exit 3)."""
    env = os.environ if env is None else env
    problems = []
    if env.get("PYTHONSAFEPATH"):
        problems.append("PYTHONSAFEPATH is set, which breaks `python -m engine` in a clone: unset it, "
                        "or use the plugin path with PYTHONPATH set to the plugin root")
    entry = _load_record(data)["projects"].get(_key(project))
    if entry is None:
        return problems + ["engine setup has not been run for this clone"]
    if entry.get("data_dir") != str(data):
        problems.append("the recorded data directory differs from the current AMA_HOME: re-run `engine setup`")
    f = pathlib.Path(project).joinpath(*SETTINGS_REL)
    try:
        obj = _read_settings(f) if f.exists() else None
    except SetupError as e:
        return problems + [str(e)]
    if obj is None:
        return problems + [f"{'/'.join(SETTINGS_REL)} is missing: re-run `engine setup`"]
    perms = obj.get("permissions", {})
    want = desired(data, entry.get("python", "python3"))
    for k in ("additionalDirectories", "allow"):
        missing = [s for s in want[k] if s not in perms.get(k, [])]
        if missing:
            problems.append(f"{len(missing)} {k} entr{'y' if len(missing) == 1 else 'ies'} missing: re-run `engine setup`")
    return problems


def remove(project, data):
    _refuse_if_active(data)
    rec = _load_record(data)
    key = _key(project)
    entry = rec["projects"].get(key)
    if entry is None:
        return {}
    f = pathlib.Path(project).joinpath(*SETTINGS_REL)
    if f.exists():
        obj = _read_settings(f)
        perms = obj.get("permissions", {})
        for k, strings in entry.get("added", {}).items():
            if k in perms:
                perms[k] = [s for s in perms[k] if s not in strings]
                if not perms[k]:
                    del perms[k]
        if "permissions" in obj and not perms:
            del obj["permissions"]
        _write_settings(f, obj)
    del rec["projects"][key]
    _save_record(data, rec)
    return entry.get("added", {})


def configure(p):
    g = p.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="verify the local settings (exit 3 when not in place)")
    g.add_argument("--remove", action="store_true", help="delete exactly the strings setup added")
    p.add_argument("--python", default="python3", choices=["python3", "python", "py -3"])


def run(args):
    try:
        project = paths.project_root()
        data = paths.data_dir(project=project, create=not args.check)
        if args.check:
            problems = check(project, data)
            for m in problems:
                print(f"setup --check: {m}")
            if problems:
                print(f"Fix: {args.python} -m engine setup. {RELOAD}")
                return EXIT_MISSING
            print("setup --check: ok")
            return EXIT_OK
        if args.remove:
            gone = remove(project, data)
            print(f"setup --remove: removed {sum(len(v) for v in gone.values())} entries")
            return EXIT_OK
        added = setup(project, data, args.python)
        print(f"setup: {sum(len(v) for v in added.values())} entries recorded in {'/'.join(SETTINGS_REL)}. {RELOAD}")
        return EXIT_OK
    except (SetupError, paths.PathError) as e:
        print(f"setup: {e}")
        return e.code
