# Path map

The frozen files (`methodology-v1.0.md`, `evaluator-agent-v1.0.md`, `rubric-v2.0.pt.md`) name paths and shell commands from the workspace where they were written. Those files cannot change, so this map, which is **not frozen**, says what each name means in this repository.

## Paths named inside the frozen files

| Path in the frozen text | Repository path or meaning |
|---|---|
| `docs/research/scoring/methodology.md` | `methodology/methodology-v1.0.md` |
| `anexos/metodologia-v1.0.md` | `methodology/methodology-v1.0.md` (byte-identical copy) |
| `docs/research/scoring/evaluator-agent.md` | `methodology/evaluator-agent-v1.0.md` |
| `docs/research/scoring/scorecards/` | a run's sealed scorer folders, `runs/<run-id>/sealed/<scorer>/`; for the shipped reference round, `baseline/rounds/<round>/scorecards/<slug>/` (machine blocks only) |
| `docs/research/scoring/audit-log.md` | a run's red-team audit, `runs/<run-id>/audit.json`; for the reference round, `baseline/rounds/<round>/audits/<slug>.json` |
| `docs/research/inventory/*.md` | **not shipped.** No mechanism inventories ship with this tool |
| `docs/research/inventory/bmad.md` | **not shipped** (an example inventory named by the evaluator brief) |

## Evidence type I-inv unavailable

Because no mechanism inventory ships, the evidence type **I-inv** (methodology §6.1) and the inventory ID prefixes it uses (`SP-`, `MP-`, `AO-`, `BM-`, `AV-`) are unavailable: **I-inv unavailable**. Scorers cite evidence of type **I, D, S or P** only, and the `INVENTORY` input of the evaluator brief is always empty.

## Shell commands named in the frozen evaluator brief

Agents never call raw tools while a run is active (`rules/injection.md`). Use these portable equivalents:

| Command in the frozen text | Portable equivalent |
|---|---|
| `sha256sum <f>` | `python -m engine verify-freeze --file <f>` (or `--print`) |
| `printf … \| shuf` | `python -m engine shuffle --seed <s>` |
| `find` plus `wc -w` | `python -m engine inventory --root <r>` or `python -m engine list <portable dir>` |
| `git -C <SOURCE> rev-parse HEAD` | `python -m engine git-log <portable root> --rev HEAD -n 1` |

## Methodology §10.4: three weakest criteria relative to the benchmark median

Methodology §10.4 requires every scorecard to list the method's three weakest criteria relative to the benchmark median. Scorers are barred from `baseline/`, so they cannot know the median. The requirement is met after reconciliation instead:
- the engine computes `weakest_vs_median` (plan §7.10) and inserts it into the target's analysis and report profile;
- `engine superiority` refuses to emit a verdict when that block is absent (plan §7.12).
