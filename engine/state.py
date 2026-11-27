"""Run state, stages, gates and the guard marker (plan §4.5, §6.1–§6.3, §7.15).

`runs/<id>/state.json` is managed only by this module. Every write goes through
`save()`, which validates the state schema and the portable-path rule.
"""
import datetime
import json
import os
import pathlib
import random
import shutil
import socket
import sys

from . import paths
from .common import EXIT_GATE, EXIT_INTEGRITY, EXIT_MISSING, EXIT_OK, EXIT_USAGE
from .jsonio import read_json, sha256_file, write_json

TOOL_VERSION_FILE = (".claude-plugin", "plugin.json")
CAL_DEFAULT = ["addyosmani"]
CAL_DESIGN = ["mattpocock", "bmad"]
CAL_FALLBACK = ["addyosmani", "mattpocock", "superpowers", "bmad"]
STALE_HOURS = 24
RETRY_BOUNDS = {"G2": 1, "G4": 1, "G5": 2, "G6": 2, "G7": 2}
MODEL_VENDORS = [("claude", "Anthropic"), ("gpt", "OpenAI"), ("o1", "OpenAI"), ("o3", "OpenAI"), ("o4", "OpenAI"),
                 ("codex", "OpenAI"), ("gemini", "Google"), ("gemma", "Google"), ("llama", "Meta"),
                 ("mistral", "Mistral"), ("codestral", "Mistral"), ("grok", "xAI"), ("nova", "AWS"),
                 ("titan", "AWS"), ("deepseek", "DeepSeek"), ("qwen", "Alibaba")]

# stage -> (deps, declared outputs). Declared outputs are what the running agent may write
# (the guard reads them) and what `state done` requires to exist. Engine-owned files are absent.
ASSESS = {
    "S00": ([], []),
    "S01": (["S00"], ["boundary.md", "off_limits.txt"]),
    "S02": (["S01"], []),
    "S03": (["S02"], ["trace.md"]),
    "S04:S1": (["S02"], ["sealed/S1/"]),
    "S04:S2": (["S02"], ["sealed/S2/"]),
    "S05": (["S04:S1", "S04:S2"], []),
    "S06": (["S03", "S05"], ["reconciled.json", "reconciliation.md"]),
    "S07r": (["S06"], ["r_independent.json"]),
    "S07": (["S06", "S07r"], ["redteam.json", "audit-log.md"]),
    "S07b": (["S07"], ["adjudication.json"]),
    "S08a": (["S03"], ["lenses.json"]),
    "S08b": (["S07", "S08a"], ["lenses.json"]),
    "S09": (["S08b"], ["lens-audit.json"]),
    "S10": (["S09"], []),
    "S11": (["S07b", "S09", "S10"], []),
    "S12": (["S11"], []),
    "S13": (["S02"], ["lineage.md"]),
    "S14": (["S12", "S13"], ["analysis.md"]),
}
DOCS = {
    "S00": ([], []),
    "S01": (["S00"], ["boundary.md", "off_limits.txt"]),
    "S02": (["S01"], []),
    "D1": (["S02"], ["docs-only.json", "analysis.md"]),
    "D2": (["S02"], ["sealed/D2/"]),
    "D3": (["D1", "D2"], []),
    "S13": (["S02"], ["lineage.md"]),
}
REPORT_TAIL = {
    "S16": ([], ["report/sections/"]),
    "S16b": (["S16"], []),
    "S17": (["S16b"], ["review.json"]),
}
COMPARE = {"S00": ([], []), "C1": (["S00"], []), **{k: (v[0] or ["C1"], v[1]) for k, v in REPORT_TAIL.items()}}
FITGAP = {"S00": ([], []), "F1": (["S00"], []), "S15": (["F1"], ["fitgap.md", "fitgap.json"]),
          **{k: (v[0] or ["S15"], v[1]) for k, v in REPORT_TAIL.items()}}
