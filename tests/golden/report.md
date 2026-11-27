# AI development methods: comparative assessment

Date-base **2026-01-01** · Methodology **v1.0 a6e39537** · Rubric **v2.0 8d5b63ea** · Methods **10** · Round **2026-11**

## Overview

**Key message:** A synthetic fixture is compared with the shipped baseline.

This report uses fixed sections and a precomputed sensitivity file so its output is byte-stable.

## Panorama

**Key message:** Fixture Method sits in the technical-tie group under baseline weights.

The synthetic target ranks second; see the ranking below.

- **Methods assessed:** 10
- **Leader (baseline):** AWS AI-DLC 68.6
- **Target:** Fixture Method 68.0
- **Target position:** 2 of 10
- **Technical-tie group:** 4

| # | Method | Role | Total | ± U | Band (0–100) | Reading | Δ vs leader |
|---|---|---|---|---|---|---|---|
| 1 | AWS AI-DLC | benchmark | 68.6 | 3.1 | 68.6 ± 3.1 | leader | 0.0 |
| 2 | Fixture Method | target | 68.0 | 2.6 | 68.0 ± 2.6 | technical-tie | -0.6 |
| 3 | Agile V | benchmark | 67.0 | 3.6 | 67.0 ± 3.6 | technical-tie | -1.6 |
| 4 | BMad Method v7 | benchmark | 66.8 | 2.7 | 66.8 ± 2.7 | technical-tie | -1.8 |
| 5 | Addy Osmani agent-skills | benchmark | 57.6 | 2.9 | 57.6 ± 2.9 | below | -11.0 |
| 6 | Superpowers | benchmark | 56.0 | 2.3 | 56.0 ± 2.3 | below | -12.6 |
| 7 | AWS Kiro | benchmark | 44.4 | 2.7 | 44.4 ± 2.7 | below | -24.2 |
| 8 | Matt Pocock skills | benchmark | 43.8 | 2.8 | 43.8 ± 2.8 | below | -24.8 |
| 9 | GitHub Spec Kit | benchmark | 43.2 | 2.6 | 43.2 ± 2.6 | below | -25.4 |
| 10 | OpenSpec | benchmark | 38.8 | 2.6 | 38.8 ± 2.6 | below | -29.8 |

> **How to read.** Each total is the 0–100 weighted sum of the 16 criteria on scenario R, with baseline weights; the denominator is the full 16-criterion scale, the same for every method. The band runs from T − U to T + U with a tick at T. Two methods differ only when the gap exceeds the margin M = max(5, 2·√(U₁² + U₂²)) (methodology §9); a smaller gap is a technical tie. Role chips mark the 9 frozen benchmarks, additional references (outside verdicts) and targets.

## How we assessed

**Key message:** Sixteen weighted criteria on one scenario, plus four lenses, with every score cited.

Every method is judged on reference scenario R: a team of 3–8 engineers adds a medium-sized feature to an existing production web service, with version control, CI and review before merge, using one supported AI coding agent. A mechanism counts when a user following the main entry point meets it without opting in.

- **L1** scores the 16 criteria from 0 to 5 against anchored scales; the weights below give the 0–100 totals.
- **L2** is the ceiling: the best score any shipped path reaches.
- **L3** is the autonomy level (A0 to A5).
- **L4** checks 34 features in 9 groups (0 absent, 1 opt-in or partial, 2 on the default path).
- **L5** counts the static tokens a method loads (a proxy, not a measured cost).

Evidence must cite a file and line at the pinned commit; roadmaps and claims do not count. Two scorers work blind to each other, a reconciler merges their sheets, a red team contests cells, and Krippendorff's α measures their agreement.

| # | Criterion | Baseline | Equal | Startup | Regulated | Autonomous |
|---|---|---|---|---|---|---|
| C1 | Ease of adoption | 6 | 6.25 | 12 | 3 | 4 |
| C2 | Requirements and specification | 8 | 6.25 | 6 | 10 | 6 |
| C3 | Code quality practices | 9 | 6.25 | 10 | 7 | 7 |
| C4 | Verification and evidence | 9 | 6.25 | 8 | 10 | 9 |
| C5 | Code review rigor | 8 | 6.25 | 6 | 9 | 8 |
| C6 | Loop engineering | 7 | 6.25 | 7 | 5 | 11 |
| C7 | Graph engineering | 4 | 6.25 | 4 | 2 | 9 |
| C8 | Autonomous execution safety | 6 | 6.25 | 8 | 5 | 11 |
| C9 | Traceability end to end | 5 | 6.25 | 2 | 10 | 4 |
| C10 | Human governance | 6 | 6.25 | 2 | 11 | 4 |
| C11 | Security by default | 6 | 6.25 | 4 | 9 | 5 |
| C12 | Release and operations | 6 | 6.25 | 5 | 7 | 4 |
| C13 | Context engineering and token efficiency | 6 | 6.25 | 8 | 3 | 9 |
| C14 | Right-sizing and brownfield | 6 | 6.25 | 10 | 4 | 4 |
| C15 | Portability and extensibility | 4 | 6.25 | 6 | 1 | 3 |
| C16 | Learning loop and measured outcomes | 4 | 6.25 | 2 | 4 | 2 |
|  | Total | 100 | 100 | 100 | 100 | 100 |

| Legend | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Criteria (0–5) | ○ 0 | ◔ 1 | ◑ 2 | ◑⁺ 3 | ◕ 4 | ● 5 |
| Features (0–2) | ○ 0 absent | ◑ 1 opt-in or partial | ● 2 default path |  |  |  |
| Groups (%) | ○ 0–12 | ◔ 13–37 | ◑ 38–62 | ◕ 63–87 | ● 88–100 |  |

## Per-criterion matrix (L1)

**Key message:** No method leads every criterion; the leaders change from criterion to criterion.

*Columns in baseline ranking order. The number sits beside each ball.*

