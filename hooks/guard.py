"""PreToolUse guard: default-deny while an analyzer run is active (rules/injection.md).

Reads one hook input (JSON) on stdin. Exit 0 allows the call; exit 2 blocks it and the
message on stderr goes back to the model. Any other exit code does not block in the host,
so every failure path here exits 2 (fail closed). Outside a run (no live marker entry and
no orphaned running stage), everything is allowed.

Stdlib only, and no syntax newer than Python 3.8: the hook runs under whatever `python3`
the shell finds, and a SyntaxError would exit 1 and fail open. Project and data-directory
resolution come from `hooks/amahome.py`, loaded by file path, the same file the engine uses.
"""
import importlib.util
import json
import os
import pathlib
import shlex
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Must equal engine.cli.COMMANDS (tests/test_guard.py checks the two stay in sync).
SUBCOMMANDS = frozenset([
    "fetch", "intake", "isolate", "inventory", "shuffle", "validate", "scorecard", "calibration",
    "reconcile", "alpha", "audit-scope", "apply-audit", "tokens", "consolidate", "rank", "sensitivity",
    "superiority", "ranges", "lineage", "fitgap", "leakcheck", "state", "baseline", "verify-freeze",
    "setup", "tty-check", "log", "answers", "estimate", "adjudication", "hooks", "report", "slides",
    "read", "list", "convert", "git-log", "git-show", "git-ls", "build-plugin",
])
FORBIDDEN_CHARS = set(";&|`$()<>{}*?~!")
BASH_TOOLS = ("Bash",)
WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
READ_TOOLS = {"Read": "file_path", "Glob": "path", "Grep": "path", "LS": "path"}
NEUTRAL_TOOLS = frozenset(["Task", "Agent", "TodoWrite", "Skill", "AskUserQuestion", "ToolSearch",
                           "ExitPlanMode", "SendMessage", "TaskStop"])
ENGINE_OWNED = frozenset(["state.json", "log.md", "owner-answers.md", "calibration.json", "alpha.json",
                          "results.json", "ranking.json", "sensitivity.json", "superiority.json"])
REPORT_STAGES = ("S16", "S16b")


class Deny(Exception):
    pass


