"""Shared test setup. Every test gets its own $AMA_HOME under tmp_path, so no test
touches the real per-user data directory. Tests marked `needs_cache` read the real
reference cache instead (read-only) and skip when it is absent."""
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _isolated_ama_home(request, tmp_path_factory, monkeypatch):
    if request.node.get_closest_marker("needs_cache"):
        return
    home = tmp_path_factory.mktemp("ama-home")
    monkeypatch.setenv("AMA_HOME", str(home))
    monkeypatch.delenv("AMA_OFFLINE", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
