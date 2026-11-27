# Changelog

All notable changes to this project are recorded here. The version authority is `.claude-plugin/plugin.json`.

## [Unreleased]

### Added
- Repository skeleton: plugin manifest, marketplace file, project settings, pinned development and tokenizer requirements.
- Engine CLI skeleton, methodology constants and the CI matrix.
- Leak gate: `engine leakcheck` (denylist, built-in patterns, CC BY-SA detectors, git-history and pre-push modes), `engine hooks install`, `.githooks/pre-push`, and a CI leak job.
- Frozen methodology v1.0, evaluator v1.0 and rubric v2.0 (Portuguese original) with `methodology/FREEZE.md` and `engine verify-freeze`.
- English translation of rubric v2.0 (non-normative), reviewed section by section by a second reviewer.
- Rulings v1 (common yardstick) and protocol v1 (process addenda, interpretations I-1 and I-2), frozen at creation.
- Reference registry (`references/registry.yaml`: 9 benchmarks, 2 additional references, 3 variants), strict mini-YAML parser and `engine validate registry`.
- Reference baseline round `2026-11` for the 9 benchmark methods: reconciled L1 vectors with scorer pairs, scorecard machine blocks, post-audit lenses, lens audits and uniform-ruler divergences, with `MANIFEST.json` and `engine baseline verify`. Analyses, tokens and derived results follow (see `TODO.md`).
- `engine/stats.py` (plan §7.3) and `engine/paths.assert_portable`.
- Phase 2 engine, part 1: `paths` (portable `cache:`/`target:`/`run:`/`docs:` resolution, `$AMA_HOME` outside the project, the shared resolver in `hooks/amahome.py`), `validate` with 13 JSON schemas, the full `stats` golden suite, `state` (stages per mode, gates and bounded retry, guard marker, engine-owned logs, TTY-only privileged commands, `baseline promote`, adjudication request/import), `fetch`, `intake`/`isolate`/`inventory`/`shuffle`/`estimate`, `scorecard`, `reconcile`, `calibration`, `alpha`, `audit-scope`, `apply-audit` and `tokens`.
- Baseline round `2026-11`: `tokens.json` recomputed at the pins (31 of 32 values equal Appendix A.4; the difference is explained in `MANIFEST.json`), and the citation check of Pre-step A.
- Phase 2 engine, part 2: `consolidate` (results per round, U rule, design-only and documentation-only entries), `rank`, `sensitivity` (methodology samplers, per-target verdict set), `superiority` (strict and literal interpretations), `ranges`, `lineage`, `fitgap`, `leakcheck --run` and `--public`, the no-network test, and the full `baseline promote`.
- Baseline round `2026-11`: `derived/results.json`, `ranking.json` and `sensitivity.json` (seed 20261127), listed in `MANIFEST.json`.
- Phase 3 report engine: `svg` (Harvey balls, ±U band), `themes/neutral.css` with the theme validator and WCAG contrast test, the Markdown converter, the shared report model, `engine report` (HTML and Markdown, `--run`, `--baseline-only`, `--from`), `selfcheck`, and the report-run fixture.
- Golden report files `tests/golden/report.html` and `report.md` generated from `tests/fixtures/report-run/` (`--date 2026-01-01`, neutral theme) and eye-checked at desktop width in light mode by the implementing agent; owner review pending (see `TODO.md`).
- Sample baseline-only report in `docs/report/index.html` and `report.md` (round 2026-11, date-base 2026-11-27), kept in sync by `tests/test_report_sample.py`. Print CSS expands `<details>` and fits wide tables; the golden files were regenerated for it.