| # | Criterion | Weight | AWS AI-DLC | Fixture Method | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Ease of adoption | 6 | ◑ 2 | ◕ 4 | ◑⁺ 3 | ● 5 | ◑ 2 | ◑ 2 | ◕ 4 | ◑ 2 | ◕ 4 | ◑⁺ 3 |
| C2 | Requirements and specification | 8 | ◕ 4 | ◕ 4 | ◑ 2 | ◕ 4 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ◕ 4 |
| C3 | Code quality practices | 9 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑⁺ 3 | ● 5 | ◕ 4 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 |
| C4 | Verification and evidence | 9 | ● 5 | ◕ 4 | ● 5 | ◕ 4 | ◑⁺ 3 | ◕ 4 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C5 | Code review rigor | 8 | ◕ 4 | ◕ 4 | ◕ 4 | ◕ 4 | ◑⁺ 3 | ◕ 4 | ◑ 2 | ◑ 2 | ◔ 1 | ◑ 2 |
| C6 | Loop engineering | 7 | ◕ 4 | ◑⁺ 3 | ◕ 4 | ◕ 4 | ◑ 2 | ◕ 4 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C7 | Graph engineering | 4 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 |
| C8 | Autonomous execution safety | 6 | ◕ 4 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ○ 0 |
| C9 | Traceability end to end | 5 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◔ 1 |
| C10 | Human governance | 6 | ◑⁺ 3 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C11 | Security by default | 6 | ◑ 2 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◔ 1 | ◑ 2 | ◔ 1 | ◑ 2 | ◔ 1 |
| C12 | Release and operations | 6 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ○ 0 | ◔ 1 | ◔ 1 | ◔ 1 | ◔ 1 |
| C13 | Context engineering and token efficiency | 6 | ● 5 | ◕ 4 | ◕ 4 | ◕ 4 | ● 5 | ● 5 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑ 2 |
| C14 | Right-sizing and brownfield | 6 | ◑⁺ 3 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 |
| C15 | Portability and extensibility | 4 | ◑ 2 | ◕ 4 | ● 5 | ◑ 2 | ◕ 4 | ◕ 4 | ◑ 2 | ◑⁺ 3 | ● 5 | ◑ 2 |
| C16 | Learning loop and measured outcomes | 4 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ○ 0 | ◑ 2 | ◑ 2 | ◑ 2 | ○ 0 | ○ 0 |
|  | Total (baseline) | 100 | 68.6 | 68.0 | 67.0 | 66.8 | 57.6 | 56.0 | 44.4 | 43.8 | 43.2 | 38.8 |

**Who leads each criterion** (benchmark set)

| # | Max | Leaders | Benchmark median | Target |
|---|---|---|---|---|
| C1 | 5 | BMad Method v7 | 3 | Fixture Method 4 |
| C2 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec | 3 | Fixture Method 4 |
| C3 | 5 | Addy Osmani agent-skills | 3 | Fixture Method 4 |
| C4 | 5 | Agile V, AWS AI-DLC | 3 | Fixture Method 4 |
| C5 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers | 3 | Fixture Method 4 |
| C6 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers | 2 | Fixture Method 3 |
| C7 | 3 | Agile V, AWS AI-DLC, BMad Method v7, AWS Kiro | 2 | Fixture Method 3 |
| C8 | 4 | AWS AI-DLC | 2 | Fixture Method 3 |
| C9 | 3 | Agile V, AWS AI-DLC, BMad Method v7 | 2 | Fixture Method 3 |
| C10 | 4 | Agile V | 2 | Fixture Method 3 |
| C11 | 3 | Addy Osmani agent-skills, Agile V | 2 | Fixture Method 3 |
| C12 | 3 | Addy Osmani agent-skills, AWS AI-DLC | 1 | Fixture Method 2 |
| C13 | 5 | Addy Osmani agent-skills, AWS AI-DLC, Superpowers | 4 | Fixture Method 4 |
| C14 | 4 | Agile V | 3 | Fixture Method 3 |
| C15 | 5 | Agile V, GitHub Spec Kit | 3 | Fixture Method 4 |
| C16 | 3 | AWS AI-DLC, BMad Method v7 | 2 | Fixture Method 2 |

## Features (L4)

**Key message:** Feature coverage is uneven across the nine groups; no method covers them all.

*Group cells show the share of the group's points (2 per feature); coverage is over all 34 features.*

| Group | AWS AI-DLC | Fixture Method | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|---|
| Discovery | ● 100% | ◑ 62% | ● 88% | ● 100% | ● 88% | ◑ 62% | ◑ 62% | ◑ 38% | ◕ 75% | ◕ 75% |
| Design | ● 88% | ◑ 50% | ◕ 75% | ● 100% | ● 88% | ◕ 75% | ◑ 62% | ● 88% | ◕ 75% | ◑ 62% |
| Construction | ● 88% | ◑ 38% | ◕ 75% | ◕ 75% | ● 100% | ● 88% | ◑ 50% | ● 88% | ◑ 38% | ○ 0% |
| Verification | ◕ 75% | ◑ 62% | ● 88% | ● 88% | ● 100% | ◑ 62% | ◑ 50% | ◑ 50% | ◔ 25% | ◔ 25% |
| Autonomy | ◕ 70% | ◑ 40% | ◑ 40% | ◑ 60% | ◑ 60% | ◑ 60% | ◕ 70% | ◔ 30% | ◑ 50% | ◔ 30% |
| Governance | ◕ 67% | ◑ 50% | ◕ 67% | ◑ 50% | ◔ 17% | ◔ 17% | ◔ 33% | ◔ 17% | ◑ 50% | ○ 0% |
| Operations | ◕ 75% | ◑ 62% | ◑ 62% | ◕ 75% | ◑ 50% | ○ 12% | ◔ 25% | ◑ 38% | ○ 12% | ◑ 38% |
| Ecosystem | ● 100% | ◑ 50% | ◕ 83% | ◕ 83% | ● 100% | ◕ 83% | ◔ 33% | ◕ 83% | ● 100% | ● 100% |
| Economy | ● 100% | ◑ 50% | ◕ 67% | ◕ 67% | ◕ 67% | ◕ 67% | ◔ 33% | ◔ 33% | ◔ 17% | ◔ 33% |
| Coverage | 84% | 51% | 71% | 78% | 75% | 59% | 49% | 51% | 49% | 40% |

### All 34 features

