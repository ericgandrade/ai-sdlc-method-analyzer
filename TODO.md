# TODO

Open items recorded during the build. Each line says what is missing and why.

## Phase 2

- [ ] **`hooks/amahome.py`** is the single project and data-directory resolver (#61), loaded by `engine/paths.py` by file path. `hooks/guard.py` (Task 4.2) must load it the same way, and `tests/test_amahome_parity.py` is still to be written.
- [ ] **`baseline promote`** implements the refusals (TTY, closed reference run, round, pin, CHANGELOG line) and writes `lenses/<slug>.json` and the `l1.json` scores, then refreshes `MANIFEST.json`. Pairs, `u`, audits, tokens and derived files are not yet promoted (after Task 2.10).
- [ ] **`estimate` coefficients** are uncalibrated hypotheses until Phase 6.

## Phase 0

- [ ] **Spike 0.3, live checks.** `docs/spikes/hooks.md` lists every row marked LIVE (hook input fields in main session and subagent, exit-2 blocking, `$CLAUDE_PROJECT_DIR`, plugin component paths, additional-directory reload, hostile nested instructions (a) and (b), session-model resume). They need an interactive Claude Code session and were not run in the unattended build. Blocks Task 4.2.
- [x] **CI fetch of the CC BY-SA corpus.** The `leakcheck` CI job now runs `python -m engine fetch --slug agile-v` into `$AMA_HOME` (Task 2.5).
- [ ] **`leakcheck --run` and `--public`.** The run layer (`engine/paths.py`, `engine/state.py`) now exists (Phase 2); wiring these two modes is still open.

## History on `main` (for the pre-release full-history scan, Task 7.6)

- The plan file as first committed on `main` contains one placeholder absolute path in a test example (`builtin:home-path`, an illustrative single-letter user, not a real path). It is fixed on `build/v0.1`. `leakcheck --git-history` will still report it on the old blob; decide at Task 7.6 whether to accept it or rewrite history.
- [ ] **Registry: V-GSD check** (numbering reset or divergence between `gsd-legacy` and `gsd`) is recorded as pending in `notes:`; it runs in Task 6.4.

## Task 1.6 (baseline round 2026-11): shipped partially

Shipped and gated (leakcheck with owner denylist, `--ccbysa`, portable-path and Appendix A tests): `l1.json`, `scorecards/`, `lenses/`, `audits/`, `divergences.json`, `MANIFEST.json`, `baseline/current`.

- [ ] **`analyses/<slug>.md` (D2): follow-up.** The dense English rewrite of the nine analyses (sections 1–10 and the audit log, private-comparison section dropped, no CC BY-SA text for agile-v) did not fit in this batch. When it ships it must pass the same neutralization, Pass C claim check, `leakcheck --denylist` and `leakcheck --ccbysa` gates.
- [x] **`tokens.json`:** recomputed by `engine tokens --baseline` at the pins. 31 of 32 open-slug values equal Appendix A.4; mattpocock T0 is lower by exactly 1,039 tokens because the reference round followed the `AGENTS.md -> CLAUDE.md` symlink, which this engine never follows (§7.5). Explained in `MANIFEST.json` `notes.tokens`.
- [ ] **Owner review of two token readings** used to reproduce A.4: (1) T0 walks the whole method root (`cache:<slug>`), not the lens `T0_root` (that reading would miss bmad and spec-kit by large margins); (2) dependency lockfiles (`package-lock.json`, `npm-shrinkwrap.json`, `pnpm-lock.yaml`, `yarn.lock`) are skipped, a rule not listed in plan §7.8. Also confirm `shipped_root: "skills/"` for bmad in the registry (other slugs stay null; it changes none of their counts).
- [ ] **Pre-step A (tree diff at pin): partial.** `engine fetch --all` ran (all pins verified). The pass-rule citation check is done: every `cache:` path cited in `lenses/` and `audits/` exists at the pin for all 9 slugs (`MANIFEST.json` `notes.tree_diff.citation_check`). **Blocked:** the added/removed/changed lists against the prototype snapshot need the prototype, which this build does not have. The maintainer runs that diff and fills `notes.tree_diff[<slug>]`; any cited file that changed goes to the lens auditor (Task 6.2).
- [ ] **`derived/{results,ranking,sensitivity}.json`:** computed by the engine in Phase 2.
- [ ] **Human review of Pass B strings (100%).** The plan requires a person to review every string the owner's denylist flagged. In the unattended build, an agent rewrote 8 strings and translated 1; none was emptied. IDs: `ai-dlc|audit/log/3/reason`, `ai-dlc|lens/L5/T3/29/why`, `kiro|audit/log/2/evidence`, `kiro|audit/log/2/reason`, `openspec|audit/log/0/reason`, `openspec|audit/log/1/reason`, `openspec|audit/log/2/reason`, `superpowers|audit/log/0/reason`, `superpowers|audit/log/1/reason` (file `audits/<slug>.json` or `lenses/<slug>.json`, JSON path after the slash). The 20% spot check of unflagged strings is also pending.
- [ ] **Divergences for ai-dlc:** C15's uniform reading is "not stated" in the source analysis; confirm or fill it during the A2 reproduction check.
