"""The repository itself passes the leak gate with the owner's denylist (Task 1.7).

- Locally: uses `.leakcheck/denylist.txt`; skips when it is absent.
- CI: uses the `LEAK_DENYLIST` secret (env). It fails on a push to the default
  branch when the secret is absent, and skips with a notice on a fork pull
  request, which receives no secrets (#65).
"""
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".leakcheck" / "denylist.txt"


def _is_fork_pr():
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        event = json.load(f)
    return bool(event.get("pull_request", {}).get("head", {}).get("repo", {}).get("fork"))


def _denylist(tmp_path):
    if LOCAL.exists():
        return LOCAL
    secret = os.environ.get("LEAK_DENYLIST", "")
    if secret.strip():
        p = tmp_path / "denylist.txt"
        p.write_text(secret + "\n", encoding="utf-8")
        return p
    if os.environ.get("CI"):
        if _is_fork_pr():
            pytest.skip("fork pull request: no secrets; the maintainer runs the denylist scan before merging")
        default = os.environ.get("AMA_DEFAULT_BRANCH", "main")
        if (os.environ.get("GITHUB_EVENT_NAME") == "push"
                and os.environ.get("GITHUB_REF") == f"refs/heads/{default}"):
            pytest.fail("LEAK_DENYLIST secret is absent on a push to the default branch")
        pytest.skip("CI without the LEAK_DENYLIST secret on a non-default branch")
    pytest.skip("no local owner denylist")


def test_repository_has_no_leaks(tmp_path):
    deny = _denylist(tmp_path)
    r = subprocess.run([sys.executable, "-m", "engine", "leakcheck", "--path", ".", "--ci",
                        "--denylist", str(deny)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