| # | Feature | AWS AI-DLC | Fixture Method | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | Structured elicitation | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ◑ 1 |
| F2 | Spec template with testable acceptance criteria | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ● 2 | ● 2 |
| F3 | Independent spec critique | ● 2 | ○ 0 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 |
| F4 | Spec change control | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ○ 0 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 |
| F5 | Task decomposition with explicit dependencies | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 |
| F6 | Decision records (ADR) | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ● 2 | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 |
| F7 | Existing-code mapping (brownfield) | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F8 | Routing by size or risk | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ◑ 1 |
| F9 | Test-first | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 |
| F10 | Systematic debugging | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F11 | Role-specialised agents | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ○ 0 | ○ 0 |
| F12 | Subagents with isolated context and brief | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 |
| F13 | Verification gate with fresh command evidence | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F14 | Review by a context independent of the author | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ○ 0 | ◑ 1 |
| F15 | Multiple review lenses with consolidation | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 |
| F16 | Security review or threat modelling | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ○ 0 |
| F17 | Iteration loop with numeric bound and action | ● 2 | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ● 2 | ○ 0 |
| F18 | Multi-session execution without a human between tasks | ○ 0 | ○ 0 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F19 | Execution isolation (branch, worktree, sandbox) | ◑ 1 | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F20 | Persisted state and resume | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ● 2 |
| F21 | Environment-enforced limits (hooks, permissions, sandbox) | ● 2 | ○ 0 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 | ● 2 | ○ 0 | ○ 0 | ○ 0 |
| F22 | Recorded human approvals (who, when, version) | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 |
| F23 | Traceable IDs requirement→task→test | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F24 | Exportable or tool-checked audit trail | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 | ◑ 1 | ○ 0 |
| F25 | Release with rollback | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ◑ 1 |
| F26 | Incident and postmortem | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ○ 0 |
| F27 | Retrospective that changes the environment | ● 2 | ○ 0 | ◑ 1 | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 |
| F28 | Cross-session memory | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ◑ 1 | ● 2 |
| F29 | Official support for 3+ agent platforms | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ● 2 | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 |
| F30 | Versioned installer and update | ● 2 | ○ 0 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 |
| F31 | Automatic validation of the method itself | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ● 2 |
| F32 | Token or cost telemetry | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 |
| F33 | Context or artifact size budget | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ● 2 |
| F34 | Evals that measure the method's behaviour | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 |

## Autonomy × safety (C8) × maturity

**Key message:** Several methods offer more autonomy than their safety controls cover.

| Method | L3 autonomy | C8 safety | L1 (baseline) | Reading |
|---|---|---|---|---|
| AWS AI-DLC | A3 | 4 | 68.6 | orchestrates with partial protection |
| Fixture Method | A3 | 3 | 68.0 | orchestrates with partial protection |
| Agile V | A3 | 2 | 67.0 | autonomy above protection |
| BMad Method v7 | A2 | 3 | 66.8 | assisted |
| Addy Osmani agent-skills | A2 | 2 | 57.6 | assisted |
| Superpowers | A3 | 3 | 56.0 | orchestrates with partial protection |
| AWS Kiro | A3 | 2 | 44.4 | autonomy above protection |
| Matt Pocock skills | A3 | 2 | 43.8 | autonomy above protection |
| GitHub Spec Kit | A2 | 2 | 43.2 | assisted |
| OpenSpec | A1 | 0 | 38.8 | assisted |

> **Autonomy is not quality.** A higher L3 level means the method runs longer without a person; it says nothing about the quality of the result. Read it together with C8, the safety of autonomous execution.

## Tokens (L5)

**Key message:** Static footprints differ by an order of magnitude across methods.

| Method | T1 | T2 | T3 | T0 | Tokenizer |
|---|---|---|---|---|---|
| AWS AI-DLC | 12,342 | 37,720 | 96,496 | 3,185,959 | tiktoken o200k_base |
| Fixture Method | 1,500 | 2,500 | 20,000 | 90,000 | tiktoken o200k_base |
| Agile V | 1,758 | 2,842 | 25,403 | 662,512 | tiktoken o200k_base |
| BMad Method v7 | 1,813 | 2,008 | 41,183 | 515,146 | tiktoken o200k_base |
| Addy Osmani agent-skills | 2,338 | 3,893 | 32,577 | 199,401 | tiktoken o200k_base |
| Superpowers | 1,245 | 3,820 | 16,282 | 226,283 | tiktoken o200k_base |
| AWS Kiro | n/m | n/m | n/m | n/m | tiktoken o200k_base |
| Matt Pocock skills | 575 | 1,278 | 10,562 | 171,389 | tiktoken o200k_base |
| GitHub Spec Kit | 942 | 2,739 | 32,240 | 983,534 | tiktoken o200k_base |
| OpenSpec | 634 | 3,584 | 13,998 | 1,065,039 | tiktoken o200k_base |

> **Proxy.** Static token counts of the files a method ships, not measured runtime cost. T1 is what loads at start, T2 one typical step, T3 the default path for scenario R, T0 the whole method root. n/m means not measurable; approx. means not comparable with the other rows.

## Ranking robustness

**Key message:** AWS AI-DLC is first in 48% of centred weight draws; the lead depends on the weighting.

| Method | Baseline total (rank) | Equal total (rank) | Startup total (rank) | Regulated total (rank) | Autonomous total (rank) |
|---|---|---|---|---|---|
| AWS AI-DLC | 68.6 (1) | 66.2 (1) | 67.4 (4) | 68.4 (1) | 72.0 (1) |
| Fixture Method | 68.0 (2) | 66.2 (1) | 69.8 (1) | 66.4 (2) | 68.0 (2) |
| Agile V | 67.0 (3) | 66.2 (1) | 68.0 (3) | 65.6 (3) | 67.4 (4) |
| BMad Method v7 | 66.8 (4) | 65.0 (4) | 68.8 (2) | 65.2 (4) | 67.8 (3) |
| Addy Osmani agent-skills | 57.6 (5) | 55.0 (5) | 60.2 (5) | 54.6 (5) | 57.2 (6) |
| Superpowers | 56.0 (6) | 53.8 (6) | 58.4 (6) | 51.0 (6) | 60.2 (5) |
| AWS Kiro | 44.4 (7) | 45.0 (7) | 48.2 (7) | 41.6 (7) | 45.2 (7) |
| Matt Pocock skills | 43.8 (8) | 43.8 (8) | 46.6 (9) | 40.4 (8) | 44.6 (8) |
| GitHub Spec Kit | 43.2 (9) | 43.8 (8) | 48.2 (7) | 39.6 (9) | 43.2 (9) |
| OpenSpec | 38.8 (10) | 36.2 (10) | 40.6 (10) | 37.2 (10) | 36.8 (10) |
| Leader | AWS AI-DLC | AWS AI-DLC | Fixture Method | AWS AI-DLC | AWS AI-DLC |