def _load_amahome():
    spec = importlib.util.spec_from_file_location("_ama_guard_amahome", str(HERE / "amahome.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _real(p):
    return pathlib.Path(os.path.realpath(str(p)))


def _inside(child, parent):
    c, p = _real(child), _real(parent)
    if os.name == "nt":
        c, p = pathlib.Path(str(c).lower()), pathlib.Path(str(p).lower())
    return c == p or p in c.parents


def _rel(child, parent):
    return _real(child).relative_to(_real(parent)).as_posix() if not _real(child) == _real(parent) else ""


class Ctx(object):
    def __init__(self, ama, env, data, project, hook_cwd):
        self.ama, self.env, self.data, self.project, self.cwd = ama, env, data, project, hook_cwd
        self.runs = []            # [(run_id, run_dir, state dict)]

    def load_runs(self, entries):
        for e in entries:
            rid = str(e.get("run_id") or "")
            if not rid or "/" in rid or "\\" in rid or rid in (".", ".."):
                continue
            rdir = self.data / "runs" / rid
            try:
                st = json.loads((rdir / "state.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                st = {}           # a stale entry: the guard stays active; `state list` cleans it
            self.runs.append((rid, rdir, st if isinstance(st, dict) else {}))

    def abspath(self, p):
        q = pathlib.Path(str(p))
        if not q.is_absolute():
            q = pathlib.Path(self.cwd or str(self.project)) / q
        return q


def _stages(st):
    s = st.get("stages")
    return s if isinstance(s, dict) else {}


def _status(st, stage):
    v = _stages(st).get(stage)
    return v.get("status") if isinstance(v, dict) else None


def _running(st):
    return [(k, v) for k, v in _stages(st).items() if isinstance(v, dict) and v.get("status") == "running"]


# ------------------------------------------------------------------ Bash

def _split(cmd):
    if os.name == "nt":
        toks = shlex.split(cmd, posix=False)
        return [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t for t in toks]
    return shlex.split(cmd, posix=True)


def _interpreters(ctx):
    found = set()
    for _, _, st in ctx.runs:
        py = st.get("python")
        if isinstance(py, str) and py in ("python3", "python", "py -3"):
            found.add(py)
    return found or {"python3"}


def _terminal_message(py, argv):
    msg = "this command needs an interactive terminal; type it yourself:\n  %s -m engine %s" % (py, " ".join(argv))
    if ctx_env_mintty():
        msg += "\nGit Bash/mintty is not detected as interactive; use PowerShell, cmd or Windows Terminal."
    return msg


def ctx_env_mintty():
    return bool(os.environ.get("MSYSTEM")) or os.environ.get("TERM_PROGRAM") == "mintty"


def _exports_allow(ctx):
    try:
        cfg = json.loads((ctx.data / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    allow = ((cfg.get("exports") or {}).get("allow") if isinstance(cfg, dict) else None) or []
    return [a for a in allow if isinstance(a, str)]


def check_bash(ctx, tool_input):
    cmd = tool_input.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        raise Deny("empty or missing command")
    if "\n" in cmd or "\r" in cmd:
        raise Deny("a command may not contain a newline or a carriage return")
    bad = sorted(set(cmd) & FORBIDDEN_CHARS)
    if bad:
        raise Deny("shell metacharacters are not allowed (%s); use one plain engine call" % " ".join(bad))
    try:
        toks = _split(cmd)
    except ValueError:
        raise Deny("the command does not tokenize")
    guard_dir = ctx.data / "guard"
    if str(guard_dir) in cmd or any("guard" in t and _inside(ctx.abspath(t), guard_dir) for t in toks):
        raise Deny("the guard marker folder is protected")
    i = 0
    if toks and toks[0].startswith("PYTHONPATH="):
        plugin = ctx.env.get("CLAUDE_PLUGIN_ROOT")
        if not plugin or toks[0][len("PYTHONPATH="):] != plugin:
            raise Deny("PYTHONPATH must be absent or equal to the plugin root")
        i = 1
    py = None
    for interp in sorted(_interpreters(ctx), key=len, reverse=True):
        parts = interp.split()
        if toks[i:i + len(parts)] == parts:
            py, i = interp, i + len(parts)
            break
    if py is None or toks[i:i + 2] != ["-m", "engine"] or len(toks) <= i + 2:
        raise Deny("only `<recorded python> -m engine <subcommand> [args]` is allowed while a run is active "
                   "(direct find, ls, wc, git, pdftotext, node, npm and other programs are denied)")
    sub, rest = toks[i + 2], toks[i + 3:]
    if sub not in SUBCOMMANDS:
        raise Deny("unknown engine subcommand: %s" % sub)
    if ctx.cwd is not None:
        allowed = [ctx.project] + ([pathlib.Path(ctx.env["CLAUDE_PROJECT_DIR"])] if ctx.env.get("CLAUDE_PROJECT_DIR") else [])
        if not any(_real(ctx.cwd) == _real(a) for a in allowed) or _inside(ctx.cwd, ctx.data):
            raise Deny("engine calls must run from the project root")
    head = rest[:1]
    argv = [sub] + rest
    if (sub == "state" and head == ["reset"]) or \
            (sub == "state" and head == ["close"] and ("--abort" in rest or "--force" in rest)) or \
            (sub == "adjudication" and head == ["import"]) or (sub == "baseline" and head == ["promote"]):
        raise Deny(_terminal_message(py, argv))
    if sub == "setup":
        raise Deny("engine setup edits host settings and is refused while a run is active")
    if sub == "report":
        dests = [rest[k + 1] for k, a in enumerate(rest[:-1]) if a == "--copy-to"]
        dests += [a.split("=", 1)[1] for a in rest if a.startswith("--copy-to=")]
        if "--copy-to" in rest[-1:]:
            raise Deny("--copy-to needs a directory")
        allow = _exports_allow(ctx)
        for d in dests:
            if not any(_real(ctx.abspath(d)) == _real(a) for a in allow):
                raise Deny("report --copy-to is refused while a run is active unless the directory is in "
                           "exports.allow of the data directory's config.json")


# ------------------------------------------------------------------ writes

def check_write(ctx, tool, tool_input):
    raw = tool_input.get(WRITE_TOOLS[tool])
    if not isinstance(raw, str) or not raw:
        raise Deny("missing path")
    p = ctx.abspath(raw)
    if _inside(p, ctx.data / "guard"):
        raise Deny("the guard marker folder is protected")
    for rid, rdir, st in ctx.runs:
        if _inside(p, rdir):
            _check_run_write(st, _rel(p, rdir))
            return
        if _inside(p, ctx.data / "reports" / rid):
            if any(_status(st, s) == "running" for s in REPORT_STAGES):
                return
            raise Deny("the report folder is writable only while S16 or S16b is running")
    raise Deny("writes are allowed only inside an active run's declared outputs")


def _check_run_write(st, rel):
    name = rel.rsplit("/", 1)[-1]
    if not rel or rel in ENGINE_OWNED or name.endswith("-pre.json") or rel.startswith("pristine/"):
        raise Deny("%s is engine-owned; use the engine subcommand that writes it" % (rel or "the run folder"))
    if rel.startswith("requests/log/"):
        return
    if rel.startswith("requests/intake/"):
        if _status(st, "S01") == "done":
            raise Deny("requests/intake/ is closed once S01 is done")
        return
    for _, s in _running(st):
        for d in s.get("declared_outputs") or []:
            if (d.endswith("/") and rel.startswith(d)) or rel == d:
                return
    raise Deny("%s is not a declared output of a running stage" % rel)


# ------------------------------------------------------------------ reads

def check_read(ctx, tool, tool_input):
    raw = tool_input.get(READ_TOOLS[tool])
    p = ctx.abspath(raw) if isinstance(raw, str) and raw else pathlib.Path(ctx.cwd or str(ctx.project))
    roots = [ctx.project, ctx.data / "cache"]
    for rid, rdir, st in ctx.runs:
        roots += [rdir, ctx.data / "reports" / rid]
        roots += [ctx.data / "runs" / str(s) for s in (st.get("sources") or []) if isinstance(s, str)
                  and "/" not in s and "\\" not in s and s not in (".", "..")]
    if not any(_inside(p, r) for r in roots):
        raise Deny("reads are allowed in the project, the reference cache, the active run and its declared sources")
    for rid, rdir, st in ctx.runs:
        if _status(st, "S07r") != "running":
            continue
        if tool != "Read" and _inside(rdir, p):
            raise Deny("while S07r runs, search inside the snapshot (target/) or name a file")
        if not _inside(p, rdir):
            continue
        rel = _rel(p, rdir)
        parts = rel.split("/")
        if rel in ("reconciled.json", "reconcile-pre.json") or rel.startswith("pristine/") or \
                (parts[0] == "sealed" and (tool != "Read" or (len(parts) == 3 and parts[2].startswith("target.")))):
            raise Deny("while S07r runs, the r-bearing files are sealed; use reconciled-blind.json")


# ------------------------------------------------------------------ main

def decide(stdin_text, env=None):
    """Return (exit code, message)."""
    env = os.environ if env is None else env
    ama = _load_amahome()
    project = ama.project_root(env, cwd=HERE.parent) or HERE.parent
    data = pathlib.Path(ama.data_dir(env))
    marker = ama.marker_path(data)
    corrupt = False
    if marker.exists():
        try:
            obj = json.loads(marker.read_text(encoding="utf-8"))
            corrupt = not (isinstance(obj, dict) and isinstance(obj.get("runs"), list))
        except (OSError, ValueError):
            corrupt = True
    entries = [] if corrupt else ama.read_marker(data)
    orphaned = [] if (entries or corrupt) else ama.fail_closed_runs(data)
    if not entries and not corrupt and not orphaned:
        return 0, ""
    hook = json.loads(stdin_text)
    if not isinstance(hook, dict):
        raise ValueError("hook input is not an object")
    tool = hook.get("tool_name")
    tool_input = hook.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tool_input, dict):
        raise ValueError("hook input lacks tool_name or tool_input")
    ctx = Ctx(ama, env, data, project, hook.get("cwd") if isinstance(hook.get("cwd"), str) else None)
    try:
        if corrupt or orphaned:
            if tool in BASH_TOOLS or tool in WRITE_TOOLS:
                why = "the guard marker is unreadable" if corrupt else \
                    "a run has a running stage but is not in the guard marker"
                raise Deny(why + "; run `engine state list` in a terminal to repair it")
            return 0, ""
        ctx.load_runs(entries)
        if tool in BASH_TOOLS:
            check_bash(ctx, tool_input)
        elif tool in WRITE_TOOLS:
            check_write(ctx, tool, tool_input)
        elif tool in READ_TOOLS:
            check_read(ctx, tool, tool_input)
        elif tool not in NEUTRAL_TOOLS:
            raise Deny("tool %s is not allowed while a run is active" % tool)
    except Deny as d:
        return 2, "guard: denied: %s" % d
    return 0, ""


def main():
    try:
        text = sys.stdin.read()
        code, msg = decide(text)
    except BaseException as e:      # fail closed: only exit 2 blocks in the host
        code, msg = 2, "guard: denied (fail closed): %s" % type(e).__name__
    if msg:
        sys.stderr.write(msg + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
