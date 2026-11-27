"""#61: the guard and the engine resolve the project and data directory through one file."""
import importlib.util
import pathlib

import pytest

from engine import paths

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_parity_guard", ROOT / "hooks" / "guard.py")
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

ENVS = [
    {"HOME": "/h/u"},
    {"HOME": "/h/u", "XDG_DATA_HOME": "/x/d"},
    {"HOME": "/h/u", "AMA_HOME": "/data/ama"},
    {"USERPROFILE": "C:\\Users\\u", "LOCALAPPDATA": "C:\\Users\\u\\AppData\\Local"},
    {"HOME": "/h/u", "CLAUDE_PLUGIN_ROOT": "/plugins/ama"},
]


def test_same_file():
    assert pathlib.Path(guard._load_amahome().__file__).resolve() == pathlib.Path(paths.amahome.__file__).resolve()


@pytest.mark.parametrize("env", ENVS)
@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_same_results(env, platform):
    g = guard._load_amahome()
    assert str(g.data_dir(env, platform)) == str(paths.amahome.data_dir(env, platform))
    assert g.project_root(env, cwd=ROOT) == paths.amahome.project_root(env, cwd=ROOT)
