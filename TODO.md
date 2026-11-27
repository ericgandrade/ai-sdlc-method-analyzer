# TODO

Open items recorded during the build. Each line says what is missing and why.

## Phase 0

- [ ] **Spike 0.3, live checks.** `docs/spikes/hooks.md` lists every row marked LIVE (hook input fields in main session and subagent, exit-2 blocking, `$CLAUDE_PROJECT_DIR`, plugin component paths, additional-directory reload, hostile nested instructions (a) and (b), session-model resume). They need an interactive Claude Code session and were not run in the unattended build. Blocks Task 4.2.
- [ ] **CI fetch of the CC BY-SA corpus.** The `leakcheck` CI job clones Agile V with raw git at its pin. Replace it with `python -m engine fetch --slug agile-v` once `fetch` exists (Task 2.x).
- [ ] **`leakcheck --run` and `--public`.** Need the run layer (`engine/paths.py`, `state.json`); not built in Phase 1.

## History on `main` (for the pre-release full-history scan, Task 7.6)

- The plan file as first committed on `main` contains one placeholder absolute path in a test example (`builtin:home-path`, an illustrative single-letter user, not a real path). It is fixed on `build/v0.1`. `leakcheck --git-history` will still report it on the old blob; decide at Task 7.6 whether to accept it or rewrite history.
