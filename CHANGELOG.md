# Changelog

All notable changes to this project are recorded here. The version authority is `.claude-plugin/plugin.json`.

## [Unreleased]

### Added
- Repository skeleton: plugin manifest, marketplace file, project settings, pinned development and tokenizer requirements.
- Engine CLI skeleton, methodology constants and the CI matrix.
- Leak gate: `engine leakcheck` (denylist, built-in patterns, CC BY-SA detectors, git-history and pre-push modes), `engine hooks install`, `.githooks/pre-push`, and a CI leak job.