**Superiority test: Fixture Method** (methodology §9)

| Condition | Value | Threshold | Pass |
|---|---|---|---|
| S1 margin (base) | ΔT = -0.6 | M = 8.1 | ✗ |
| S2 per profile | autonomous -4.0 / equal 0.0 / regulated -2.0 / startup 1.0 | M(P) each | ✗ |
| S3 rank-1 prob. | centred ✗ / loo ✗ / score_perturbation ✗ / uniform ✗ | .90/.75/.90; 16/16 | ✗ |
| S4 criteria below median | none | none | ✓ |
| S5 best-in-class count | 5 (core 2) | ≥6 (≥3 core) | ✗ |
| S6 audit | completed | completed | ✓ |
| S7 Krippendorff α | 0.712 | ≥ .667 | ✓ |
| Verdict | Comparable |  |  |

**P(first)** over 200 draws per sampler (seed 20260101).

| Method | Centred | Uniform | Score perturbation | Mean rank (centred) |
|---|---|---|---|---|
| AWS AI-DLC | 0.485 | 0.330 | 0.432 | 1.90 |
| Fixture Method | 0.253 | 0.152 | 0.367 | 2.32 |
| Agile V | 0.175 | 0.355 | 0.122 | 2.83 |
| BMad Method v7 | 0.087 | 0.163 | 0.077 | 2.96 |
| Addy Osmani agent-skills | 0.000 | 0.000 | 0.000 | 5.34 |
| Superpowers | 0.000 | 0.000 | 0.000 | 5.65 |
| AWS Kiro | 0.000 | 0.000 | 0.000 | 7.60 |
| Matt Pocock skills | 0.000 | 0.000 | 0.000 | 8.12 |
| GitHub Spec Kit | 0.000 | 0.000 | 0.000 | 8.45 |
| OpenSpec | 0.000 | 0.000 | 0.000 | 9.82 |

**Tornado** (each weight × 0.5 and × 1.5): methods whose rank moves, and who is first.

| # | Methods moved (max) | First under the change |
|---|---|---|
| C1 | 6 | AWS AI-DLC, Fixture Method |
| C2 | 4 | Agile V, AWS AI-DLC |
| C3 | 4 | AWS AI-DLC, Fixture Method |
| C4 | 4 | AWS AI-DLC, Fixture Method |
| C5 | 2 | AWS AI-DLC |
| C6 | 2 | AWS AI-DLC, Fixture Method |
| C7 | 0 | AWS AI-DLC |
| C8 | 2 | AWS AI-DLC, Fixture Method |
| C9 | 0 | AWS AI-DLC |
| C10 | 2 | AWS AI-DLC |
| C11 | 3 | AWS AI-DLC, Fixture Method |
| C12 | 3 | AWS AI-DLC, Fixture Method |
| C13 | 2 | AWS AI-DLC, Fixture Method |
| C14 | 3 | AWS AI-DLC |
| C15 | 4 | AWS AI-DLC, Fixture Method |
| C16 | 2 | AWS AI-DLC |

**Leave-one-out** (each criterion removed in turn).

| Removed | First |
|---|---|
| C1 | AWS AI-DLC |
| C2 | Agile V |
| C3 | AWS AI-DLC |
| C4 | Fixture Method |
| C5 | AWS AI-DLC |
| C6 | Fixture Method |
| C7 | AWS AI-DLC |
| C8 | Agile V |
| C9 | AWS AI-DLC |
| C10 | AWS AI-DLC |
| C11 | AWS AI-DLC |
| C12 | Fixture Method |
| C13 | Fixture Method |
| C14 | AWS AI-DLC |
| C15 | AWS AI-DLC |
| C16 | Fixture Method |

## Method profiles

**Key message:** Each profile shows the card, the scores and the weakest criteria.

*Open a method to see its card, L1 table, lenses and weakest criteria.*

### AWS AI-DLC (68.6, benchmark)

| Field | Value |
|---|---|
| Name | AWS AI-DLC |
| Origin | AWS (awslabs) |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT-0 |
| Pin | 1c557ea27781 |
| Source | https://github.com/awslabs/aidlc-workflows |

**Key message:** ranks 1 of 10 under baseline weights at 68.6 ± 3.1.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑ 2 | 1.5 |
| C2 | Requirements and specification | ◕ 4 | 0.5 |
| C3 | Code quality practices | ◑⁺ 3 | 0.5 |
| C4 | Verification and evidence | ● 5 | 0.5 |
| C5 | Code review rigor | ◕ 4 | 1 |
| C6 | Loop engineering | ◕ 4 | 0.5 |
| C7 | Graph engineering | ◑⁺ 3 | 1 |
| C8 | Autonomous execution safety | ◕ 4 | 0.5 |
| C9 | Traceability end to end | ◑⁺ 3 | 0.5 |
| C10 | Human governance | ◑⁺ 3 | 0.5 |
| C11 | Security by default | ◑ 2 | 0.5 |
| C12 | Release and operations | ◑⁺ 3 | 1 |
| C13 | Context engineering and token efficiency | ● 5 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◑ 2 | 1.5 |
| C16 | Learning loop and measured outcomes | ◑⁺ 3 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 69.8 |
| L3 autonomy | A3 (confidence M) |
| L4 coverage | 84% |
| L5 T1 tokens | 12,342 |

