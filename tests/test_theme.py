import pathlib

import pytest

from engine import theme

ROOT = pathlib.Path(__file__).resolve().parents[1]
NEUTRAL = (ROOT / "themes" / "neutral.css").read_text(encoding="utf-8")


def test_neutral_passes():
    t = theme.parse(NEUTRAL)
    assert set(theme.REQUIRED) <= set(t["light"])
    assert t["dark"]["--paper"] == "#0d1117"


def test_crlf_is_accepted():
    theme.parse(NEUTRAL.replace("\n", "\r\n"))


@pytest.mark.parametrize("bad, needle", [
    (":root{--ink:url(x.png);}", "url("),
    ("@import 'x.css';", "@import"),
    ("body{--ink:#000}", "only :root"),
    (":root{color:#000}", "only --*"),
    ("@font-face{--x:1}", "@font-face"),
    (":root{--x:\\41}", "\\"),
    ("@media print{:root{--ink:#000}}", "only :root"),
])
def test_bad_themes_fail(bad, needle):
    with pytest.raises(theme.ThemeError) as e:
        theme.parse(NEUTRAL + "\n" + bad + "\n")
    assert needle in str(e.value)
    assert "line " in str(e.value)


def test_missing_token_fails():
    with pytest.raises(theme.ThemeError, match="--mono"):
        theme.parse(NEUTRAL.replace("--mono:", "--mono-x:"))


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_wcag_contrast(mode):
    t = theme.parse(NEUTRAL)
    tok = dict(t["light"]) | t[mode]
    c = theme.contrast
    assert c(tok["--ink"], tok["--paper"]) >= 4.5
    assert c(tok["--ink-soft"], tok["--paper"]) >= 4.5
    assert c(tok["--paper"], tok["--ink"]) >= 4.5
    assert c(tok["--ink"], tok["--wash"]) >= 4.5
    assert c(tok["--ink-faint"], tok["--paper"]) >= 3.0