MODES = ("folder", "git", "docs", "reference", "compare", "fitgap")
HINTS = {
    "S00": "engine verify-freeze", "S01": "agent intake-pinner + engine intake", "S02": "engine isolate",
    "S03": "agent path-tracer", "S04": "agent l1-scorer", "S05": "engine scorecard check",
    "S06": "engine reconcile pre -> agent reconciler -> engine alpha", "S06b": "agent l1-scorer (third scorer)",
    "S07r": "engine reconcile blind -> agent red-team-auditor", "S07": "engine audit-scope -> agent red-team-auditor",
    "S07b": "agent adjudicator", "S08a": "agent lens-evaluator", "S08b": "agent lens-evaluator (L2)",
    "S09": "agent lens-auditor", "S10": "engine apply-audit + engine tokens", "S11": "engine consolidate",
    "S12": "engine rank, sensitivity, superiority", "S13": "engine lineage -> agent lineage-detector",
    "S14": "agent dense-analyst", "S15": "engine fitgap -> agent fitgap-writer", "S16": "agent report-builder -> engine report",
    "S16b": "engine slides", "S17": "agent report-reviewer", "D1": "agent docs-only-assessor",
    "D2": "agent docs-only-assessor (second, independent)", "D3": "engine ranges", "C1": "engine consolidate, rank, sensitivity, superiority",
    "F1": "engine fitgap",
}
END_MESSAGES = {
    "folder": "Assessment {id} complete. Next: menu 5 (report) or 6 (fit-gap). Files: run:analysis.md, run:results.json",
    "git": "Assessment {id} complete. Next: menu 5 (report) or 6 (fit-gap). Files: run:analysis.md, run:results.json",
    "docs": "Documentation-only assessment {id} complete. Range summary in run:analysis.md. Next: menu 5 (report).",
    "reference": "Reference run {id} complete. Compare the reproduction delta against baseline/ and its recorded U.",
    "compare": "Report {id} complete: reports/{id}/report.html, report.md and deck.html. Export with engine report --copy-to <dir>.",
    "fitgap": "Fit-gap report {id} complete: reports/{id}/report.html, report.md, deck.html and run:fitgap.md. "
              "Export with engine report --copy-to <dir>.",
}


