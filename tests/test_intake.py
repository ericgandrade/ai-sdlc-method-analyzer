"""Intake, isolate, inventory, shuffle and estimate (plan §7.5, §6.5; Task 2.6)."""
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading
import time

import pytest

from engine import intake, paths, state
from engine.intake import IntakeError

ROOT = pathlib.Path(__file__).resolve().parents[1]
TINY = ROOT / "tests" / "fixtures" / "tiny-method"
RID = "20261127-101500-tiny"
REQ = "run:requests/intake/intake-request.json"
posix_only = pytest.mark.skipif(sys.platform.startswith("win"), reason="symlinks need privileges on Windows")


@pytest.fixture(autouse=True)
def at_root(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(state, "is_interactive", lambda: False)


def rd(rid=RID):
    return state.run_path(rid)


def new_run(mode="folder", rid=RID, slug="tiny", **kw):
    return state.init(rid, mode, slug, **kw)


def request(obj, rid=RID):
    p = rd(rid) / "requests" / "intake" / "intake-request.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj))
    return p


def copy_tiny(tmp_path, name="tiny"):
    d = tmp_path / name
    shutil.copytree(TINY, d)
    return d


def folder_intake(src, rid=RID, **extra):
    request({"mode": "folder", "source": str(src), "slug": "tiny", "name": "Tiny", "type": "open",
             "status": "implemented", **extra}, rid)
    return intake.intake(rid, REQ)


def all_json(d):
    for p in pathlib.Path(d).rglob("*.json"):
        yield json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- request rules (#77, #88)

def test_second_intake_refused(tmp_path):
    new_run()
    src = copy_tiny(tmp_path)
    folder_intake(src)
    with pytest.raises(IntakeError) as e:
        folder_intake(src)
    assert e.value.code == 1 and "already" in str(e.value)


def test_intake_after_s01_done_refused(tmp_path):
    new_run()
    for s in ("S00",):
        state.start(RID, s)
        state.done(RID, s)
    st = state.load(RID)
    st["stages"]["S01"]["status"] = "done"
    state.save(st)
    p = request({"mode": "folder", "source": str(copy_tiny(tmp_path)), "slug": "tiny"})
    with pytest.raises(IntakeError):
        intake.intake(RID, REQ)
    assert not p.exists()


def test_request_deleted_after_failed_intake_and_retry_allowed(tmp_path):
    new_run()
    p = request({"mode": "folder", "source": str(tmp_path / "absent"), "slug": "tiny"})
    with pytest.raises(IntakeError) as e:
        intake.intake(RID, REQ)
    assert e.value.code == 3 and not p.exists()
    assert folder_intake(copy_tiny(tmp_path))["pin"].startswith("tree:")


def test_odd_characters_in_source_path(tmp_path):
    new_run()
    odd = tmp_path / "my (odd) & ! ~ $ {dir}"
    shutil.copytree(TINY, odd)
    p = request({"mode": "folder", "source": str(odd), "slug": "tiny", "name": "Tiny (odd) & co"})
    r = subprocess.run([sys.executable, "-m", "engine", "intake", "--run", RID, "--request", REQ], cwd=ROOT,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    assert not p.exists()
    for obj in all_json(rd()):
        paths.assert_portable(obj)
    assert str(tmp_path) not in "".join(f.read_text(encoding="utf-8") for f in rd().rglob("*.json"))


def test_request_must_be_the_intake_request(tmp_path):
    new_run()
    with pytest.raises(IntakeError):
        intake.intake(RID, "run:requests/log/x.json")


# ---------------------------------------------------------------- folder snapshot

def test_folder_snapshot_and_flags(tmp_path):
    new_run()
    src = copy_tiny(tmp_path)
    (src / "dist").mkdir()
    (src / "dist" / "plugin.json").write_text("{}\n")
    (src / "node_modules").mkdir()
    (src / "node_modules" / "x.js").write_text("x")
    (src / "env").mkdir()
    (src / "env" / "pyvenv.cfg").write_text("home = x\n")
    rec = folder_intake(src)
    tgt = rd() / "target"
    assert (tgt / "dist" / "plugin.json").exists()
    assert not (tgt / "node_modules").exists() and not (tgt / "env").exists()
    assert rec["private"] is True and rec["root"] == "target:" and rec["mode"] == "folder"
    assert state.load(RID)["stages"]["S01"]["status"] == "pending"


@posix_only
def test_symlinks_recorded_not_followed(tmp_path):
    new_run()
    src = copy_tiny(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret outside\n")
    (src / "ext.md").symlink_to(outside)
    (src / "int.md").symlink_to(src / "README.md")
    (src / "broken.md").symlink_to(src / "nope.md")
    (src / "skills" / "loop").symlink_to(src / "skills")       # a link loop
    rec = folder_intake(src)
    kinds = {l["path"]: l["kind"] for l in rec["symlinks"]}
    assert kinds == {"ext.md": "external", "int.md": "internal", "broken.md": "broken", "skills/loop": "internal"}
    assert not (rd() / "target" / "ext.md").exists()
    assert str(tmp_path) not in json.dumps(rec)


def test_size_warning(tmp_path, monkeypatch, capsys):
    new_run()
    monkeypatch.setattr(intake, "SIZE_WARN_BYTES", 10)
    src = copy_tiny(tmp_path)
    with pytest.raises(IntakeError):
        folder_intake(src)
    assert "over 200 MB" in capsys.readouterr().err
    assert folder_intake(src, accept_large=True)["files"] == 4


def test_t0_excludes_dist_only_with_declared_shipped_root(tmp_path):
    src = copy_tiny(tmp_path)
    (src / "dist").mkdir()
    (src / "dist" / "bundle.md").write_text("built copy\n")
    rels = lambda skip: {r for r, _, _ in intake.walk(src, skip_build=skip)}
    assert "dist/bundle.md" in rels(intake.skip_build_for(None))
    assert "dist/bundle.md" not in rels(intake.skip_build_for("skills/"))
    assert "dist/bundle.md" in rels(intake.skip_build_for("dist/"))


def test_tree_hash_stable_across_crlf_and_layout(tmp_path):
    a, b = copy_tiny(tmp_path, "a"), copy_tiny(tmp_path, "b")
    for f in a.rglob("*.md"):                     # the checkout may already use CRLF (Windows)
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    for f in b.rglob("*.md"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert intake.tree_hash(a) == intake.tree_hash(b)
    (b / "skills" / "plan" / "SKILL.md").write_text("changed\n")
    assert intake.tree_hash(a) != intake.tree_hash(b)


def test_resume_after_moving_original_and_g9(tmp_path):
    new_run()
    src = copy_tiny(tmp_path)
    folder_intake(src)
    shutil.move(str(src), str(tmp_path / "moved"))
    p = paths.resolve("target:skills/plan/SKILL.md", run=RID)
    assert p.read_text().startswith("---")
    assert intake.verify_snapshot(RID)
    p.write_text("edited after intake\n")
    with pytest.raises(IntakeError) as e:
        intake.verify_snapshot(RID)
    assert e.value.code == 4


def test_git_head_and_dirty_recorded(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git not available")
    new_run()
    src = copy_tiny(tmp_path)
    g = ["git", "-c", "user.name=t", "-c", "user.email=noreply" + "@" + "example.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(g + ["init", "-q"], cwd=src, check=True)
    subprocess.run(g + ["add", "-A"], cwd=src, check=True)
    subprocess.run(g + ["commit", "-q", "-m", "c"], cwd=src, check=True)
    (src / "README.md").write_text("dirty\n")
    rec = folder_intake(src)
    assert rec["dirty"] is True and len(rec["git_head"]) == 40
    assert not (rd() / "target" / ".git").exists()


# ---------------------------------------------------------------- detection

def test_self_score_candidates(tmp_path):
    src = copy_tiny(tmp_path)
    (src / "docs" / "scoring").mkdir(parents=True)
    (src / "docs" / "scoring" / "scorecard.md").write_text("# our score\n")
    (src / "README.md").write_text("# Tiny\n\n## Score\n\nWe rate ourselves 90.\n")
    cands = intake.self_score_candidates(src)
    assert "docs/scoring/scorecard.md" in cands and "README.md#score" in cands


def test_rubric_ids_flag(tmp_path):
    src = copy_tiny(tmp_path)
    assert intake.rubric_ids(src)["revised_against_rubric"] is False
    (src / "notes.md").write_text("We meet C2, C4, C5, C9 and C10 and also F13, F22, F23.\n")
    r = intake.rubric_ids(src)
    assert r["revised_against_rubric"] is True and r["files"] == ["notes.md"]
    assert r["criteria"] == ["C2", "C4", "C5", "C9", "C10"]


# ---------------------------------------------------------------- docs

def test_html_conversion():
    text = intake.html_to_text((ROOT / "tests" / "fixtures" / "page.html").read_text())
    assert "<<h1 Tiny docs>>" in text and "<<h2 Install>>" in text
    assert "Step one" in text and "plan | writes plan.md" in text
    assert "SCRIPT-TEXT" not in text and "FOOTER-TEXT" not in text and "Home | Docs" not in text


def test_docs_intake(tmp_path):
    new_run("docs", type_="docs")
    page = tmp_path / "page.html"
    shutil.copy(ROOT / "tests" / "fixtures" / "page.html", page)
    md = tmp_path / "guide.md"
    md.write_text("# Guide\n\ntext\n")
    request({"mode": "docs", "source": [str(page), str(md)], "slug": "tiny"})
    rec = intake.intake(RID, REQ)
    assert rec["root"] == "docs:" and rec["private"] is True and len(rec["docs"]) == 2
    assert "<<h1 Guide>>" in (rd() / "docs" / "text" / "guide.md.txt").read_text()


def test_pdf_without_pdftotext_asks_for_text(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF-1.4\n")
    with pytest.raises(IntakeError) as e:
        intake.convert(f)
    assert e.value.code == 3


# ---------------------------------------------------------------- git mode (#79, #89)

def test_git_offline_exit_6(monkeypatch):
    new_run("git")
    request({"mode": "git", "source": "https://example.invalid/x.git", "slug": "tiny"})
    monkeypatch.setenv("AMA_OFFLINE", "1")
    with pytest.raises(IntakeError) as e:
        intake.intake(RID, REQ)
    assert e.value.code == 6


def test_git_credential_url_exit_2():
    new_run("git")
    request({"mode": "git", "source": "https://u:t" + "@" + "example.invalid/x.git", "slug": "tiny"})
    with pytest.raises(IntakeError) as e:
        intake.intake(RID, REQ)
    assert e.value.code == 2


STUB = """import sys, time
mode, total = sys.argv[1], float(sys.argv[2])
t0 = time.time()
if mode == "stall":
    sys.stderr.write("Cloning...\\n"); sys.stderr.flush(); time.sleep(total); sys.exit(0)
while time.time() - t0 < total:
    sys.stderr.write("Receiving objects: 10%\\r"); sys.stderr.flush(); time.sleep(0.2)
sys.exit(0)
"""


def test_stall_watch_keeps_progress_and_aborts_stall(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text(STUB)
    t0 = time.monotonic()
    rc, _ = intake.run_with_stall([sys.executable, str(stub), "progress", "2.5"], stall=1.0)
    assert rc == 0 and time.monotonic() - t0 >= 2.4          # ran past the stall window, not killed
    t0 = time.monotonic()
    with pytest.raises(intake.Stalled):
        intake.run_with_stall([sys.executable, str(stub), "stall", "30"], stall=1.0)
    assert time.monotonic() - t0 < 10


class _Auth(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="x"')
        self.end_headers()

    def log_message(self, *a):
        pass


@pytest.mark.network_local
@pytest.mark.skipif(shutil.which("git") is None or sys.platform.startswith("win"), reason="needs git on POSIX")
def test_git_auth_required_fails_fast_exit_3(monkeypatch, tmp_path):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Auth)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("AMA_GIT_STALL_SECONDS", "20")
    try:
        new_run("git")
        request({"mode": "git", "source": f"http://127.0.0.1:{srv.server_address[1]}/x.git", "slug": "tiny"})
        t0 = time.monotonic()
        with pytest.raises(IntakeError) as e:
            intake.intake(RID, REQ)
        assert e.value.code == 3 and "ls-remote" in str(e.value)
        assert time.monotonic() - t0 < 15
    finally:
        srv.shutdown()


# ---------------------------------------------------------------- isolate, inventory, shuffle, estimate

def test_isolate(tmp_path):
    new_run()
    state.init("20261126-090000-other", "folder", "other")
    src = copy_tiny(tmp_path)
    (src / "docs" / "scoring").mkdir(parents=True)
    (src / "docs" / "scoring" / "scorecard.md").write_text("x\n")
    folder_intake(src)
    lines = intake.isolate(RID)
    assert (rd() / "sealed" / "S1").is_dir() and (rd() / "sealed" / "S2").is_dir()
    assert "target:docs/scoring/scorecard.md" in lines and "run:20261126-090000-other/" in lines
    assert (rd() / "audit_seed").read_text().strip() == str(state.load(RID)["audit_seed"])


def test_inventory_word_counts():
    inv = intake.inventory(TINY)
    by = {f["path"]: f["words"] for f in inv["files"]}
    text = (TINY / "README.md").read_text()
    assert by["README.md"] == len(text.split()) and inv["total_files"] == 4


def test_shuffle_deterministic_and_distinct():
    a = intake.shuffle("20261127-S1")
    assert a == intake.shuffle("20261127-S1") and sorted(a, key=lambda c: int(c[1:])) == [f"C{i}" for i in range(1, 17)]
    assert a != intake.shuffle("20261127-S2")
    r = subprocess.run([sys.executable, "-m", "engine", "shuffle", "--seed", "20261127-S1"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.stdout.split() == a


def test_estimate_prints_ranges():
    r = subprocess.run([sys.executable, "-m", "engine", "estimate", "--source", str(TINY)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0 and "hypothesis" in r.stdout and "sessions 11-13" in r.stdout


def test_estimate_request_deleted_and_refused_after_s01(tmp_path):
    new_run()
    p = request({"mode": "folder", "source": str(copy_tiny(tmp_path))})
    r = subprocess.run([sys.executable, "-m", "engine", "estimate", "--run", RID, "--request", REQ], cwd=ROOT,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    assert not p.exists()