**Strengths** (at the benchmark best): C2, C4, C5, C6, C7, C8, C9, C12, C13, C16.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C1 | 2 | 3 | 5 | BMad Method v7 |
| C15 | 2 | 3 | 5 | Agile V, GitHub Spec Kit |
| C3 | 3 | 3 | 5 | Addy Osmani agent-skills |

### Fixture Method (68.0, target)

| Field | Value |
|---|---|
| Name | Fixture Method |
| Origin | Synthetic fixture |
| Role | target |
| Type | open |
| Status | implemented |
| Host | Claude Code |

**Key message:** The fixture is strong on core criteria and weak on C12.

**Key message:** ranks 2 of 10 under baseline weights at 68.0 ± 2.6.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◕ 4 | 0.5 |
| C2 | Requirements and specification | ◕ 4 | 0.5 |
| C3 | Code quality practices | ◕ 4 | 0.5 |
| C4 | Verification and evidence | ◕ 4 | 0.5 |
| C5 | Code review rigor | ◕ 4 | 0.5 |
| C6 | Loop engineering | ◑⁺ 3 | 0.5 |
| C7 | Graph engineering | ◑⁺ 3 | 0.5 |
| C8 | Autonomous execution safety | ◑⁺ 3 | 0.5 |
| C9 | Traceability end to end | ◑⁺ 3 | 0.5 |
| C10 | Human governance | ◑⁺ 3 | 0.5 |
| C11 | Security by default | ◑⁺ 3 | 0.5 |
| C12 | Release and operations | ◑ 2 | 0.5 |
| C13 | Context engineering and token efficiency | ◕ 4 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◕ 4 | 0.5 |
| C16 | Learning loop and measured outcomes | ◑ 2 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 68.0 |
| L3 autonomy | A3 (confidence M) |
| L4 coverage | 51% |
| L5 T1 tokens | 1,500 |

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C13 | 4 | 4 | 5 | Addy Osmani agent-skills, AWS AI-DLC, Superpowers |
| C14 | 3 | 3 | 4 | Agile V |
| C16 | 2 | 2 | 3 | AWS AI-DLC, BMad Method v7 |

Who it is for: teams that want a *synthetic* example.

### Agile V (67.0, benchmark)

| Field | Value |
|---|---|
| Name | Agile V |
| Origin | Agile V community (agile-v.org) |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | CC-BY-SA-4.0 |
| Pin | 4bcc9172f7e0 |
| Source | https://github.com/Agile-V/agile_v_skills |

**Key message:** ranks 3 of 10 under baseline weights at 67.0 ± 3.6.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑⁺ 3 | 0.5 |
| C2 | Requirements and specification | ◑ 2 | 1 |
| C3 | Code quality practices | ◑⁺ 3 | 0.5 |
| C4 | Verification and evidence | ● 5 | 1 |
| C5 | Code review rigor | ◕ 4 | 0.5 |
| C6 | Loop engineering | ◕ 4 | 0.5 |
| C7 | Graph engineering | ◑⁺ 3 | 0.5 |
| C8 | Autonomous execution safety | ◑ 2 | 1 |
| C9 | Traceability end to end | ◑⁺ 3 | 0.5 |
| C10 | Human governance | ◕ 4 | 0.5 |
| C11 | Security by default | ◑⁺ 3 | 0.5 |
| C12 | Release and operations | ◑ 2 | 1 |
| C13 | Context engineering and token efficiency | ◕ 4 | 0.5 |
| C14 | Right-sizing and brownfield | ◕ 4 | 0.5 |
| C15 | Portability and extensibility | ● 5 | 0.5 |
| C16 | Learning loop and measured outcomes | ◑ 2 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 73.2 |
| L3 autonomy | A3 (confidence M) |
| L4 coverage | 71% |
| L5 T1 tokens | 1,758 |

**Strengths** (at the benchmark best): C4, C5, C6, C7, C9, C10, C11, C14, C15.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C2 | 2 | 3 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec |
| C3 | 3 | 3 | 5 | Addy Osmani agent-skills |
| C1 | 3 | 3 | 5 | BMad Method v7 |

### BMad Method v7 (66.8, benchmark)

| Field | Value |
|---|---|
| Name | BMad Method v7 |
| Origin | BMad Code, LLC |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT |
| Pin | e435a22574fe |
| Source | https://github.com/bmad-code-org/BMAD-METHOD |

**Key message:** ranks 4 of 10 under baseline weights at 66.8 ± 2.7.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ● 5 | 1 |
| C2 | Requirements and specification | ◕ 4 | 0.5 |
| C3 | Code quality practices | ◑⁺ 3 | 0.5 |
| C4 | Verification and evidence | ◕ 4 | 0.5 |
| C5 | Code review rigor | ◕ 4 | 0.5 |
| C6 | Loop engineering | ◕ 4 | 0.5 |
| C7 | Graph engineering | ◑⁺ 3 | 0.5 |
| C8 | Autonomous execution safety | ◑⁺ 3 | 0.5 |
| C9 | Traceability end to end | ◑⁺ 3 | 0.5 |
| C10 | Human governance | ◑⁺ 3 | 0.5 |
| C11 | Security by default | ◑ 2 | 0.5 |
| C12 | Release and operations | ◑ 2 | 0.5 |
| C13 | Context engineering and token efficiency | ◕ 4 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◑ 2 | 1 |
| C16 | Learning loop and measured outcomes | ◑⁺ 3 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 68.4 |
| L3 autonomy | A2 (confidence H) |
| L4 coverage | 78% |
| L5 T1 tokens | 1,813 |

**Strengths** (at the benchmark best): C1, C2, C5, C6, C7, C9, C16.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C15 | 2 | 3 | 5 | Agile V, GitHub Spec Kit |
| C3 | 3 | 3 | 5 | Addy Osmani agent-skills |
| C11 | 2 | 2 | 3 | Addy Osmani agent-skills, Agile V |

### Addy Osmani agent-skills (57.6, benchmark)

| Field | Value |
|---|---|
| Name | Addy Osmani agent-skills |
| Origin | Addy Osmani (personal project) |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT |
| Pin | 39b723ceebf8 |
| Source | https://github.com/addyosmani/agent-skills |