class StateError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ small helpers

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_time(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def is_interactive():
    """Whether stdin is a terminal. Agent Bash calls are not; tests monkeypatch this."""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def mintty():
    return bool(os.environ.get("MSYSTEM")) or os.environ.get("TERM_PROGRAM") == "mintty"


def require_tty(command, python="python3"):
    """Refuse a privileged subcommand on non-interactive stdin (#78, #87)."""
    if is_interactive():
        return
    msg = f"refused: this command needs an interactive terminal. Type it yourself:\n  {python} -m engine {command}"
    if mintty():
        msg += "\nGit Bash/mintty is not detected as interactive; use PowerShell, cmd or Windows Terminal."
    raise StateError(msg, EXIT_GATE)


def confirm(prompt, expected):
    try:
        return input(f"{prompt} Type {expected!r} to confirm: ").strip() == expected
    except EOFError:
        return False


def project():
    return paths.project_root()


def tool_version(root=None):
    root = root or project()
    return json.loads(pathlib.Path(root).joinpath(*TOOL_VERSION_FILE).read_text(encoding="utf-8"))["version"]


def run_path(run_id):
    return paths.run_dir(run_id)


def load(run_id):
    p = run_path(run_id) / "state.json"
    if not p.exists():
        raise StateError(f"run {run_id}: state.json not found", EXIT_MISSING)
    return read_json(p)


def save(st):
    from .validate import check
    st["updated"] = now()
    errors = [e for e in check("state", st)]
    if errors:
        raise StateError("state.json would be invalid: " + "; ".join(errors[:5]), EXIT_GATE)
    write_json(run_path(st["run_id"]) / "state.json", st)


def _stage(deps, outs, status="pending"):
    return {"status": status, "started": None, "finished": None, "host": None, "model": None,
            "tokens_in": None, "tokens_out": None, "wall_minutes": None, "deps": list(deps),
            "declared_outputs": list(outs), "outputs": [], "note": "", "retries": 0}


def stage_table(mode, design_only=False, with_analysis=False, second_assessor=False, lineage=False):
    if mode in ("folder", "git"):
        table, skipped = ASSESS, set() if design_only else {"S07r"}
        skipped |= {"S07b"}
    elif mode == "reference":
        table = ASSESS
        skipped = {"S07r", "S07b"} | (set() if with_analysis else {"S13", "S14"})
    elif mode == "docs":
        table, skipped = DOCS, (set() if second_assessor else {"D2"}) | (set() if lineage else {"S13"})
    elif mode == "compare":
        table, skipped = COMPARE, set()
    else:
        table, skipped = FITGAP, set()
    return {k: _stage(d, o, "skipped" if k in skipped else "pending") for k, (d, o) in table.items()}


def last_stage(st):
    mode, stg = st["mode"], st["stages"]
    if mode in ("folder", "git"):
        return "S14"
    if mode == "docs":
        return "S13" if stg.get("S13", {}).get("status") != "skipped" else "D3"
    if mode == "reference":
        return "S14" if stg.get("S14", {}).get("status") != "skipped" else "S12"
    return "S17"


def dependents(st, stage):
    """Every stage that depends, directly or transitively, on `stage`."""
    out, frontier = set(), {stage}
    while frontier:
        nxt = {k for k, v in st["stages"].items() if set(v["deps"]) & frontier and k not in out}
        out |= nxt
        frontier = nxt
    return out


def _reset(st, names, note):
    for n in names:
        s = st["stages"][n]
        if s["status"] in ("done", "running", "failed"):
            s.update(status="pending", started=None, finished=None, outputs=[], note=note)


def ready(st):
    """Stages whose dependencies are done or skipped and which are themselves pending."""
    stg = st["stages"]
    ok = {k for k, v in stg.items() if v["status"] in ("done", "skipped")}
    return sorted((k for k, v in stg.items() if v["status"] == "pending" and set(v["deps"]) <= ok), key=_order(st))


def _order(st):
    keys = list(st["stages"])
    return keys.index


def _check_open(st):
    if st["status"] == "closed":
        raise StateError(f"run {st['run_id']} is closed; a closed run is never reopened. Start a new run.", EXIT_GATE)


def _portable_in_run(st, p):
    """Accept run:… or a path relative to the run directory; return (portable, Path)."""
    rd = run_path(st["run_id"])
    s = str(p)
    if s.startswith("run:"):
        return s, paths.resolve(s, run=rd)
    q = pathlib.Path(s)
    if q.is_absolute():
        return paths.portable(q, run=rd), q
    return "run:" + q.as_posix(), paths.resolve("run:" + q.as_posix(), run=rd)


def _hash_targets(path):
    """[(file Path)] for a file, or every file under a directory."""
    if path.is_dir():
        return sorted(f for f in path.rglob("*") if f.is_file())
    return [path]


def verify_outputs(st):
    """Reset every done stage whose latest recorded output changed, plus everything downstream.
    Returns the names of stages reset. A path recorded by several stages is checked for the last one."""
    owner = {}
    for name, s in st["stages"].items():
        if s["status"] != "done":
            continue
        for o in s["outputs"]:
            prev = owner.get(o["path"])
            if prev is None or (s.get("finished") or "") >= (st["stages"][prev[0]].get("finished") or ""):
                owner[o["path"]] = (name, o["sha256"])
    rd = run_path(st["run_id"])
    bad = set()
    for p, (name, sha) in owner.items():
        try:
            f = paths.resolve(p, run=rd)
        except paths.PathError:
            bad.add(name)
            continue
        if not f.is_file() or sha256_file(f) != sha:
            bad.add(name)
    reset = set()
    for name in bad:
        reset |= {name} | dependents(st, name)
    _reset(st, reset, "reset: an output hash no longer matches")
    return sorted(reset, key=_order(st))


# ------------------------------------------------------------------ marker

def marker_add(st):
    data = paths.data_dir()
    entries = [e for e in paths.amahome.read_marker(data) if e.get("run_id") != st["run_id"]]
    entries.append({"run_id": st["run_id"], "started": now(), "state_path": f"runs/{st['run_id']}/state.json",
                    "pid": os.getppid(), "host": socket.gethostname()})
    paths.amahome.write_marker(data, entries)


def marker_remove(run_id):
    data = paths.data_dir()
    entries = paths.amahome.read_marker(data)
    paths.amahome.write_marker(data, [e for e in entries if e.get("run_id") != run_id])


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if sys.platform.startswith("win"):
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def stale_entries(at=None):
    """Marker entries that are stale (§4.5): state missing, run closed or failed, or no update
    for 24 h while the recorded pid is dead on the same host."""
    at = at or datetime.datetime.now(datetime.timezone.utc)
    data = paths.data_dir()
    out = []
    for e in paths.amahome.read_marker(data):
        sp = data / "runs" / str(e.get("run_id")) / "state.json"
        if not sp.exists():
            out.append((e, "state missing"))
            continue
        s = read_json(sp)
        if s.get("status") in ("closed", "failed"):
            out.append((e, f"run {s.get('status')}"))
            continue
        upd = _parse_time(s.get("updated"))
        old = upd is None or (at - upd).total_seconds() > STALE_HOURS * 3600
        if old and e.get("host") == socket.gethostname() and not _pid_alive(e.get("pid")):
            out.append((e, "no update for 24 h and the recorded process is gone"))
    return out


def cleanup_stale(at=None):
    """Mark each stale run failed, reset its running stages to pending, drop it from the marker (#69)."""
    cleaned = []
    for e, why in stale_entries(at):
        rid = e.get("run_id")
        try:
            st = load(rid)
        except StateError:
            st = None
        if st is not None and st["status"] != "closed":
            for s in st["stages"].values():
                if s["status"] == "running":
                    s.update(status="pending", started=None, note="reset by stale cleanup")
            st["status"] = "failed"
            save(st)
        marker_remove(rid)
        cleaned.append((rid, why))
    return cleaned


# ------------------------------------------------------------------ init

def vendor_of(model):
    m = (model or "").lower()
    for prefix, vendor in MODEL_VENDORS:
        if m.startswith(prefix) or f"/{prefix}" in m or f".{prefix}" in m:
            return vendor
    return None


def choose_cal_refs(slug, design_only):
    base = list(CAL_DESIGN if design_only else CAL_DEFAULT)
    reason = "two references (one light, one heavy) for design-only targets" if design_only \
        else "default for implemented targets"
    if slug in base:
        rest = [r for r in CAL_FALLBACK if r not in base and r != slug]
        base = [r for r in base if r != slug] + rest[:1]
        reason += f"; {slug} is the target, replaced by the next in the fallback order"
    return base, reason


def _registry_entry(slug, root):
    from .registry import entries, load_registry
    for e in entries(load_registry(root)):
        if e.get("slug") == slug:
            return e
    return None


def reproduction_passes(root, round_id, version):
    """Protocol §9 (a): baseline/rounds/<round>/reproduction.json records an A2 pass for this major.minor."""
    p = pathlib.Path(root) / "baseline" / "rounds" / round_id / "reproduction.json"
    if not p.exists():
        return False
    rec = read_json(p)
    mm = ".".join(version.split(".")[:2])
    return any(r.get("pass") is True and ".".join(str(r.get("pipeline_version", "")).split(".")[:2]) == mm
               for r in rec.get("records", []))


def init(run_id, mode, slug, *, sources=(), seed=None, status="implemented", type_="open", name=None,
         cal_refs=None, scorer_model=None, publisher=None, self_assessment=False, isolation="subagent",
         python="python3", with_analysis=False, second_assessor=False, lineage=False, host=None):
    from . import baseline, freeze
    root = project()
    if mode not in MODES:
        raise StateError(f"mode must be one of {MODES}", EXIT_USAGE)
    if not paths.RUN_ID.match(run_id):
        raise StateError("run id must be YYYYMMDD-HHMMSS-<slug>", EXIT_USAGE)
    rd = run_path(run_id)
    if (rd / "state.json").exists():
        raise StateError(f"run {run_id} already exists", EXIT_GATE)
    bad = freeze.verify(root)
    if bad:
        raise StateError("frozen files do not match their FREEZE records (gate G0)", EXIT_INTEGRITY)
    freeze_map = {name_: sha for name_, sha, _, _ in freeze.records(root) if not name_.endswith(".en.md")}
    design_only = status == "design-only"
    entry = _registry_entry(slug, root)
    if entry and entry.get("conflict") and mode in ("reference", "folder", "git"):
        raise StateError(f"{slug} is registered with a conflict and is never scored: {entry['conflict']}", EXIT_GATE)
    pub = publisher or (entry or {}).get("publisher")
    vendor = vendor_of(scorer_model)
    if vendor and pub and vendor.lower() in str(pub).lower():
        raise StateError(f"vendor conflict (methodology 10.2): {slug} is published by {pub}, and the declared "
                         f"scorer model is from {vendor}. Choose a model from a different vendor.", EXIT_GATE)
    reason = None
    if mode in ("folder", "git", "reference", "docs"):
        if cal_refs:
            if slug in cal_refs:
                raise StateError("the target cannot be one of its own calibration references", EXIT_GATE)
            reason = "chosen by the user"
        else:
            cal_refs, reason = choose_cal_refs(slug, design_only)
    else:
        cal_refs = []
    rnd = baseline.current_round(root)
    version = tool_version(root)
    src = list(sources or [])
    if mode in ("compare", "fitgap"):
        _check_sources(src, mode)
    elif src:
        raise StateError("--sources is only for compare and fitgap runs", EXIT_USAGE)
    seed = int(seed) if seed is not None else int(run_id[:8])
    rd.mkdir(parents=True, exist_ok=True)
    st = {
        "run_id": run_id, "tool_version": version, "created": now(), "mode": mode,
        "target": None if mode in ("compare", "fitgap") else
        {"slug": slug, "name": name or (entry or {}).get("name") or slug, "type": type_, "status": status},
        "freeze": freeze_map, "seed": seed, "audit_seed": random.Random(seed).randrange(1, 2 ** 31),
        "cal_refs": cal_refs, "cal_reason": reason or "", "isolation": isolation,
        "self_assessment": bool(self_assessment),
        "comparison": "same-round" if rnd and reproduction_passes(root, rnd, version) else "cross-round",
        "round_id": f"{version}+{rnd}", "python": python, "budget": {}, "scorer_model": scorer_model,
        "roles": {"S1": None, "S2": None, "redteam": None, "adjudicator": None},
        "status": "active", "sources": src, "instances": {"S1": "S1", "S2": "S2", "extra": []},
        "retries": {}, "host": host,
        "stages": stage_table(mode, design_only, with_analysis, second_assessor, lineage),
    }
    save(st)
    marker_add(st)
    return st


def _check_sources(src, mode):
    if not src:
        raise StateError(f"{mode} runs need --sources", EXIT_USAGE)
    if mode == "fitgap" and len(src) != 1:
        raise StateError("a fitgap run has exactly one source assessment run", EXIT_USAGE)
    rounds = set()
    for rid in src:
        s = load(rid)
        if s["status"] != "closed":
            raise StateError(f"source {rid} is not closed", EXIT_GATE)
        if mode == "fitgap" and s["mode"] not in ("folder", "git", "reference"):
            raise StateError(f"source {rid} is not an assessment run", EXIT_GATE)
        rounds.add(s["round_id"].split("+", 1)[-1])
    if len(rounds) > 1:
        raise StateError("sources come from different rounds (#62)", EXIT_GATE)


# ------------------------------------------------------------------ transitions

def start(run_id, stage, host=None, model=None):
    st = load(run_id)
    _check_open(st)
    s = _get_stage(st, stage)
    ok = {k for k, v in st["stages"].items() if v["status"] in ("done", "skipped")}
    if s["status"] not in ("pending", "failed"):
        raise StateError(f"{stage} is {s['status']}, not pending", EXIT_GATE)
    if not set(s["deps"]) <= ok:
        raise StateError(f"{stage} is not ready: waiting for {sorted(set(s['deps']) - ok)}", EXIT_GATE)
    s.update(status="running", started=now(), finished=None, host=host or s["host"], model=model or s["model"])
    save(st)
    return st


def _get_stage(st, stage):
    if stage not in st["stages"]:
        raise StateError(f"unknown stage {stage} for mode {st['mode']}", EXIT_USAGE)
    return st["stages"][stage]


def done(run_id, stage, outputs=()):
    st = load(run_id)
    _check_open(st)
    s = _get_stage(st, stage)
    if s["status"] == "done":
        raise StateError(f"{stage} is already done", EXIT_GATE)
    if s["status"] == "skipped":
        raise StateError(f"{stage} is skipped in this run", EXIT_GATE)
    ok = {k for k, v in st["stages"].items() if v["status"] in ("done", "skipped")}
    if not set(s["deps"]) <= ok:
        raise StateError(f"{stage} is not ready: waiting for {sorted(set(s['deps']) - ok)}", EXIT_GATE)
    rd = run_path(run_id)
    if stage == "S07r" and not (rd / "r_independent.json").is_file():
        raise StateError("S07r cannot be done without r_independent.json", EXIT_MISSING)
    missing, files = [], {}
    for d in s["declared_outputs"]:
        p = rd / d
        if not p.exists() or (p.is_dir() and not any(p.rglob("*"))):
            missing.append(d)
        else:
            for f in _hash_targets(p):
                files[paths.portable(f, run=rd)] = f
    for o in outputs:
        port, p = _portable_in_run(st, o)
        if not p.exists():
            missing.append(port)
            continue
        for f in _hash_targets(p):
            files[paths.portable(f, run=rd)] = f
    if missing:
        raise StateError(f"{stage}: declared output(s) missing: {', '.join(missing)}", EXIT_MISSING)
    s["outputs"] = [{"path": k, "sha256": sha256_file(v)} for k, v in sorted(files.items())]
    s.update(status="done", finished=now())
    for k, f in files.items():           # pristine snapshot for idempotent apply-audit (§7.7)
        rel = k[len("run:"):]
        if not rel.startswith(("pristine/", "sealed/")):
            dst = rd / "pristine" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dst)
    if stage == "S07":
        _activate_adjudication(st, rd)
    save(st)
    return st


