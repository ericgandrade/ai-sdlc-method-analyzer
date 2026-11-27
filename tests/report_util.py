"""Shared helpers for the report tests."""
import pathlib

from engine import report_html, theme

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "report-run"
BASE = ROOT / "baseline" / "rounds" / "2026-11" / "derived"
THEME = ROOT / "themes" / "neutral.css"


def inputs(src=FIX, date="2026-01-01"):
    return report_html.load_inputs(src, ROOT, date)


def html(src=FIX, date="2026-01-01"):
    return report_html.render(inputs(src, date), theme.load(THEME))