**Key message:** ranks 5 of 10 under baseline weights at 57.6 ± 2.9.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑ 2 | 0.5 |
| C2 | Requirements and specification | ◑⁺ 3 | 0.5 |
| C3 | Code quality practices | ● 5 | 0.5 |
| C4 | Verification and evidence | ◑⁺ 3 | 0.5 |
| C5 | Code review rigor | ◑⁺ 3 | 1 |
| C6 | Loop engineering | ◑ 2 | 0.5 |
| C7 | Graph engineering | ◑ 2 | 0.5 |
| C8 | Autonomous execution safety | ◑ 2 | 0.5 |
| C9 | Traceability end to end | ◑ 2 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.25 |
| C11 | Security by default | ◑⁺ 3 | 0.5 |
| C12 | Release and operations | ◑⁺ 3 | 0.5 |
| C13 | Context engineering and token efficiency | ● 5 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◕ 4 | 0.5 |
| C16 | Learning loop and measured outcomes | ○ 0 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 59.0 |
| L3 autonomy | A2 (confidence H) |
| L4 coverage | 75% |
| L5 T1 tokens | 2,338 |

**Strengths** (at the benchmark best): C3, C11, C12, C13.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C16 | 0 | 2 | 3 | AWS AI-DLC, BMad Method v7 |
| C1 | 2 | 3 | 5 | BMad Method v7 |
| C4 | 3 | 3 | 5 | Agile V, AWS AI-DLC |

### Superpowers (56.0, benchmark)

| Field | Value |
|---|---|
| Name | Superpowers |
| Origin | Jesse Vincent / Prime Radiant |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT |
| Pin | 22f0b463e7a5 |
| Source | https://github.com/obra/superpowers |

**Key message:** ranks 6 of 10 under baseline weights at 56.0 ± 2.3.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑ 2 | 0.5 |
| C2 | Requirements and specification | ◑ 2 | 0.25 |
| C3 | Code quality practices | ◕ 4 | 0.5 |
| C4 | Verification and evidence | ◕ 4 | 0.5 |
| C5 | Code review rigor | ◕ 4 | 0.5 |
| C6 | Loop engineering | ◕ 4 | 0.5 |
| C7 | Graph engineering | ◑ 2 | 0.5 |
| C8 | Autonomous execution safety | ◑⁺ 3 | 0.5 |
| C9 | Traceability end to end | ◑ 2 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.25 |
| C11 | Security by default | ◔ 1 | 0.25 |
| C12 | Release and operations | ○ 0 | 0.25 |
| C13 | Context engineering and token efficiency | ● 5 | 0.5 |
| C14 | Right-sizing and brownfield | ◑ 2 | 0.5 |
| C15 | Portability and extensibility | ◕ 4 | 0.5 |
| C16 | Learning loop and measured outcomes | ◑ 2 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 56.0 |
| L3 autonomy | A3 (confidence H) |
| L4 coverage | 59% |
| L5 T1 tokens | 1,245 |

**Strengths** (at the benchmark best): C5, C6, C13.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C2 | 2 | 3 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec |
| C1 | 2 | 3 | 5 | BMad Method v7 |
| C11 | 1 | 2 | 3 | Addy Osmani agent-skills, Agile V |

### AWS Kiro (44.4, benchmark)

| Field | Value |
|---|---|
| Name | AWS Kiro |
| Origin | AWS (closed product) |
| Role | benchmark |
| Type | closed |
| Status | implemented |
| Host | Kiro IDE |
| Licence | none |
| Pin | efac9e3a1e15 |
| Source | https://github.com/kirodotdev/Kiro |

**Key message:** ranks 7 of 10 under baseline weights at 44.4 ± 2.7.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◕ 4 | 0.5 |
| C2 | Requirements and specification | ◑ 2 | 0.5 |
| C3 | Code quality practices | ◑ 2 | 0.5 |
| C4 | Verification and evidence | ◑ 2 | 0.5 |
| C5 | Code review rigor | ◑ 2 | 0.5 |
| C6 | Loop engineering | ◑ 2 | 0.5 |
| C7 | Graph engineering | ◑⁺ 3 | 0.5 |
| C8 | Autonomous execution safety | ◑ 2 | 0.5 |
| C9 | Traceability end to end | ◑ 2 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.5 |
| C11 | Security by default | ◑ 2 | 0.5 |
| C12 | Release and operations | ◔ 1 | 0.5 |
| C13 | Context engineering and token efficiency | ◑⁺ 3 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◑ 2 | 0.5 |
| C16 | Learning loop and measured outcomes | ◑ 2 | 1 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 45.4 |
| L3 autonomy | A3 (confidence L) |
| L4 coverage | 49% |
| L5 T1 tokens | n/m |

**Strengths** (at the benchmark best): C7.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C3 | 2 | 3 | 5 | Addy Osmani agent-skills |
| C4 | 2 | 3 | 5 | Agile V, AWS AI-DLC |
| C2 | 2 | 3 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec |

### Matt Pocock skills (43.8, benchmark)

| Field | Value |
|---|---|
| Name | Matt Pocock skills |
| Origin | Matt Pocock |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT |
| Pin | 5863806dd4e1 |
| Source | https://github.com/mattpocock/skills |

**Key message:** ranks 8 of 10 under baseline weights at 43.8 ± 2.8.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑ 2 | 0.5 |
| C2 | Requirements and specification | ◑ 2 | 0.5 |
| C3 | Code quality practices | ◑⁺ 3 | 0.5 |
| C4 | Verification and evidence | ◑ 2 | 0.5 |
| C5 | Code review rigor | ◑ 2 | 0.5 |
| C6 | Loop engineering | ◑ 2 | 0.5 |
| C7 | Graph engineering | ◑ 2 | 0.5 |
| C8 | Autonomous execution safety | ◑ 2 | 1 |
| C9 | Traceability end to end | ◑ 2 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.5 |
| C11 | Security by default | ◔ 1 | 0.5 |
| C12 | Release and operations | ◔ 1 | 0.5 |
| C13 | Context engineering and token efficiency | ◕ 4 | 0.5 |
| C14 | Right-sizing and brownfield | ◑⁺ 3 | 0.5 |
| C15 | Portability and extensibility | ◑⁺ 3 | 0.5 |
| C16 | Learning loop and measured outcomes | ◑ 2 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 45.4 |
| L3 autonomy | A3 (confidence L) |
| L4 coverage | 51% |
| L5 T1 tokens | 575 |