def _activate_adjudication(st, rd):
    p = rd / "redteam.json"
    if "S07b" not in st["stages"] or not p.exists():
        return
    try:
        contests = read_json(p).get("contests", [])
    except (ValueError, AttributeError):
        contests = []          # an invalid red-team file fails G5, not here
    open_contests = [c for c in contests if isinstance(c, dict) and c.get("outcome") == "to-adjudicator"]
    st["stages"]["S07b"]["status"] = "pending" if open_contests else "skipped"


def fail(run_id, stage, note=""):
    st = load(run_id)
    _check_open(st)
    s = _get_stage(st, stage)
    s.update(status="failed", finished=now(), note=note or s["note"])
    save(st)
    return st


def next_stages(run_id):
    st = load(run_id)
    _check_open(st)
    reset = verify_outputs(st)
    if reset:
        save(st)
    return st, ready(st), reset


def close(run_id, abort=False, force=False):
    st = load(run_id)
    _check_open(st)
    last = last_stage(st)
    if abort or force:
        require_tty(f"state close --run {run_id} --{'abort' if abort else 'force'}", st.get("python", "python3"))
        if not confirm(f"Close run {run_id} without finishing it?", run_id):
            raise StateError("not confirmed", EXIT_GATE)
        st["status"] = "closed"
        st["closed_note"] = "aborted" if abort else "forced"
    else:
        if st["stages"][last]["status"] != "done":
            raise StateError(f"run {run_id} closes after {last}, which is {st['stages'][last]['status']}", EXIT_GATE)
        st["status"] = "closed"
    st["closed"] = now()
    save(st)
    marker_remove(run_id)
    return st, END_MESSAGES[st["mode"]].format(id=run_id)


