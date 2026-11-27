"""Theme validation (plan §8.4). A theme only sets custom properties on `:root`, optionally inside
`@media (prefers-color-scheme: …)`. Anything else is refused with the offending line."""
import pathlib
import re

REQUIRED = ["--ink", "--ink-soft", "--ink-faint", "--paper", "--wash", "--accent", "--accent-2",
            "--pos", "--neg", "--rule", "--rule-soft", "--font", "--mono"]
FORBIDDEN = ["url(", "@import", "@font-face", "http", "expression(", "\\"]
MEDIA = re.compile(r"@media\s*\(\s*prefers-color-scheme\s*:\s*(light|dark)\s*\)")
DECL = re.compile(r"(--[A-Za-z0-9-]+)\s*:\s*([^;{}]+?)\s*")


class ThemeError(ValueError):
    pass


def _strip_comments(text):
    """Replace comments by spaces, keeping newlines so line numbers stay right."""
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def parse(text):
    """Return {"light": {token: value}, "dark": {token: value}}; raise ThemeError on the first problem."""
    text = text.replace("\r\n", "\n")
    raw_lines = text.split("\n")
    body = _strip_comments(text)

    def fail(pos, msg):
        n = body.count("\n", 0, pos) + 1
        raise ThemeError(f"line {n}: {msg}: {raw_lines[n - 1].strip()}")

    for word in FORBIDDEN:
        i = body.lower().find(word)
        if i >= 0:
            fail(i, f"forbidden construct {word!r}")
    out = {"light": {}, "dark": {}}
    stack, pos, n = [], 0, len(body)
    while pos < n:
        ctx = stack[-1][0] if stack else None
        stops = ";}" if ctx == "root" else "{};"
        j = pos
        while j < n and body[j] not in stops:
            j += 1
        chunk, start = body[pos:j].strip(), pos + (len(body[pos:j]) - len(body[pos:j].lstrip()))
        if j >= n:
            if chunk or stack:
                fail(start if chunk else n - 1, "unterminated block")
            break
        ch = body[j]
        if ctx == "root":
            if chunk:
                m = DECL.fullmatch(chunk)
                if not m:
                    fail(start, "only --* declarations are allowed")
                out[stack[-1][1]][m.group(1)] = m.group(2)
            if ch == "}":
                stack.pop()
        elif ch == "{":
            if ctx is None and chunk == ":root":
                stack.append(("root", "light"))
            elif ctx is None and MEDIA.fullmatch(chunk):
                stack.append(("media", MEDIA.fullmatch(chunk).group(1)))
            elif ctx == "media" and chunk == ":root":
                stack.append(("root", stack[-1][1]))
            else:
                fail(start, "only :root and @media (prefers-color-scheme) blocks are allowed")
        elif ch == "}":
            if chunk or not stack:
                fail(start, "unexpected '}'")
            stack.pop()
        else:
            fail(start, "declaration outside :root")
        pos = j + 1
    missing = [t for t in REQUIRED if t not in out["light"]]
    if missing:
        raise ThemeError(f"missing required tokens: {', '.join(missing)}")
    return out


def load(path):
    """Validated theme text (LF line endings), ready to inline."""
    text = pathlib.Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    parse(text)
    return text


# ------------------------------------------------------------------ WCAG 2 contrast

def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_):
    h = hex_.lstrip("#")
    if len(h) == 3:
        h = "".join(x * 2 for x in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
