# CLAUDE.md

Rules for agents and people working **on** this repository. The tool's own runtime instructions live in `AGENTS.md` and `.claude/`.

## Leak gate (mandatory)

- Run `python -m engine hooks install` once after cloning. It sets `core.hooksPath=.githooks`, so every push runs the leak scan. Never bypass it (`--no-verify` is forbidden).
- Keep your own denylist in `.leakcheck/denylist.txt` (git-ignored, never committed). The syntax is in `.leakcheck/denylist.example.txt`. The maintainer clone runs `hooks install --maintainer`, which refuses pushes when that file is missing.
- Before every commit, run `python -m engine leakcheck --path . --denylist .leakcheck/denylist.txt`. It prints only index-based ids (`deny#<n>`, `builtin:<name>`); never paste denylist terms into issues, logs or commit messages.
- CI runs the full scan with the `LEAK_DENYLIST` secret on pushes and on pull requests from this repository. **Pull requests from forks receive no secrets**: there the denylist step is skipped with a notice, while built-in patterns and the CC BY-SA scan still run. The maintainer runs the denylist scan locally before merging a fork pull request. `pull_request_target` is never used to expose the secret.

## Content rules

- All repository content is in English, except the frozen Portuguese rubric original.
- Never write outside the repository while working on it. The tool's runs, reports and cache live in `$AMA_HOME`, never in the clone.
- No absolute home paths, emails, credentials, or names of private methods, companies or clients in any file, fixture or commit message.
- Frozen files under `methodology/` never change; `python -m engine verify-freeze` must pass.
- Agile V is CC BY-SA 4.0: cite its paths only, never paste its text (`leakcheck --ccbysa`).

## Development

- Python >= 3.10, stdlib only for `engine/`. Tests: `python -m pytest -q`.
- Commit after every task with a conventional message.
- The version authority is `.claude-plugin/plugin.json`; `pyproject.toml` and the top `CHANGELOG.md` release must match it (`tests/test_skeleton.py`). Never set `version` in `marketplace.json`.
- Every change to a brief (`.claude/agents/`, `.claude/skills/`), a rule (`rules/`) or `AGENTS.md` gets a `CHANGELOG.md` line.