def reset(run_id, stage=None):
    st = load(run_id)
    _check_open(st)
    require_tty(f"state reset --run {run_id}" + (f" --stage {stage}" if stage else ""), st.get("python", "python3"))
    if stage is not None:
        _get_stage(st, stage)
    names = set(st["stages"]) if stage is None else {stage} | dependents(st, stage)
    _reset(st, names, "reset by user")
    save(st)
    return st


def resume(run_id):
    st = load(run_id)
    _check_open(st)
    if st["status"] not in ("waiting-external", "failed", "active"):
        raise StateError(f"run {run_id} cannot resume from {st['status']}", EXIT_GATE)
    st["status"] = "active"
    reset_names = verify_outputs(st)
    save(st)
    marker_add(st)
    return st, reset_names


def set_waiting_external(run_id):
    st = load(run_id)
    _check_open(st)
    st["status"] = "waiting-external"
    save(st)
    marker_remove(run_id)
    return st


# ------------------------------------------------------------------ retry (#84)

def _gate_failed(st, stage, gate):
    rd = run_path(st["run_id"])
    if gate == "G2":
        if not stage.startswith("S04:"):
            return False, "G2 applies to a scorer stage S04:<ID>"
        inst = stage.split(":", 1)[1]
        p = rd / "calibration.json"
        if not p.exists():
            return False, "no calibration.json"
        cal = read_json(p)
        drift = any((r.get("per_scorer", {}).get(inst) or {}).get("drift") for r in cal.get("refs", {}).values())
        return drift, f"calibration shows no drift for {inst}"
    if gate == "G4":
        p = rd / "alpha.json"
        return (p.exists() and read_json(p).get("gate") is False), "alpha.json gate did not fail"
    if gate == "G5":
        p = rd / "redteam.json"
        if not p.exists():
            return True, ""
        rt = read_json(p)
        scope = rd / "audit_scope.json"
        covered = {c.get("c") for c in rt.get("contests", [])} | {c.get("c") for c in rt.get("changes", [])}
        missing = scope.exists() and bool(set(read_json(scope).get("cells", [])) - covered)
        return (rt.get("completed") is not True or missing), "redteam.json is complete"
    if gate == "G6":
        p = rd / "lens-audit.json"
        return (not p.exists() or (read_json(p).get("checked") or {}).get("L4", 0) < 34), "lens audit checked all 34 L4 cells"
    if gate == "G7":
        p = rd / "review.json"
        return (p.exists() and read_json(p).get("verdict") == "fail"), "review.json verdict is not fail"
    return False, f"unknown gate {gate}"


