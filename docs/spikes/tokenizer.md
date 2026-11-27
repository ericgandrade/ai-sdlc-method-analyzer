# Spike 0.4: offline tokenizer

**Status: done.** Date 2026-11-27, Python 3.15 on macOS, `tiktoken==0.14.0` from `requirements-tokens.txt`.

## Steps and results

1. `pip install -r requirements-tokens.txt`: installed `tiktoken 0.14.0`.
2. Prime the cache: `TIKTOKEN_CACHE_DIR=.cache/tiktoken python -c "import tiktoken; tiktoken.get_encoding('o200k_base')"`. tiktoken downloaded its BPE file on first use.
3. Offline repeat. The network was not physically disconnected. Instead, `socket.socket`, `socket.create_connection` and `socket.getaddrinfo` were replaced in-process by functions that raise, **before** `import tiktoken`. With the same `TIKTOKEN_CACHE_DIR`, `get_encoding('o200k_base')` worked and `"Hello, world!"` gave **4 tokens**.
4. Control: with the same socket block and an **empty** cache directory, `get_encoding` raised. So the cache is required, and step 2 (`engine fetch --tokenizer`) is the priming step.

## Cache file

| Item | Value |
|---|---|
| Cache directory | `.cache/tiktoken/` (`$AMA_HOME/cache/tiktoken/` once `engine/paths.py` exists) |
| File name | `fb374d419588a4632f3f557e76b4b70aebbca790` (tiktoken names it by the SHA-1 of the source URL) |
| Size | 3,613,922 bytes |
| SHA-256 | `446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d` |

## Consequences for the engine

- `engine fetch --tokenizer` sets `TIKTOKEN_CACHE_DIR` and calls `get_encoding("o200k_base")` once.
- `engine tokens` sets the same variable before importing tiktoken, so it never needs the network after priming.
- `tests/test_tokens_tokenizer.py` checks the 4-token result when tiktoken is installed and skips otherwise. The CI `tokens` job runs it with network access.
