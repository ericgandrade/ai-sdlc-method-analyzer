<!-- Copy of the evaluator-agent v1.0 §4 output contract (not frozen; the frozen source governs). -->
# Scorecard — <METHOD_NAME>

| Field | Value |
|---|---|
| Method / version | <METHOD_NAME> @ <PIN> |
| Status | implemented / design-only |
| Scorer ID | <SCORER_ID> |
| Methodology version + sha256 | <v> / <hash> |
| Date | <YYYY-MM-DD> |
| Access | full / partial (<what was missing>) |
| Conflict declaration | <none / details> |
| Criterion order used | <randomized list> |

## Default path trace (scenario R)
<5–10 lines; route selected and why>

## Scores
| ID | Criterion | Score (D) | r | RA | Conf | Ev. type | Evidence | Rationale: requirements met per level; first unmet requirement |
|---|---|---|---|---|---|---|---|---|
| C1 | Ease of adoption | | 1.0 | | | | | |
| C2 | Requirements and specification | | 1.0 | | | | | |
| C3 | Code quality practices | | 1.0 | | | | | |
| C4 | Verification and evidence | | 1.0 | | | | | |
| C5 | Code review rigor | | 1.0 | | | | | |
| C6 | Loop engineering | | 1.0 | | | | | |
| C7 | Graph engineering | | 1.0 | | | | | |
| C8 | Autonomous execution safety | | 1.0 | | | | | |
| C9 | Traceability end to end | | 1.0 | | | | | |
| C10 | Human governance | | 1.0 | | | | | |
| C11 | Security by default | | 1.0 | | | | | |
| C12 | Release and operations | | 1.0 | | | | | |
| C13 | Context engineering and token efficiency | | 1.0 | | | | | |
| C14 | Right-sizing and brownfield | | 1.0 | | | | | |
| C15 | Portability and extensibility | | 1.0 | | | | | |
| C16 | Learning loop and measured outcomes | | 1.0 | | | | | |

## Concreteness test (design-only)
| Mechanism | Criterion | Artifact | Trigger | Rule | Output | Failure | Counts? |

## Weakest criteria
## Realization risks (design-only)
## Claims not scored
## Search log
| Criterion | Paths / probe terms | Hits used | Hits rejected (reason) |

## Files read
| Path | Words | Read (full / partial) |

## Machine-readable
```json
{"method":"<slug>","version":"<pin>","status":"implemented|design-only","scorer":"<id>",
 "methodology_sha256":"<hash>",
 "scores":{"C1":{"s":0,"r":1.0,"ra":0,"conf":"H|M|L","ev":"I|I-inv|D|S|P",
   "first_unmet":"<text>","cites":["path#section","SP-12","https://..."]}}}
```