GATE_STAGE = {"G2": "S04:", "G4": "S06", "G5": "S07", "G6": "S09", "G7": "S16"}


def retry(run_id, stage, gate):
    st = load(run_id)
    _check_open(st)
    if gate not in RETRY_BOUNDS:
        raise StateError(f"unknown gate {gate}", EXIT_USAGE)
    want = GATE_STAGE[gate]
    if not (stage.startswith(want) if gate == "G2" else stage == want):
        raise StateError(f"gate {gate} retries stage {want}{'<ID>' if gate == 'G2' else ''}, not {stage}", EXIT_USAGE)
    _get_stage(st, stage)
    failed, why = _gate_failed(st, stage, gate)
    if not failed:
        raise StateError(f"retry refused: the engine records do not show {gate} failed for {stage} ({why})", EXIT_GATE)
    key = f"{gate}:{stage}" if gate == "G2" else gate
    used = st["retries"].get(key, 0)
    if used >= RETRY_BOUNDS[gate]:
        raise StateError(f"retry refused: {gate} is bounded to {RETRY_BOUNDS[gate]} for {stage}", EXIT_GATE)
    st["retries"][key] = used + 1
    stg = st["stages"]
    if gate == "G2":
        inst = stage.split(":", 1)[1]
        if inst.endswith("r"):
            raise StateError("a replacement scorer is not replaced again (at most one per instance)", EXIT_GATE)
        new = f"S04:{inst}r"
        stg[new] = _stage(stg[stage]["deps"], [f"sealed/{inst}r/"])
        slot = "S1" if inst == "S1" else "S2" if inst == "S2" else inst
        st["instances"][slot] = f"{inst}r"
        for v in stg.values():
            v["deps"] = [new if d == stage else d for d in v["deps"]]
        opened = new
        _reset(st, dependents(st, new), f"reset by retry {gate}")
    elif gate == "G4":
        new = "S06b:S3"
        stg[new] = _stage(["S05"], ["sealed/S3/"])
        if "S3" not in st["instances"]["extra"]:
            st["instances"]["extra"].append("S3")
        if new not in stg["S06"]["deps"]:
            stg["S06"]["deps"].append(new)
        _reset(st, {"S06"} | dependents(st, "S06"), f"reset by retry {gate}")
        stg["S06"].update(status="pending")
        opened = new
    else:
        names = {stage} | dependents(st, stage)
        _reset(st, names, f"reset by retry {gate}")
        stg[stage]["status"] = "pending"
        stg[stage]["retries"] = stg[stage].get("retries", 0) + 1
        opened = stage
    save(st)
    from . import runlog
    runlog.engine_note(st, f"retry {gate} on {stage}: opened {opened}")
    return st, opened


