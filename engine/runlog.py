"""Engine-owned, append-only run logs (#85): `log append` and `answers add`.

Text arrives through request files under runs/<id>/requests/log/, never on the
command line. Each request is deleted after reading, on success and on failure.
The sha256 of each log after every append is kept in state.json; an append onto a
log whose bytes changed since the engine last wrote it is refused (exit 4).
"""
import pathlib
import sys

from . import paths
from .common import EXIT_GATE, EXIT_INTEGRITY, EXIT_MISSING, EXIT_OK, EXIT_USAGE
from .jsonio import read_json, sha256_file

LOG = "log.md"
ANSWERS = "owner-answers.md"
REQUEST_DIR = "requests/log/"


class LogError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def _append(st, name, text):
    from . import state
    rd = state.run_path(st["run_id"])
    p = rd / name
    logs = st.setdefault("logs", {})
    if p.exists():
        if logs.get(name) != sha256_file(p):
            raise LogError(f"{name} changed outside the engine; refusing to append", EXIT_INTEGRITY)
    elif logs.get(name):
        raise LogError(f"{name} was removed outside the engine", EXIT_INTEGRITY)
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    logs[name] = sha256_file(p)
    state.save(st)


def engine_note(st, text):
    from . import state
    _append(st, LOG, f"- {state.now()} engine: {text}")


def _read_request(st, request, kind):
    from . import state
    if not str(request).startswith("run:" + REQUEST_DIR):
        raise LogError(f"requests must come from run:{REQUEST_DIR}", EXIT_USAGE)
    p = paths.resolve(request, run=state.run_path(st["run_id"]))
    if not p.exists():
        raise LogError("request file not found", EXIT_MISSING)
    try:
        obj = read_json(p)
    except ValueError:
        obj = None
    finally:
        p.unlink(missing_ok=True)
    if not isinstance(obj, dict) or obj.get("type") != kind:
        raise LogError(f"request type must be {kind!r}", EXIT_GATE)
    return obj


def log_append(run_id, request):
    from . import state
    st = state.load(run_id)
    obj = _read_request(st, request, "log-entry")
    text = str(obj.get("text", "")).strip()
    if not text:
        raise LogError("empty log entry", EXIT_GATE)
    paths.assert_portable(text)
    _append(st, LOG, f"- {state.now()} {text}")
    return st


def answers_add(run_id, request):
    from . import state
    st = state.load(run_id)
    obj = _read_request(st, request, "answer")
    q, a = str(obj.get("question", "")).strip(), str(obj.get("answer", "")).strip()
    if not q or not a:
        raise LogError("an answer needs question and answer", EXIT_GATE)
    paths.assert_portable([q, a])
    _append(st, ANSWERS, f"## {state.now()} (source: via orchestrator)\n\n**Q.** {q}\n\n**A.** {a}\n")
    return st


def configure_log(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    a = sub.add_parser("append")
    a.add_argument("--run", required=True)
    a.add_argument("--text-request", required=True)


def configure_answers(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    a = sub.add_parser("add")
    a.add_argument("--run", required=True)
    a.add_argument("--request", required=True)


def _wrap(fn, *a):
    from . import state
    try:
        fn(*a)
    except (LogError, state.StateError, paths.PathError) as e:
        print(f"{fn.__name__}: {e}", file=sys.stderr)
        return e.code
    print(f"{fn.__name__}: ok")
    return EXIT_OK


def run_log(args):
    return _wrap(log_append, args.run, args.text_request)


def run_answers(args):
    return _wrap(answers_add, args.run, args.request)
