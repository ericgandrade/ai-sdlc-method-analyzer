# Dry run: menu option 1 on the tiny fixture method (Task 4.8)

- **Date:** 2026-11-27.
- **Executable record:** `tests/test_dry_run.py`. It runs in CI on every push, on the three operating systems.
- **Target:** `tests/fixtures/tiny-method/`, a synthetic method of 7 files: README, three skills (plan as the entry, build, review as the reviewer prompt), one script, one CI file and one spec template. Its scores mean nothing; only the contracts are tested.
- **Data directory:** a fresh temporary `$AMA_HOME` per test run. The run's guard marker never touches a real data folder.

## Result

- Every stage from S00 to S14 is `done`. S07r and S07b are `skipped`: the target is implemented, and the red team left no contest open.
- `state close` succeeds, and it removes the run from the guard marker.
- Every JSON the run produced validates against its schema with `engine validate`'s checker. These are `target`, `calibration`, `reconciled`, `alpha`, `audit_scope`, `redteam`, `lenses`, `lens-audit`, `tokens`, `results` and `state`. `ranking.json`, `sensitivity.json` and `superiority.json` are present; they have no schema file.
- **Guard replay: zero denials.** Each call goes through `hooks/guard.py` before it runs, with the run's marker live. That covers more than 40 Bash calls, all in the single `python3 -m engine …` form, plus every agent Write and Read.

## What ran for real and what was simulated

| Stage | Engine (ran) | Agent (simulated) |
|---|---|---|
| S00 | `verify-freeze` | — |
| S01 | `intake --request` (folder snapshot and pin), `inventory` | intake-pinner: wrote the intake request, `boundary.md` and an empty `off_limits.txt` |
| S02 | `isolate` | — |
| S03 | — | path-tracer: a fixed `trace.md` |
| S04:S1, S04:S2 | `shuffle` | l1-scorer ×2: the `run-min` fixture scorecards. S2 is a copy of S1 with one cell one level lower, so that gate G4 passes |
| S05 | `scorecard check` ×2, `calibration` | — |
| S06 | `reconcile pre`, `alpha` | reconciler: `reconciled.json`, built by applying the pre-computed proposals mechanically |
| S07 | `audit-scope` | red-team-auditor: no changes, no contests, `completed: true` |
| S08a, S08b | — | lens-evaluator: `tests/fixtures/lenses-example.json`, re-rooted to `target:` (L2 null in S08a) |
| S09 | — | lens-auditor: every cell kept, `checked.L4 == 34` |
| S10 | `apply-audit`, `tokens` | — |
| S11 | `consolidate` | — |
| S12 | `rank`, `sensitivity` (200 draws, for speed), `superiority` | — |
| S13 | `lineage` (no reference cache in the temporary data directory) | lineage-detector: a fixed `lineage.md` |
| S14 | — | dense-analyst: a one-section `analysis.md` |
| close | `log append`, `state close` | — |

## What this does not prove

- **No agent ran.** The briefs were not executed by a model, and no subagent was dispatched. The live checks that need an interactive host session stay open in `TODO.md`:
  - that `/analyze` shows the menu;
  - that exit 2 blocks a call;
  - that the hook variables expand.
- The guard was exercised as a function, fed the same JSON a host sends, not as a hook registered in a live session.
- Lineage, calibration and consolidation ran without the reference cache. Calibration and consolidation use the shipped baseline; lineage found nothing to compare.
- Finding: `isolate` rewrites `off_limits.txt`, which S01 recorded, so S02 must be closed with `--outputs off_limits.txt audit_seed`. Otherwise `state next` sees a changed S01 output and resets S01 and everything downstream. The orchestrator skill now says so.
