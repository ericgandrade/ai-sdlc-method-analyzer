"""Hook install and pre-push behaviour (plan §7.14 #51, Task 1.7)."""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AT = "@"
HOOK = ROOT / ".githooks" / "pre-push"
needs_sh = pytest.mark.skipif(shutil.which("sh") is None, reason="sh not available")


def env():
    e = dict(os.environ)
    e["PYTHONPATH"] = str(ROOT)
    e["AMA_PYTHON"] = sys.executable
    e.pop("CI", None)
    return e


def git(repo, *a, check=True):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t" + AT + "example.net",
                           "-c", "commit.gpgsign=false", *a], cwd=repo, check=check,
                          capture_output=True, text=True, env=env())


def engine(repo, *a, stdin=None):
    return subprocess.run([sys.executable, "-m", "engine", *a], cwd=repo, capture_output=True,
                          text=True, env=env(), input=stdin)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "work"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".githooks").mkdir()
    shutil.copy2(HOOK, r / ".githooks" / "pre-push")
    (r / ".leakcheck").mkdir()
    (r / "a.md").write_text("clean\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "c1")
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True)
    git(r, "remote", "add", "origin", str(bare))
    return r


def push(repo):
    return git(repo, "push", "-q", "origin", "main", check=False)


def test_install_sets_hooks_path(repo):
    assert engine(repo, "hooks", "install").returncode == 0
    assert git(repo, "config", "--get", "core.hooksPath").stdout.strip() == ".githooks"


def test_install_maintainer_requires_denylist(repo):
    assert engine(repo, "hooks", "install", "--maintainer").returncode == 3
    (repo / ".leakcheck" / "denylist.txt").write_text("ci:zorblax\n")
    assert engine(repo, "hooks", "install", "--maintainer").returncode == 0
    assert git(repo, "config", "--get", "ama.maintainer").stdout.strip() == "true"


@needs_sh
def test_non_maintainer_without_denylist_passes_with_notice(repo):
    engine(repo, "hooks", "install")
    r = push(repo)
    assert r.returncode == 0, r.stderr
    assert "denylist scan runs in CI" in r.stderr


@needs_sh
def test_maintainer_without_denylist_is_refused(repo):
    engine(repo, "hooks", "install")
    git(repo, "config", "ama.maintainer", "true")
    r = push(repo)
    assert r.returncode != 0
    assert "maintainer clone" in r.stderr


@needs_sh
def test_missing_ccbysa_cache_warns(repo):
    engine(repo, "hooks", "install")
    r = push(repo)
    assert "CC BY-SA corpus absent" in r.stderr


@needs_sh
def test_unpushed_denylist_hit_blocks_push(repo):
    (repo / ".leakcheck" / "denylist.txt").write_text("ci:zorblax\n")
    with open(repo / ".git" / "info" / "exclude", "a") as f:
        f.write(".leakcheck/denylist.txt\n")
    engine(repo, "hooks", "install", "--maintainer")
    assert push(repo).returncode == 0
    (repo / "b.md").write_text("the zorblax notes\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c2")
    r = push(repo)
    assert r.returncode != 0
    assert "deny#1" in r.stderr
    assert "zorblax" not in r.stderr


@needs_sh
def test_first_push_to_empty_remote_scans_every_commit(repo):
    (repo / "old.md").write_text("path /" + "Users" + "/dave/x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c2")
    git(repo, "rm", "-q", "old.md")
    git(repo, "commit", "-q", "-m", "c3")
    engine(repo, "hooks", "install")
    r = push(repo)
    assert r.returncode != 0
    assert "builtin:home-path" in r.stderr


def test_pre_push_reports_commit_count(repo):
    sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    r = engine(repo, "hooks", "pre-push", "origin", stdin=f"refs/heads/main {sha} refs/heads/main {'0' * 40}\n")
    assert r.returncode == 0
    assert "1 commit(s) scanned" in r.stderr


def test_already_pushed_content_is_not_rescanned(repo):
    # A built-in hit that is already on the remote does not block later pushes.
    (repo / "old.md").write_text("path /" + "Users" + "/erin/x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c2")
    git(repo, "push", "-q", "origin", "main")   # hook not installed here: history that predates the hook
    (repo / "new.md").write_text("clean\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c3")
    sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    old = git(repo, "rev-parse", "origin/main").stdout.strip()
    r = engine(repo, "hooks", "pre-push", "origin", stdin=f"refs/heads/main {sha} refs/heads/main {old}\n")
    assert r.returncode == 0, r.stderr
