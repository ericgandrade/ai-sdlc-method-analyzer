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
