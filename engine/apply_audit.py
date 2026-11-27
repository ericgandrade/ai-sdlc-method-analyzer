"""`engine apply-audit --run <id>` (plan §7.7): apply the red team and the lens audit.

Always starts from the pristine inputs that `state done` snapshotted (runs/<id>/pristine/),
falling back to the working file only when no snapshot exists, so running it twice gives
byte-identical outputs. It never edits its inputs. Order:
  1. red-team `final` replaces the reconciled L1 vector (and `final_r` the r vector, design-only);
  2. upheld adjudication decisions apply after it;
  3. lens-audit overrides touch only the listed L2, L3 and L4 cells;
  4. L5_corrections add or remove list entries; an added path that does not resolve exits 3.
Writes l1.final.json and lenses.final.json.
"""
import copy
import sys

from . import paths, state
from .common import CRITERIA, EXIT_GATE, EXIT_MISSING, EXIT_OK
from .jsonio import read_json, write_json


class AuditError(Exception):
    def __init__(self, message, code=EXIT_GATE):
        super().__init__(message)
        self.code = code


def _input(rd, name, required=True):
    for p in (rd / "pristine" / name, rd / name):
        if p.exists():
            return read_json(p)
    if required:
        raise AuditError(f"{name} missing", EXIT_MISSING)
    return None


def apply_l1(reconciled, redteam, adjudication, design):
    vector = list(redteam["final"]) if redteam and redteam.get("final") else list(reconciled["vector"])
    r = None
    if design:
        r = list((redteam or {}).get("final_r") or reconciled.get("r") or [1.0] * 16)
    applied, boundary = [], []
    for d in (adjudication or {}).get("decisions", []):
        if d.get("decision") != "upheld":
            continue
        i = CRITERIA.index(d["c"])
        if d["kind"] == "score":
            vector[i] = d["after"]
        elif d["kind"] == "r" and r is not None:
            r[i] = d["after_r"]
        elif d["kind"] == "boundary":
            boundary.append({"c": d["c"], "verdict": d.get("boundary_verdict"), "path": d.get("path")})
        applied.append(d.get("contest_id"))
    out = {"vector": vector, "r": r, "ra": [round(v * x, 2) for v, x in zip(vector, r)] if r else None,
           "source": "redteam.final" if redteam and redteam.get("final") else "reconciled.vector",
           "adjudicated": applied, "boundary": boundary}
    return out


def apply_lenses(lenses, audit, resolve):
    out = copy.deepcopy(lenses)
    ov = (audit or {}).get("overrides") or {}
    if ov.get("L3"):
        out["L3"]["level"] = ov["L3"]
        out["L3"]["audit_override"] = True
    if ov.get("L2"):
        if out.get("L2") is None:
            raise AuditError("lens audit overrides L2 but lenses.json has no L2 pass")
        ceiling = out["L2"].setdefault("ceiling", {})
        for c, v in sorted(ov["L2"].items()):
            ceiling.setdefault(c, {})["s"] = v
            ceiling[c]["audit_override"] = True
    for f, v in sorted((ov.get("L4") or {}).items()):
        if f not in out["L4"]:
            raise AuditError(f"lens audit overrides unknown item {f}")
        out["L4"][f]["v"] = v
        out["L4"][f]["audit_override"] = True
    if "L4_total" in out:
        out["L4_total"] = sum(x["v"] for x in out["L4"].values() if isinstance(x["v"], int))
    corr = (audit or {}).get("L5_corrections") or {}
    for tier in ("T1", "T2", "T3"):
        lst = out["L5"].get(tier)
        if lst is None:
            if corr.get(f"{tier}_add"):
                raise AuditError(f"L5 {tier} is not measurable here; nothing can be added")
            continue
        remove = set(corr.get(f"{tier}_remove") or [])
        lst = [e for e in lst if e["path"] not in remove]
        have = {e["path"] for e in lst}
        for p in corr.get(f"{tier}_add") or []:
            if not resolve(p):
                raise AuditError(f"added L5 path does not resolve: {p}", EXIT_MISSING)
            if p not in have:
                lst.append({"path": p, "frontmatter_only": tier == "T1", "why": "added by the lens audit"})
                have.add(p)
        out["L5"][tier] = lst
    return out


def apply(run_id):
    st = state.load(run_id)
    rd = state.run_path(run_id)
    design = (st.get("target") or {}).get("status") == "design-only"
    l1 = apply_l1(_input(rd, "reconciled.json"), _input(rd, "redteam.json", False),
                  _input(rd, "adjudication.json", False), design)

    def resolve(p):
        try:
            return paths.resolve(p, run=rd).is_file()
        except paths.PathError:
            return False

    lenses = apply_lenses(_input(rd, "lenses.json"), _input(rd, "lens-audit.json", False), resolve)
    write_json(rd / "l1.final.json", l1)
    write_json(rd / "lenses.final.json", lenses)
    return l1, lenses


def configure(p):
    p.add_argument("--run", required=True)


def run(args):
    try:
        l1, _ = apply(args.run)
    except (AuditError, state.StateError, paths.PathError) as e:
        print(f"apply-audit: {e}", file=sys.stderr)
        return e.code
    print(f"apply-audit: l1.final.json ({l1['source']}, {len(l1['adjudicated'])} adjudicated) and lenses.final.json")
    return EXIT_OK
