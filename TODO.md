# TODO

Open items recorded during the build. Each line says what is missing and why.

## v0.2

Deliberately left out of v0.1.0. The phase sections below keep the detail of each item.

- [ ] **Live-session checks** in an interactive Claude Code session: spike 0.3 (every LIVE row of `docs/spikes/hooks.md`), the guard (exit 2 blocks, hook variables expand, also on Windows), `engine setup` (no prompts, reload rule), the plugin path (spike row 8: `/analyze` and the 14 agents from the marketplace), and exit gate P4 (a fresh clone shows the menu on `/analyze`).
- [ ] **`AGENTS.md` walkthrough on a non-Claude host** (Task 5.1 manual check, exit gate P5): up to S06 on the tiny fixture, recorded.
- [ ] **Task 5.3, CI offline job:** `fetch --all --docs --tokenizer`, then `AMA_OFFLINE=1 python -m pytest -q -m "not network_local"`. Not in `ci.yml` yet.
- [ ] **Phase 6, real scoring runs (Tasks 6.1–6.8):** golden files on CI (A1), re-score one reference end to end within its ±U (A2, which also fills the "Reproduction (A2) for 0.1" line of `CHANGELOG.md`), a documentation-only sample (A3), score GSD (A4) and Ralph (A5) with the full pipeline, a comparative report with both plus a fit-gap (A6), CI, leak and claim review (A7), and a clean-machine run on another OS (A8).
- [ ] **Slide deck (Phase 3b, Task 7.5):** `engine slides` (§8.8). Until it ships, compare and fit-gap runs stop at S16b and cannot close.
- [ ] **Task 7.3:** promote GSD and Ralph into `baseline/` as additional references (`benchmark: false`).
- [ ] **Task 7.4:** rebuild the shipped report `docs/report/index.html` with the promoted references.
- [ ] **Task 7.6, release and visibility:** decide on `docs/plans/` (D12), run `leakcheck --git-history --ccbysa` over every ref, rewrite history if needed, then tag and write the release notes.
- [ ] **Unbuilt engine subcommands:** `report --public` and `--copy-to`, `read`, `list`, `convert`, `git-log`, `git-show`, `git-ls`, `build-plugin`.
- [ ] **Owner reviews** listed below (README and shipped report approval for exit gate P7, Pass B strings, tie-break key, `U_recorded` of a promoted reference, token readings, guard residual risks).
- [ ] **GitHub private vulnerability reporting** is off on the repository; `SECURITY.md` points to it. The owner enables it in the repository settings.

## Phase 2

