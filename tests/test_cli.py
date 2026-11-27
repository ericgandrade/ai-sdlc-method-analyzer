import pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(*a):
    return subprocess.run([sys.executable, "-m", "engine", *a], capture_output=True, text=True, cwd=ROOT)

def test_help():
    assert run("--help").returncode == 0

def test_unknown_command_is_usage_error():
    assert run("frobnicate").returncode == 2

def test_unbuilt_command_exits_2():
    r = run("rank")
    assert r.returncode == 2
    assert "not implemented" in r.stderr
