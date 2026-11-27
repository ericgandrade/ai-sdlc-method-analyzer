"""Portable paths and runtime locations (plan §7.1, §10.1; Task 2.1)."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

from engine import paths
from engine.paths import PathError, assert_portable, portable, resolve

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN = "20261127-101500-tiny"
SRC = "20261126-090000-tiny"


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "ama"
    monkeypatch.setenv("AMA_HOME", str(h))
    return h


def test_cache_resolves_under_refs(home):
    p = resolve("cache:bmad/a/b.md", subpaths={})
    assert p == home / "cache" / "refs" / "bmad" / "a" / "b.md"
    assert portable(p) == "cache:bmad/a/b.md"


def test_cache_uses_registry_when_no_override(home, monkeypatch):
    monkeypatch.chdir(ROOT)
    assert resolve("cache:bmad/a/b.md") == home / "cache" / "refs" / "bmad" / "a" / "b.md"


def test_run_and_source_run_round_trip(home):
    rdir = home / "runs" / RUN
    rdir.mkdir(parents=True)
    (rdir / "state.json").write_text(json.dumps({"sources": [SRC]}))
    p = resolve("run:sealed/S1/target.md", run=RUN)
    assert p == rdir / "sealed" / "S1" / "target.md"
    assert portable(p, run=RUN) == "run:sealed/S1/target.md"
    q = resolve(f"run:{SRC}/results.json", run=RUN)
    assert q == home / "runs" / SRC / "results.json"
    assert portable(q, run=RUN) == f"run:{SRC}/results.json"
    t = resolve("target:skills/x/SKILL.md", run=RUN)
    assert portable(t, run=RUN) == "target:skills/x/SKILL.md"
    d = resolve("docs:guide.pdf#p3", run=RUN)
    assert d == rdir / "docs" / "guide.pdf"
    for s in ("run:sealed/S1/target.md", f"run:{SRC}/results.json", "target:skills/x/SKILL.md"):
        assert_portable({"path": s})


def test_undeclared_source_run_refused(home):
    (home / "runs" / RUN).mkdir(parents=True)
    with pytest.raises(PathError):
        resolve(f"run:{SRC}/results.json", run=RUN)


def test_portable_windows_style_input():
    refs = r"C:\Data\ama\cache\refs"
    assert portable(r"C:\Data\ama\cache\refs\bmad\src\x.md", refs=refs) == "cache:bmad/src/x.md"
    rd = r"C:\Data\ama\runs" + "\\" + RUN
    assert portable(rd + r"\target\a\b.md", run=rd, refs=refs) == "target:a/b.md"
    assert portable("/data/ama/cache/refs/bmad/src/x.md", refs="/data/ama/cache/refs") == "cache:bmad/src/x.md"


def test_portable_outside_every_root_raises(home):
    with pytest.raises(PathError):
        portable(pathlib.Path("/opt/elsewhere/x.md"))


@pytest.mark.parametrize("bad", ["/x", "C:\\x", "~/x", "see /opt/u/x.md:3", "a=(/etc/x)"])
def test_assert_portable_raises(bad):
    with pytest.raises(paths.NotPortable):
        assert_portable({"k": [bad]})


@pytest.mark.parametrize("good", ["https://example.org/a", "cache:bmad/x.md:3", "and/or", "run:a/b"])
def test_assert_portable_passes(good):
    assert_portable({"k": good})


@pytest.mark.parametrize("bad", ["cache:bmad/../x.md", "cache:bmad/a/../../x", "target:../x", "run:../other/x",
                                 "cache:bmad//abs", "target:/abs"])
def test_escapes_refused(home, bad):
    (home / "runs" / RUN).mkdir(parents=True)
    with pytest.raises(PathError):
        resolve(bad, run=RUN, subpaths={})


def test_subpath_confines(home):
    sp = {"plug": "plugins/loop"}
    assert resolve("cache:plug/plugins/loop/README.md", subpaths=sp).name == "README.md"
    with pytest.raises(PathError):
        resolve("cache:plug/other/README.md", subpaths=sp)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="symlinks need privileges on Windows")
def test_symlink_escape_refused(home, tmp_path):
    base = home / "cache" / "refs" / "bmad"
    base.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("x")
    (base / "link.md").symlink_to(outside)
    with pytest.raises(PathError):
        resolve("cache:bmad/link.md", subpaths={})


# ---------------------------------------------------------------- project and data directory

def test_project_resolution(tmp_path):
    plugin = tmp_path / "plugin"
    assert paths.project_root(env={"CLAUDE_PLUGIN_ROOT": str(plugin)}, cwd=tmp_path) == plugin
    assert paths.project_root(env={}, cwd=ROOT) == ROOT
    with pytest.raises(PathError) as e:
        paths.project_root(env={}, cwd=tmp_path)
    assert e.value.code == 3


def test_os_default_data_dirs():
    a = paths.amahome
    mac = a.default_data_dir({"HOME": "/h"}, "darwin")
    assert pathlib.PurePosixPath(mac) == pathlib.PurePosixPath("/h/Library/Application Support/ai-sdlc-method-analyzer")
    lin = a.default_data_dir({"HOME": "/h"}, "linux")
    assert pathlib.PurePosixPath(lin) == pathlib.PurePosixPath("/h/.local/share/ai-sdlc-method-analyzer")
    xdg = a.default_data_dir({"HOME": "/h", "XDG_DATA_HOME": "/x"}, "linux")
    assert pathlib.PurePosixPath(xdg) == pathlib.PurePosixPath("/x/ai-sdlc-method-analyzer")
    win = a.default_data_dir({"LOCALAPPDATA": "C:\\L"}, "win32")
    assert pathlib.PureWindowsPath(win) == pathlib.PureWindowsPath("C:\\L\\ai-sdlc-method-analyzer")


def test_ama_home_inside_project_refused():
    with pytest.raises(PathError) as e:
        paths.data_dir(env={"AMA_HOME": str(ROOT / "data")}, project=ROOT)
    assert e.value.code == 2
    assert paths.data_dir(env={"AMA_HOME": str(ROOT / "data")}, project=ROOT, allow_inside_project=True)


def test_ama_home_override(tmp_path):
    assert paths.data_dir(env={"AMA_HOME": str(tmp_path / "d")}, project=ROOT) == tmp_path / "d"


def test_paths_module_importable_from_subprocess():
    r = subprocess.run([sys.executable, "-c", "from engine import paths; print(paths.amahome.APP)"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.stdout.strip() == "ai-sdlc-method-analyzer"
