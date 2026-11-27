"""Portable path notation (plan §0.3, §7.1). Resolution of cache:/target:/run: paths
arrives with the run layer (Phase 2); this module already holds the persisted-JSON check."""

import re

# An absolute path anywhere inside a string: POSIX root, Windows drive, or home tilde.
# URLs pass, because `//` does not match `/[A-Za-z]`.
ABSOLUTE = re.compile(r"(^|[\s(\"';,=])(/[A-Za-z]|[A-Za-z]:\\|~/)")


class NotPortable(ValueError):
    pass


def assert_portable(obj, where="$"):
    """Raise NotPortable if any string value (or key) inside obj embeds an absolute path."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_portable(k, f"{where}.{k}")
            assert_portable(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_portable(v, f"{where}[{i}]")
    elif isinstance(obj, str) and ABSOLUTE.search(obj):
        raise NotPortable(f"absolute path in {where}")
