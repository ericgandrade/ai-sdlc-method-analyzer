"""Tokenizer pin check (plan §7.8, spike 0.4). Skips when tiktoken is not installed."""
import os, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_tokens_o200k_hello_world():
    tiktoken = pytest.importorskip("tiktoken")
    from engine import paths
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(paths.cache_dir() / "tiktoken"))
    enc = tiktoken.get_encoding("o200k_base")
    assert len(enc.encode("Hello, world!")) == 4