def active_instances(st):
    """Scorer instances whose cells feed reconciliation and alpha (#93)."""
    inst = st.get("instances") or {"S1": "S1", "S2": "S2", "extra": []}
    return [inst["S1"], inst["S2"]] + list(inst.get("extra", []))


# ------------------------------------------------------------------ CLI

def configure(p):
    sub = p.add_subparsers(dest="action", metavar="<action>")
    sub.required = True
    i = sub.add_parser("init", help="create a run")
    i.add_argument("--run", required=True)
    i.add_argument("--mode", required=True, choices=MODES)
    i.add_argument("--slug", default=None)
    i.add_argument("--sources", default="")
    i.add_argument("--seed", type=int, default=None)
    i.add_argument("--status", default="implemented", choices=["implemented", "design-only"])
    i.add_argument("--type", dest="type_", default="open", choices=["open", "closed", "docs"])
    i.add_argument("--cal-refs", default=None, help="comma-separated calibration references")
    i.add_argument("--scorer-model", default=None)
    i.add_argument("--publisher", default=None)
    i.add_argument("--self-assessment", action="store_true")
    i.add_argument("--isolation", default="subagent", choices=["subagent", "fresh-session"])
    i.add_argument("--python", default="python3", choices=["python3", "python", "py -3"])
    i.add_argument("--with-analysis", action="store_true", help="reference mode: also run S13 and S14")
    i.add_argument("--second-assessor", action="store_true", help="docs mode: run D2")
    i.add_argument("--lineage", action="store_true", help="docs mode: run S13")
    i.add_argument("--host", default=None)
    for name in ("next", "list", "reset", "start", "done", "fail", "close", "resume", "retry"):
        q = sub.add_parser(name)
        if name != "list":
            q.add_argument("--run", required=True)
        if name in ("reset", "start", "done", "fail", "retry"):
            q.add_argument("--stage", required=(name != "reset"))
        if name == "done":
            q.add_argument("--outputs", nargs="*", default=[])
        if name == "start":
            q.add_argument("--host", default=None)
            q.add_argument("--model", default=None)
        if name == "fail":
            q.add_argument("--note", default="")
        if name == "close":
            g = q.add_mutually_exclusive_group()
            g.add_argument("--abort", action="store_true")
            g.add_argument("--force", action="store_true")
        if name == "retry":
            q.add_argument("--gate", required=True)
        if name == "list":
            q.add_argument("--cleanup", action="store_true", help="clean stale entries (interactive)")