**Strengths** (at the benchmark best): none.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C4 | 2 | 3 | 5 | Agile V, AWS AI-DLC |
| C2 | 2 | 3 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec |
| C5 | 2 | 3 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers |

### GitHub Spec Kit (43.2, benchmark)

| Field | Value |
|---|---|
| Name | GitHub Spec Kit |
| Origin | GitHub |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | GitHub Copilot |
| Licence | MIT |
| Pin | a4d571229e16 |
| Source | https://github.com/github/spec-kit |

**Key message:** ranks 9 of 10 under baseline weights at 43.2 ± 2.6.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◕ 4 | 1 |
| C2 | Requirements and specification | ◑⁺ 3 | 0.5 |
| C3 | Code quality practices | ◑ 2 | 0.25 |
| C4 | Verification and evidence | ◑ 2 | 0.5 |
| C5 | Code review rigor | ◔ 1 | 0.5 |
| C6 | Loop engineering | ◑ 2 | 0.5 |
| C7 | Graph engineering | ◑ 2 | 0.5 |
| C8 | Autonomous execution safety | ◑ 2 | 0.5 |
| C9 | Traceability end to end | ◑ 2 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.5 |
| C11 | Security by default | ◑ 2 | 0.5 |
| C12 | Release and operations | ◔ 1 | 0.5 |
| C13 | Context engineering and token efficiency | ◑⁺ 3 | 0.5 |
| C14 | Right-sizing and brownfield | ◑ 2 | 0.5 |
| C15 | Portability and extensibility | ● 5 | 0.25 |
| C16 | Learning loop and measured outcomes | ○ 0 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 45.0 |
| L3 autonomy | A2 (confidence M) |
| L4 coverage | 49% |
| L5 T1 tokens | 942 |

**Strengths** (at the benchmark best): C15.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C5 | 1 | 3 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers |
| C16 | 0 | 2 | 3 | AWS AI-DLC, BMad Method v7 |
| C3 | 2 | 3 | 5 | Addy Osmani agent-skills |

### OpenSpec (38.8, benchmark)

| Field | Value |
|---|---|
| Name | OpenSpec |
| Origin | Fission AI |
| Role | benchmark |
| Type | open |
| Status | implemented |
| Host | Claude Code |
| Licence | MIT |
| Pin | 0c737dc1b543 |
| Source | https://github.com/Fission-AI/OpenSpec |

**Key message:** ranks 10 of 10 under baseline weights at 38.8 ± 2.6.

| # | Criterion | L1 | u |
|---|---|---|---|
| C1 | Ease of adoption | ◑⁺ 3 | 0.5 |
| C2 | Requirements and specification | ◕ 4 | 0.5 |
| C3 | Code quality practices | ◑⁺ 3 | 0.5 |
| C4 | Verification and evidence | ◑ 2 | 0.5 |
| C5 | Code review rigor | ◑ 2 | 0.5 |
| C6 | Loop engineering | ◑ 2 | 0.5 |
| C7 | Graph engineering | ◑ 2 | 0.5 |
| C8 | Autonomous execution safety | ○ 0 | 0.5 |
| C9 | Traceability end to end | ◔ 1 | 0.5 |
| C10 | Human governance | ◑ 2 | 0.5 |
| C11 | Security by default | ◔ 1 | 0.5 |
| C12 | Release and operations | ◔ 1 | 0.5 |
| C13 | Context engineering and token efficiency | ◑ 2 | 0.5 |
| C14 | Right-sizing and brownfield | ◑ 2 | 0.5 |
| C15 | Portability and extensibility | ◑ 2 | 1 |
| C16 | Learning loop and measured outcomes | ○ 0 | 0.5 |

| Lens | Value |
|---|---|
| L2 ceiling (baseline) | 38.8 |
| L3 autonomy | A1 (confidence M) |
| L4 coverage | 40% |
| L5 T1 tokens | 634 |

**Strengths** (at the benchmark best): C2.

**Weakest three versus the benchmark median**

| # | Score | Median | Best | Leaders |
|---|---|---|---|---|
| C8 | 0 | 2 | 4 | AWS AI-DLC |
| C13 | 2 | 4 | 5 | Addy Osmani agent-skills, AWS AI-DLC, Superpowers |
| C16 | 0 | 2 | 3 | AWS AI-DLC, BMad Method v7 |

## Fit-gap and roadmap

**Key message:** The target trails the best reference on 11 criteria.

| # | Target | Best | Gap (baseline points) | Leaders |
|---|---|---|---|---|
| C1 | 4 | 5 | 1.20 | BMad Method v7 |
| C3 | 4 | 5 | 1.80 | Addy Osmani agent-skills |
| C4 | 4 | 5 | 1.80 | Agile V, AWS AI-DLC |
| C6 | 3 | 4 | 1.40 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers |
| C8 | 3 | 4 | 1.20 | AWS AI-DLC |
| C10 | 3 | 4 | 1.20 | Agile V |
| C12 | 2 | 3 | 1.20 | Addy Osmani agent-skills, AWS AI-DLC |
| C13 | 4 | 5 | 1.20 | Addy Osmani agent-skills, AWS AI-DLC, Superpowers |
| C14 | 3 | 4 | 1.20 | Agile V |
| C15 | 4 | 5 | 0.80 | Agile V, GitHub Spec Kit |
| C16 | 2 | 3 | 0.80 | AWS AI-DLC, BMad Method v7 |
| Total |  |  | 13.80 |  |

### Feature gaps

