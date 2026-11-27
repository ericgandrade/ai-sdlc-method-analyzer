"""`engine fetch` (plan §7.4; Task 2.5). Uses a local bare repository and a localhost
http.server only; no external network."""
import functools
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading

import pytest

from engine import fetch

ROOT = pathlib.Path(__file__).resolve().parents[1]
AT = "@"
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=noreply" + AT + "example.invalid",
                           "-c", "commit.gpgsign=false", *a], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def remote(tmp_path):
    work = tmp_path / "src"
    work.mkdir()
    git(work, "init", "-q", "-b", "main")
    (work / "SKILL.md").write_text("---\nname: tiny\n---\nfirst\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "one")
    first = git(work, "rev-parse", "HEAD").stdout.strip()
    (work / "SKILL.md").write_text("---\nname: tiny\n---\nsecond\n")
    git(work, "commit", "-q", "-am", "two")
    second = git(work, "rev-parse", "HEAD").stdout.strip()
    bare = tmp_path / "tiny.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True, capture_output=True)
    return bare.as_uri(), first, second


def project(tmp_path, url, pin, docs=None, slug="tiny", ref_type="open"):
    root = tmp_path / "proj"
    (root / "references").mkdir(parents=True)
    lines = ["schema: 1", "references:", f"  - slug: \"{slug}\"", "    name: \"Tiny\"", f"    url: \"{url}\"",
             f"    pin: \"{pin}\"", f"    type: \"{ref_type}\"", "    licence: \"MIT\""]
    if docs:
        lines.append("    docs:")
        for d in docs:
            lines += [f"      - url: \"{d['url']}\"", f"        snapshot_date: \"2026-11-26\"", f"        file: \"{d['file']}\""]
    else:
        lines.append("    docs: []")
    (root / "references" / "registry.yaml").write_text("\n".join(lines) + "\n")
    return root


def engine(root, *a, env=None):
    e = dict(os.environ, **(env or {}))
    e["PYTHONPATH"] = str(ROOT)
    return subprocess.run([sys.executable, "-m", "engine", "fetch", "--root", str(root), *a], cwd=root,
                          capture_output=True, text=True, env=e, stdin=subprocess.DEVNULL)


@needs_git
def test_fetch_pin_and_head(tmp_path, remote):
    url, first, second = remote
    root = project(tmp_path, url, first)
    r = engine(root, "--slug", "tiny")
    assert r.returncode == 0, r.stderr
    dest = pathlib.Path(os.environ["AMA_HOME"]) / "cache" / "refs" / "tiny"
    assert fetch.head(dest) == first
    assert "first" in (dest / "SKILL.md").read_text()
    assert subprocess.run(["git", "-C", str(dest), "config", "core.autocrlf"], capture_output=True,
                          text=True).stdout.strip() == "false"
    assert "cached" in engine(root, "--slug", "tiny").stdout
    root2 = project(tmp_path / "b", url, second)
    assert engine(root2, "--all").returncode == 0
    assert fetch.head(dest) == second


@needs_git
def test_wrong_pin_exit_4(tmp_path, remote):
    url, first, _ = remote
    root = project(tmp_path, url, "1" * 40)
    r = engine(root, "--slug", "tiny")
    assert r.returncode == 4, r.stderr


def test_offline_with_empty_cache_exit_6(tmp_path):
    root = project(tmp_path, "https://example.invalid/tiny.git", "1" * 40)
    assert engine(root, "--slug", "tiny", "--offline").returncode == 6
    assert engine(root, "--all", env={"AMA_OFFLINE": "1"}).returncode == 6


@needs_git
def test_offline_with_cache_present_exit_0(tmp_path, remote):
    url, first, _ = remote
    root = project(tmp_path, url, first)
    assert engine(root, "--slug", "tiny").returncode == 0
    assert engine(root, "--slug", "tiny", "--offline").returncode == 0


def test_credential_url_refused_exit_2(tmp_path):
    root = project(tmp_path, "https://user:tok" + AT + "example.invalid/tiny.git", "1" * 40)
    r = engine(root, "--slug", "tiny")
    assert r.returncode == 2 and "credential" in r.stderr
    assert fetch.has_credentials("https://u" + AT + "h/x") and not fetch.has_credentials("git" + AT + "github.com:o/r.git")


def test_cache_is_outside_the_project(tmp_path):
    root = project(tmp_path, "https://example.invalid/x.git", "1" * 40)
    r = engine(root, "--slug", "tiny", env={"AMA_HOME": str(root / "data")})
    assert r.returncode == 2 and "inside the project" in r.stderr


@pytest.mark.network_local
def test_docs_manifest_from_localhost(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "a.html").write_text("<h1>A</h1><a href='b.html'>b</a>")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        out, failed = fetch.fetch_docs("tiny", [{"url": f"{base}/a.html", "file": "a.html", "snapshot_date": "2026-11-26"},
                                                {"url": f"{base}/missing.html", "file": "m.html", "snapshot_date": "2026-11-26"}],
                                       tmp_path / "docs", today="2026-11-27")
    finally:
        srv.shutdown()
    man = json.loads((out / "MANIFEST.json").read_text())
    ok = [p for p in man["pages"] if p["status"] == "ok"]
    assert failed == 1 and len(ok) == 1
    assert ok[0]["sha256"] == __import__("hashlib").sha256((site / "a.html").read_bytes()).hexdigest()
    assert not (out / "b.html").exists()       # links are never followed


def test_tokenizer_absent_is_a_notice(tmp_path, monkeypatch):
    import builtins
    real = builtins.__import__

    def no_tiktoken(name, *a, **k):
        if name == "tiktoken":
            raise ImportError
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", no_tiktoken)
    assert fetch.prime_tokenizer(tmp_path) == "absent"
