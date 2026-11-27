"""Stable JSON output (plan §7.1): sort_keys, indent 2, ensure_ascii False, trailing
newline, LF line endings, and the portable-path check on everything persisted."""
import hashlib
import json
import os
import pathlib
import tempfile

from .paths import assert_portable


def dumps(obj):
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_json(path, obj, portable=True):
    """Atomic write. Raises paths.NotPortable before writing if any string embeds an absolute path."""
    if portable:
        assert_portable(obj)
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(obj))
    os.replace(tmp, p)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalized_bytes(data):
    """LF-normalized bytes, the form hashed and counted everywhere (§7.5, §7.8)."""
    return data.replace(b"\r\n", b"\n")
