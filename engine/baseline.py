"""Shipped baseline: round resolution (plan §0.3 #42). `verify` and `promote` follow in Task 1.6/2.x."""
import pathlib


def current_round(root="."):
    p = pathlib.Path(root) / "baseline" / "current"
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def round_dir(root=".", round_id=None):
    rid = round_id or current_round(root) or "_none_"
    return pathlib.Path(root) / "baseline" / "rounds" / rid