| # | Feature | Target | At 2 in |
|---|---|---|---|
| F2 | Spec template with testable acceptance criteria | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, AWS Kiro, OpenSpec, GitHub Spec Kit |
| F3 | Independent spec critique | 0 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers |
| F5 | Task decomposition with explicit dependencies | 1 | Addy Osmani agent-skills, AWS AI-DLC, BMad Method v7, AWS Kiro, Matt Pocock skills, GitHub Spec Kit, Superpowers |
| F6 | Decision records (ADR) | 0 | Addy Osmani agent-skills, BMad Method v7, Matt Pocock skills, OpenSpec, GitHub Spec Kit, Superpowers |
| F8 | Routing by size or risk | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, AWS Kiro, Matt Pocock skills |
| F9 | Test-first | 0 | Addy Osmani agent-skills, Matt Pocock skills, Superpowers |
| F11 | Role-specialised agents | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, Matt Pocock skills, Superpowers |
| F12 | Subagents with isolated context and brief | 0 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, Matt Pocock skills, Superpowers |
| F14 | Review by a context independent of the author | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, Matt Pocock skills, Superpowers |
| F15 | Multiple review lenses with consolidation | 0 | Addy Osmani agent-skills, BMad Method v7 |
| F17 | Iteration loop with numeric bound and action | 1 | Agile V, AWS AI-DLC, BMad Method v7, GitHub Spec Kit, Superpowers |
| F18 | Multi-session execution without a human between tasks | 0 | — |
| F20 | Persisted state and resume | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, AWS Kiro, OpenSpec, Superpowers |
| F21 | Environment-enforced limits (hooks, permissions, sandbox) | 0 | AWS AI-DLC, AWS Kiro |
| F23 | Traceable IDs requirement→task→test | 1 | Agile V |
| F24 | Exportable or tool-checked audit trail | 0 | AWS AI-DLC |
| F26 | Incident and postmortem | 1 | — |
| F27 | Retrospective that changes the environment | 0 | AWS AI-DLC, BMad Method v7 |
| F29 | Official support for 3+ agent platforms | 1 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, Matt Pocock skills, OpenSpec, GitHub Spec Kit, Superpowers |
| F30 | Versioned installer and update | 0 | Addy Osmani agent-skills, AWS AI-DLC, BMad Method v7, AWS Kiro, Matt Pocock skills, OpenSpec, GitHub Spec Kit, Superpowers |
| F32 | Token or cost telemetry | 1 | AWS AI-DLC |
| F33 | Context or artifact size budget | 0 | Addy Osmani agent-skills, Agile V, AWS AI-DLC, BMad Method v7, Matt Pocock skills, OpenSpec, Superpowers |

| ID | Horizon | Criteria | Mechanism | Learn from | Effort | Impact | Owner |
|---|---|---|---|---|---|---|---|
| R1 | now | C1 | Add a guided first-run setup with one command | BMad Method v7 | S | 1.2 | maintainer |
| R2 | 60-90 | C16 | Ship evals that measure the method on fixed tasks | AWS AI-DLC | L | 0.8 | maintainer |

| Horizon (cumulative) | Baseline total |
|---|---|
| Current | 68.0 |
| If done: 30 | 69.2 |
| If done: 60-90 | 70.0 |
| If done: now | 69.2 |

> **Hypothesis.** hypothesis: assumes each item lifts its criteria to the stated level; not a score

## Decisions and open questions

**Key message:** One decision remains open.

| Decision | Owner | If not decided |
|---|---|---|
| Adopt R1 now | maintainer | C1 stays at 4 |

## Assumptions and limitations

**Key message:** The numbers are cited and reproducible; the weights and the field effect are not measured.

- **Isolation mode:** not recorded.
- **Host and models (Fixture Method):** host Claude Code; S1 model-a, S2 model-b.
- **Accepted risk (#95):** `requests/log/` is writable throughout a run, so any agent could append log lines or submit an owner answer. The log is informational; owner answers are recorded as "via orchestrator" and the adjudicator treats them only as claims of fact that still need cited evidence.
- **Isolation note (#86):** scorer stages run per instance, but while they run in parallel and the hook cannot identify agents, one scorer could write into another's sealed folder. Write isolation between parallel scorers is then prompt-only.
- **Residual state-integrity risk (#78):** where the hook cannot tell sessions apart, non-privileged state commands for the running stage are bounded by declared-output and hash checks but not prevented.
- **Excluded directories:** Fixture Method: examples/
- **Comparison set:** the 9 frozen benchmarks; no additional references.
- **Cross-round status:** all methods are same-round.
- **Self-assessment:** none.
- **Krippendorff's α:** Fixture Method α = 0.712 (90% interval 0.610–0.800); with few rated units the interval is wide.
- **Kiro:** scored from a 2026-11-26 documentation snapshot that cannot be re-fetched.
- **Calibration drift:** not applicable: no calibration in this report.
- **U_recorded versus derived u:** for the references, the baseline-profile U is the value recorded in the reference round; every other profile, and every target, uses the U derived from per-criterion u.
- **Tokenizer:** tiktoken o200k_base; counts are static proxies.
- **Evidence caps:** closed products scored mostly from documentation are capped at 4 (methodology §12); documentation-only targets are capped as their range assessment states.
- **Single-assessor ranges:** none in this report.
- **Confidence:** medium: scores rest on cited evidence and two independent scorers, but the weights are judgment and the field outcomes are not measured.

---

Generated by ai-sdlc-method-analyzer 0.1.0 on 2026-01-01.

Methodology v1.0 a6e39537 · rubric v2.0 8d5b63ea.

Code and shipped data are under the MIT licence; each reference method keeps its own licence and is not redistributed.

No telemetry: the tool sends nothing anywhere. The AI provider that runs the agents processes the files they read under its own terms.

Sources: [Addy Osmani agent-skills](https://github.com/addyosmani/agent-skills) · [Agile V](https://github.com/Agile-V/agile_v_skills) · [AWS AI-DLC](https://github.com/awslabs/aidlc-workflows) · [BMad Method v7](https://github.com/bmad-code-org/BMAD-METHOD) · [AWS Kiro](https://github.com/kirodotdev/Kiro) · [Matt Pocock skills](https://github.com/mattpocock/skills) · [OpenSpec](https://github.com/Fission-AI/OpenSpec) · [GitHub Spec Kit](https://github.com/github/spec-kit) · [Superpowers](https://github.com/obra/superpowers)