def run(args):
    try:
        return _run(args)
    except (StateError, paths.PathError) as e:
        print(f"state {args.action}: {e}", file=sys.stderr)
        return e.code


def _run(args):
    a = args.action
    if a == "init":
        if args.mode not in ("compare", "fitgap") and not args.slug:
            raise StateError("--slug is required", EXIT_USAGE)
        st = init(args.run, args.mode, args.slug or args.mode, sources=[s for s in args.sources.split(",") if s],
                  seed=args.seed, status=args.status, type_=args.type_,
                  cal_refs=[c for c in (args.cal_refs or "").split(",") if c] or None, scorer_model=args.scorer_model,
                  publisher=args.publisher, self_assessment=args.self_assessment, isolation=args.isolation,
                  python=args.python, with_analysis=args.with_analysis, second_assessor=args.second_assessor,
                  lineage=args.lineage, host=args.host)
        print(f"state init: {st['run_id']} ({st['mode']}), seed {st['seed']}, cal_refs {st['cal_refs']}, "
              f"{st['comparison']}")
        return EXIT_OK
    if a == "list":
        return _list(args)
    if a == "next":
        st, names, reset_names = next_stages(args.run)
        for r in reset_names:
            print(f"reset (output changed): {r}")
        if not names:
            last = last_stage(st)
            print(f"nothing ready; last stage {last} is {st['stages'][last]['status']}")
        for n in names:
            print(f"{n}\t{HINTS.get(n.split(':')[0], '')}")
        return EXIT_OK
    if a == "start":
        start(args.run, args.stage, args.host, args.model)
    elif a == "done":
        done(args.run, args.stage, args.outputs)
    elif a == "fail":
        fail(args.run, args.stage, args.note)
    elif a == "close":
        st, msg = close(args.run, args.abort, args.force)
        print(msg)
        return EXIT_OK
    elif a == "reset":
        reset(args.run, args.stage)
    elif a == "resume":
        st, reset_names = resume(args.run)
        for r in reset_names:
            print(f"reset (output changed): {r}")
    elif a == "retry":
        st, opened = retry(args.run, args.stage, args.gate)
        print(f"state retry: opened {opened}")
        return EXIT_OK
    print(f"state {a}: ok")
    return EXIT_OK


def _list(args):
    data = paths.data_dir()
    runs = sorted((data / "runs").glob("*/state.json")) if (data / "runs").is_dir() else []
    stale = {e.get("run_id"): why for e, why in stale_entries()}
    for sp in runs:
        s = read_json(sp)
        order = list(s["stages"])
        done_ = [k for k in order if s["stages"][k]["status"] == "done"]
        last = done_[-1] if done_ else "-"
        flag = f"  STALE: {stale[s['run_id']]}" if s["run_id"] in stale else ""
        print(f"{s['run_id']}\t{s['mode']}\t{s['status']}\tlast done: {last}{flag}")
    for rid, why in stale.items():
        if not any(sp.parent.name == rid for sp in runs):
            print(f"{rid}\t(marker only)\tSTALE: {why}")
    if args.cleanup:
        require_tty("state list --cleanup")
        if stale and confirm(f"Clean {len(stale)} stale entr(y/ies)?", "yes"):
            for rid, why in cleanup_stale():
                print(f"cleaned {rid}: marked failed ({why})")
    return EXIT_OK


def configure_tty(p):
    pass


def run_tty(args):
    if is_interactive():
        print("tty-check: interactive")
        return EXIT_OK
    msg = "tty-check: not interactive (privileged subcommands will be refused)"
    if mintty():
        msg += "; Git Bash/mintty detected: use PowerShell, cmd or Windows Terminal"
    print(msg)
    return EXIT_GATE
