# Third-party notices

This repository is under the MIT licence (`LICENSE`). It **does not vendor or redistribute** any reference method.

## How references are used

- **Fetched at a pin, not redistributed.** `python -m engine fetch` clones each reference at the commit pinned in `references/registry.yaml` into the user's local cache (`$AMA_HOME/cache/`), outside this repository. Documentation pages listed in the registry are downloaded the same way.
- **No text copied.** Scorecards, lenses, audits and reports in this repository (`baseline/`, `docs/report/`) contain scores, short assessment notes and portable citations (`cache:<slug>/<path>` with a line or section). They do not reproduce the references' text.
- **Never executed.** Reference files are read as data; nothing from a reference is run.
- **Agile V (CC BY-SA 4.0) is cited only.** Its paths are cited; its text is never quoted or adapted. `python -m engine leakcheck --ccbysa` checks every commit and CI run for copied passages.

## Reference methods

### Benchmarks (round 2026-11)

| Slug | Method | Source | Licence | Use |
|---|---|---|---|---|
| `ai-dlc` | AWS AI-DLC | https://github.com/awslabs/aidlc-workflows | MIT-0 | fetched at pin; scored and cited |
| `agile-v` | Agile V | https://github.com/Agile-V/agile_v_skills | CC-BY-SA-4.0 | fetched at pin; scored; **cited by path only, never quoted** |
| `bmad` | BMad Method v7 | https://github.com/bmad-code-org/BMAD-METHOD | MIT | fetched at pin; scored and cited |
| `addyosmani` | Addy Osmani agent-skills | https://github.com/addyosmani/agent-skills | MIT | fetched at pin; scored and cited |
| `superpowers` | Superpowers | https://github.com/obra/superpowers | MIT | fetched at pin; scored and cited |
| `kiro` | AWS Kiro | https://github.com/kirodotdev/Kiro and the kiro.dev documentation pages listed in the registry | none (closed product) | documentation snapshot fetched locally; scored from documentation only; cited, never redistributed |
| `mattpocock` | Matt Pocock skills | https://github.com/mattpocock/skills | MIT | fetched at pin; scored and cited |
| `spec-kit` | GitHub Spec Kit | https://github.com/github/spec-kit | MIT | fetched at pin; scored and cited |
| `openspec` | OpenSpec | https://github.com/Fission-AI/OpenSpec | MIT | fetched at pin; scored and cited |

### Additional references (outside the verdict set; not scored in v0.1)

| Slug | Method | Source | Licence | Use |
|---|---|---|---|---|
| `gsd` | GSD Core | https://github.com/open-gsd/gsd-core | MIT | fetched at pin; to be scored (v0.2) |
| `ralph` | Ralph (snarktank) | https://github.com/snarktank/ralph | MIT | fetched at pin; to be scored (v0.2) |

### Variants (registered for lineage and context only)

| Slug | Method | Source | Licence | Use |
|---|---|---|---|---|
| `gsd-legacy` | GSD (legacy repository) | https://github.com/gsd-build/get-shit-done | MIT | candidate; lineage only, not scored |
| `ralph-loop-plugin` | Ralph loop plugin | https://github.com/anthropics/claude-plugins-official (`plugins/ralph-loop`) | Apache-2.0 | lineage only; never scored (its publisher is the vendor of the default scorer model) |
| `ralph-playbook` | How to Ralph Wiggum (playbook) | https://github.com/ghuntley/how-to-ralph-wiggum | none | read-only context; no licence, so never adapted or quoted; not scored |

## Optional dependencies

The engine uses the Python standard library only. These are optional and installed by the user:

| Package | Version | Licence | Use |
|---|---|---|---|
| `tiktoken` | 0.14.0 | MIT | exact token counts (`requirements-tokens.txt`); its `o200k_base` encoding file is downloaded by `engine fetch --tokenizer` |
| `pytest` | 8.3.4 | MIT | the test suite (`requirements-dev.txt`) |
