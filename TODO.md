# TODO

Open items recorded during the build. Each line says what is missing and why.

## Phase 0

- [ ] **Spike 0.3, live checks.** `docs/spikes/hooks.md` lists every row marked LIVE (hook input fields in main session and subagent, exit-2 blocking, `$CLAUDE_PROJECT_DIR`, plugin component paths, additional-directory reload, hostile nested instructions (a) and (b), session-model resume). They need an interactive Claude Code session and were not run in the unattended build. Blocks Task 4.2.
- [ ] **CI fetch of the CC BY-SA corpus.** The `leakcheck` CI job clones Agile V with raw git at its pin. Replace it with `python -m engine fetch --slug agile-v` once `fetch` exists (Task 2.x).
- [ ] **`leakcheck --run` and `--public`.** Need the run layer (`engine/paths.py`, `state.json`); not built in Phase 1.

## History on `main` (for the pre-release full-history scan, Task 7.6)

- The plan file as first committed on `main` contains one placeholder absolute path in a test example (`builtin:home-path`, an illustrative single-letter user, not a real path). It is fixed on `build/v0.1`. `leakcheck --git-history` will still report it on the old blob; decide at Task 7.6 whether to accept it or rewrite history.
- [ ] **Registry: V-GSD check** (numbering reset or divergence between `gsd-legacy` and `gsd`) is recorded as pending in `notes:`; it runs in Task 6.4.

## Task 1.6 (baseline round 2026-11): shipped partially

Shipped and gated (leakcheck with owner denylist, `--ccbysa`, portable-path and Appendix A tests): `l1.json`, `scorecards/`, `lenses/`, `audits/`, `divergences.json`, `MANIFEST.json`, `baseline/current`.

- [ ] **`analyses/<slug>.md` (D2): follow-up.** The dense English rewrite of the nine analyses (sections 1–10 and the audit log, private-comparison section dropped, no CC BY-SA text for agile-v) did not fit in this batch. When it ships it must pass the same neutralization, Pass C claim check, `leakcheck --denylist` and `leakcheck --ccbysa` gates.
- [ ] **`tokens.json`:** recomputed by `engine tokens --baseline` (Phase 2, needs `fetch` and `tokens`). Must equal Appendix A.4 for the 8 open slugs.
- [ ] **Pre-step A (tree diff at pin):** needs `engine fetch --all`; results go to `MANIFEST.json` `notes.tree_diff`.
- [ ] **`derived/{results,ranking,sensitivity}.json`:** computed by the engine in Phase 2.
- [ ] **Human review of Pass B strings (100%).** The plan requires a person to review every string the owner's denylist flagged. In the unattended build, an agent rewrote 8 strings and translated 1; none was emptied. IDs: `ai-dlc|audit/log/3/reason`, `ai-dlc|lens/L5/T3/29/why`, `kiro|audit/log/2/evidence`, `kiro|audit/log/2/reason`, `openspec|audit/log/0/reason`, `openspec|audit/log/1/reason`, `openspec|audit/log/2/reason`, `superpowers|audit/log/0/reason`, `superpowers|audit/log/1/reason` (file `audits/<slug>.json` or `lenses/<slug>.json`, JSON path after the slash). The 20% spot check of unflagged strings is also pending.
- [ ] **Divergences for ai-dlc:** C15's uniform reading is "not stated" in the source analysis; confirm or fill it during the A2 reproduction check.
