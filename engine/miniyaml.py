"""A strict YAML subset parser (stdlib has none). Plan Task 1.5.

Accepted: 2-space indentation; mappings `key: scalar` and `key:` + nested block;
block lists (`- scalar`, `- key: v` starting a mapping); inline `[]` and flow
lists of scalars `[a, b]`; `#` comments; quoted and unquoted strings,
integers, `true`/`false`/`null`.

Rejected with a line number: tabs, anchors and aliases, block scalars (`|`,
`>`), flow maps, nested flow lists, bad indentation, duplicate keys.
"""
import re


class MiniYamlError(ValueError):
    def __init__(self, line, msg):
        super().__init__(f"line {line}: {msg}")
        self.line = line


_INT = re.compile(r"^-?\d+$")
_KEY = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:\s+(.*))?$")


def _strip_comment(s, n):
    out, quote = [], None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            if i == 0 or s[i - 1] in " [,:":
                quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] == " "):
            break
        out.append(ch)
    if quote:
        raise MiniYamlError(n, "unterminated quoted string")
    return "".join(out).rstrip()


def _scalar(s, n):
    s = s.strip()
    if s == "":
        raise MiniYamlError(n, "empty value (use null)")
    if s[0] in "&*!":
        raise MiniYamlError(n, "anchors, aliases and tags are not supported")
    if s[0] in "|>":
        raise MiniYamlError(n, "block scalars are not supported")
    if s[0] == "{":
        raise MiniYamlError(n, "flow maps are not supported")
    if s[0] in "\"'":
        q = s[0]
        if len(s) < 2 or s[-1] != q:
            raise MiniYamlError(n, "bad quoted string")
        body = s[1:-1]
        if q == "'":
            return body.replace("''", "'")
        return body.replace('\\"', '"').replace("\\\\", "\\")
    if s == "[]":
        return []
    if s[0] == "[":
        if s[-1] != "]":
            raise MiniYamlError(n, "unterminated flow list")
        inner = s[1:-1]
        if "[" in inner or "{" in inner:
            raise MiniYamlError(n, "nested flow collections are not supported")
        return [_scalar(x, n) for x in inner.split(",")]
    if s in ("true", "false"):
        return s == "true"
    if s in ("null", "~"):
        return None
    if _INT.match(s):
        return int(s)
    if ": " in s:
        raise MiniYamlError(n, "unquoted ': ' inside a scalar")
    return s


def _lines(text):
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise MiniYamlError(n, "tabs are not allowed")
        body = _strip_comment(raw, n)
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        if indent % 2:
            raise MiniYamlError(n, "indentation must be a multiple of 2 spaces")
        out.append((n, indent, body.strip()))
    return out


def loads(text):
    lines = _lines(text)
    if not lines:
        return None
    pos = [0]

    def block(indent):
        n, ind, content = lines[pos[0]]
        if ind != indent:
            raise MiniYamlError(n, "unexpected indentation")
        return seq(indent) if content == "-" or content.startswith("- ") else mapping(indent)

    def mapping(indent, first=None):
        result = {}
        while pos[0] < len(lines):
            n, ind, content = lines[pos[0]]
            if first is not None:
                content, first = first, None
            elif ind < indent:
                break
            elif ind > indent:
                raise MiniYamlError(n, "unexpected indentation")
            if content.startswith("- "):
                raise MiniYamlError(n, "list item where a key was expected")
            m = _KEY.match(content)
            if not m:
                raise MiniYamlError(n, "expected 'key: value'")
            key, value = m.group(1), m.group(2)
            if key in result:
                raise MiniYamlError(n, f"duplicate key {key!r}")
            pos[0] += 1
            if value is None or value == "":
                if pos[0] < len(lines) and lines[pos[0]][1] > indent:
                    result[key] = block(indent + 2)
                elif pos[0] < len(lines) and lines[pos[0]][1] == indent and lines[pos[0]][2].startswith("- "):
                    result[key] = seq(indent)
                else:
                    raise MiniYamlError(n, "missing value (use null or [])")
            else:
                result[key] = _scalar(value, n)
        return result

    def seq(indent):
        result = []
        while pos[0] < len(lines):
            n, ind, content = lines[pos[0]]
            if ind < indent or not content.startswith("- "):
                if ind > indent:
                    raise MiniYamlError(n, "unexpected indentation")
                break
            if ind > indent:
                raise MiniYamlError(n, "unexpected indentation")
            item = content[2:].strip()
            if _KEY.match(item):
                result.append(mapping(indent + 2, first=item))
            else:
                pos[0] += 1
                result.append(_scalar(item, n))
        return result

    value = block(0)
    if pos[0] != len(lines):
        n = lines[pos[0]][0]
        raise MiniYamlError(n, "unexpected content")
    return value


def load(path):
    with open(path, encoding="utf-8") as f:
        return loads(f.read())