- [x] **`hooks/amahome.py`** is the single project and data-directory resolver (#61), loaded by file path by `engine/paths.py` and `hooks/guard.py`; `tests/test_amahome_parity.py` covers it.
- [x] **`baseline promote`** implements the refusals (TTY, closed reference run, round, pin, CHANGELOG line) and writes `lenses/<slug>.json`, `audits/<slug>.json` (from `lens-audit.json`), the `l1.json` row (final vector, the two active instances' pre-reconciliation pairs, `u`, scorer ids), the `tokens.json` row, and recomputes `derived/` (keeping its seed and draws), then refreshes `MANIFEST.json`.
- [ ] **Owner review: `U_recorded` of a promoted reference.** The plan does not say what `U_recorded` becomes when a reference is re-scored and promoted. The engine records its own U, `total_u(u, baseline)` with `u` from the run's pre-reconciliation pairs and confidences, and writes the source run id into the row. Confirm, or keep the reference round's recorded value.
- [ ] **`estimate` coefficients** are uncalibrated hypotheses until Phase 6.

- [ ] **Owner review: tie-break key under equal weights.** Plan §7.10 and §7.12 say the tied leader with the larger U gives the stricter margin, and the §7.12 code keys on `U[profile]` from results.json. The plan's golden text expects agile-v under `equal` "(larger U 3.6)", but 3.6 is agile-v's recorded U, which §7.6 applies to `U.baseline` only. Under the §7.6 U rule, `U.equal` is 4.0 for ai-dlc and 3.3 for agile-v, so `rank` and `superiority` pick **ai-dlc** as B(equal). The engine follows the code and the stricter-margin rule; the tests assert that. Confirm, or switch both modules to key on `U.baseline`.

## Phase 3 (report engine, v0.1)

- [ ] **Phase 3b, slide deck (`engine slides`, plan §8.8): deferred to v0.2.** Not built in v0.1; `slides` still exits 2 "not implemented".
- [ ] **Owner visual review of the baseline-only report** (exit gate P3): desktop, phone width and print preview, recorded in `docs/reviews/report-v0.1.md`. The implementing agent only eye-checked it in headless Chrome (desktop light and dark, print to PDF); headless Chrome cannot go below 500 px, so phone width is unchecked.
- [ ] **`engine report --public` and `--copy-to <dir>`** (§4.4 rule 5, #67) are not built; they belong with the Phase 4 guard work.
- [ ] **Profiles: "one-line why from the analysis"** and strengths/weaknesses/who-it-is-for prose need `baseline/analyses/` (D2, still pending). Profiles show tables only; lens and audit free text is deliberately not rendered (CC BY-SA and leak safety).
- [ ] **Robustness: the calibration-aligned reading** (§8.2 item 9, from `divergences.json`) is not rendered yet.
- [ ] **Baseline-only narrative:** with no report-builder sections, the lead and key messages are fixed sentences built from the numbers. Review their wording with the owner.
- [ ] **Theme validator location:** it lives in `engine/theme.py` (imported by `report_html.py`), not inside `report_html.py` as §8.4 says.

## Phase 0

- [ ] **Spike 0.3, live checks.** `docs/spikes/hooks.md` lists every row marked LIVE (hook input fields in main session and subagent, exit-2 blocking, `$CLAUDE_PROJECT_DIR`, plugin component paths, additional-directory reload, hostile nested instructions (a) and (b), session-model resume). They need an interactive Claude Code session and were not run in the unattended build. Task 4.2 is built in **mode (b)** (global rules, no agent-identity sealing) and tested with stdin fixtures only; live confirmation is pending: exit 2 blocks, `$CLAUDE_PROJECT_DIR` and `${CLAUDE_PLUGIN_ROOT}` expand in the hook commands (also on Windows, where `python3` may be missing), matcher `*` covers every tool, and the neutral-tool allowlist in `guard.py` (`Task`, `Agent`, `TodoWrite`, `Skill`, …) matches the host's tool names.
- [ ] **Owner review: guard residual risks.** (1) A hook process that fails to start (for example `python3` not on PATH) is a non-blocking error in the host, so the guard fails open; only a guard that runs can fail closed. (2) Under `python -m`, `sys.path[0]` is the cwd, so `PYTHONPATH` = plugin root alone does not stop a hostile `engine/` package in the cwd; the guard pins the cwd to the project root (or `$CLAUDE_PROJECT_DIR`) and outside `$AMA_HOME`, which may conflict with plugin users whose cwd is elsewhere. (3) `engine/__main__.py`'s self-location check (exit 4, a misconfiguration check only) is not built yet.
- [x] **CI fetch of the CC BY-SA corpus.** The `leakcheck` CI job now runs `python -m engine fetch --slug agile-v` into `$AMA_HOME` (Task 2.5).
- [x] **`leakcheck --run` and `--public`.** Wired in Task 2.17: `--run` scans a run's outputs (`run:`) and its report folder (`report:`), skipping the private snapshot (`target/`, `docs/`); `--public` adds the slugs and names of other runs' non-reference targets as `private#<n>` ids. The report reviewer (Task 4.x) and the report stages (Phase 3) still have to call them.

## History on `main` (for the pre-release full-history scan, Task 7.6)

- The plan file as first committed on `main` contains one placeholder absolute path in a test example (`builtin:home-path`, an illustrative single-letter user, not a real path). It is fixed on `build/v0.1`. `leakcheck --git-history` will still report it on the old blob; decide at Task 7.6 whether to accept it or rewrite history.
- [ ] **Registry: V-GSD check** (numbering reset or divergence between `gsd-legacy` and `gsd`) is recorded as pending in `notes:`; it runs in Task 6.4.

## Task 1.6 (baseline round 2026-11): shipped partially

Shipped and gated (leakcheck with owner denylist, `--ccbysa`, portable-path and Appendix A tests): `l1.json`, `scorecards/`, `lenses/`, `audits/`, `divergences.json`, `MANIFEST.json`, `baseline/current`.

- [ ] **`analyses/<slug>.md` (D2): follow-up.** The dense English rewrite of the nine analyses (sections 1–10 and the audit log, private-comparison section dropped, no CC BY-SA text for agile-v) did not fit in this batch. When it ships it must pass the same neutralization, Pass C claim check, `leakcheck --denylist` and `leakcheck --ccbysa` gates.
- [x] **`tokens.json`:** recomputed by `engine tokens --baseline` at the pins. 31 of 32 open-slug values equal Appendix A.4; mattpocock T0 is lower by exactly 1,039 tokens because the reference round followed the `AGENTS.md -> CLAUDE.md` symlink, which this engine never follows (§7.5). Explained in `MANIFEST.json` `notes.tokens`.
- [ ] **Owner review of two token readings** used to reproduce A.4: (1) T0 walks the whole method root (`cache:<slug>`), not the lens `T0_root` (that reading would miss bmad and spec-kit by large margins); (2) dependency lockfiles (`package-lock.json`, `npm-shrinkwrap.json`, `pnpm-lock.yaml`, `yarn.lock`) are skipped, a rule not listed in plan §7.8. Also confirm `shipped_root: "skills/"` for bmad in the registry (other slugs stay null; it changes none of their counts).
- [ ] **Pre-step A (tree diff at pin): partial.** `engine fetch --all` ran (all pins verified). The pass-rule citation check is done: every `cache:` path cited in `lenses/` and `audits/` exists at the pin for all 9 slugs (`MANIFEST.json` `notes.tree_diff.citation_check`). **Blocked:** the added/removed/changed lists against the prototype snapshot need the prototype, which this build does not have. The maintainer runs that diff and fills `notes.tree_diff[<slug>]`; any cited file that changed goes to the lens auditor (Task 6.2).
- [x] **`derived/{results,ranking,sensitivity}.json`:** shipped and listed in `MANIFEST.json` (Tasks 2.10–2.12); sensitivity uses seed 20261127 and 10,000 draws per sampler.
- [ ] **Human review of Pass B strings (100%).** The plan requires a person to review every string the owner's denylist flagged. In the unattended build, an agent rewrote 8 strings and translated 1; none was emptied. IDs: `ai-dlc|audit/log/3/reason`, `ai-dlc|lens/L5/T3/29/why`, `kiro|audit/log/2/evidence`, `kiro|audit/log/2/reason`, `openspec|audit/log/0/reason`, `openspec|audit/log/1/reason`, `openspec|audit/log/2/reason`, `superpowers|audit/log/0/reason`, `superpowers|audit/log/1/reason` (file `audits/<slug>.json` or `lenses/<slug>.json`, JSON path after the slash). The 20% spot check of unflagged strings is also pending.
- [ ] **Divergences for ai-dlc:** C15's uniform reading is "not stated" in the source analysis; confirm or fill it during the A2 reproduction check.

## Phase 4

- [ ] **`engine setup`, live check.** The allow-rule syntax (`Read(//<abs>/runs/**)`, `Edit(…)`, `Write(…)`, `Bash(<python> -m engine *)`) and the Windows form of an absolute rule path are from the host documentation, not a live session. Confirm that a fresh session with the written `.claude/settings.local.json` reads and writes `$AMA_HOME` without prompts, and whether a reload is needed (spike row 9).
- [ ] **Plugin path, live check (spike row 8).** `plugin.json` points `agents` and `skills` at `./.claude/agents/` and `./.claude/skills/`, so the plugin reuses the one copy (`tests/test_plugin_sync.py`). Confirm once that installing from the marketplace shows `/analyze` and the 14 agents. If the host rejects directory component paths, build `engine build-plugin` (copy into `dist/plugin/`) and switch the sync test to byte-compare the copy.
- [ ] **Exit gate P4, live checks.** A fresh clone opened in Claude Code shows the menu on `/analyze` with no install step; the marketplace path shows it too. Not run in the unattended build.
- [ ] **Engine subcommands still unbuilt:** `read`, `list`, `convert`, `git-log`, `git-show`, `git-ls`, `build-plugin` are registered but exit 2. The briefs therefore use the host Read, Glob and Grep tools and `engine inventory`, and the guard denies direct `git`, `find`, `ls` and `pdftotext`. `report` and `slides` come from the report branch.
- [ ] **Guard replay, remaining coverage.** The replay is inline in `tests/test_dry_run.py` (one assessment run, S00–S14, zero denials); there is no `tests/fixtures/tiny-run/tool-calls.jsonl` yet. Not covered: the compare and fit-gap runs (they need `report` and `slides` from the report branch), the G2, G4, G5 and G7 gate paths (#84), and a literal hostile snapshot that ships its own `engine/` package (the guard test covers the `PYTHONPATH` form only).
- [ ] **Owner review: plugin-mode prompts.** In plugin mode, engine calls carry the `PYTHONPATH=<plugin root>` prefix, which does not match the `Bash(<python> -m engine *)` allow rule that `setup` writes, so each call may prompt. This follows the plan as written.
