# AI development methods: comparative assessment

Date-base **2026-11-27** · Methodology **v1.0 a6e39537** · Rubric **v2.0 8d5b63ea** · Methods **9** · Round **2026-11**

## Overview

This report compares 9 AI development methods on 16 weighted criteria (L1) and four lenses (L2 to L5), under methodology v1.0 and rubric v2.0. The data are the shipped baseline round 2026-11: each public method was read at a pinned commit, listed in the footer.

The 9 frozen benchmarks form the comparison set. Two scorers rated each method independently, a reconciler merged their sheets, and every lens reading was audited.

Under baseline weights, AWS AI-DLC leads at 68.6 ± 3.1; Agile V, BMad Method v7 are within the margin (technical tie).

## Panorama

**Key message:** AWS AI-DLC leads under baseline weights; 3 methods share the technical-tie group.

- **Methods assessed:** 9
- **Leader (baseline):** AWS AI-DLC 68.6
- **Target:** n/a
- **Target position:** n/a
- **Technical-tie group:** 3

| # | Method | Role | Total | ± U | Band (0–100) | Reading | Δ vs leader |
|---|---|---|---|---|---|---|---|
| 1 | AWS AI-DLC | benchmark | 68.6 | 3.1 | 68.6 ± 3.1 | leader | 0.0 |
| 2 | Agile V | benchmark | 67.0 | 3.6 | 67.0 ± 3.6 | technical-tie | -1.6 |
| 3 | BMad Method v7 | benchmark | 66.8 | 2.7 | 66.8 ± 2.7 | technical-tie | -1.8 |
| 4 | Addy Osmani agent-skills | benchmark | 57.6 | 2.9 | 57.6 ± 2.9 | below | -11.0 |
| 5 | Superpowers | benchmark | 56.0 | 2.3 | 56.0 ± 2.3 | below | -12.6 |
| 6 | AWS Kiro | benchmark | 44.4 | 2.7 | 44.4 ± 2.7 | below | -24.2 |
| 7 | Matt Pocock skills | benchmark | 43.8 | 2.8 | 43.8 ± 2.8 | below | -24.8 |
| 8 | GitHub Spec Kit | benchmark | 43.2 | 2.6 | 43.2 ± 2.6 | below | -25.4 |
| 9 | OpenSpec | benchmark | 38.8 | 2.6 | 38.8 ± 2.6 | below | -29.8 |

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

| # | Criterion | Weight | AWS AI-DLC | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Ease of adoption | 6 | ◑ 2 | ◑⁺ 3 | ● 5 | ◑ 2 | ◑ 2 | ◕ 4 | ◑ 2 | ◕ 4 | ◑⁺ 3 |
| C2 | Requirements and specification | 8 | ◕ 4 | ◑ 2 | ◕ 4 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ◕ 4 |
| C3 | Code quality practices | 9 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ● 5 | ◕ 4 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 |
| C4 | Verification and evidence | 9 | ● 5 | ● 5 | ◕ 4 | ◑⁺ 3 | ◕ 4 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C5 | Code review rigor | 8 | ◕ 4 | ◕ 4 | ◕ 4 | ◑⁺ 3 | ◕ 4 | ◑ 2 | ◑ 2 | ◔ 1 | ◑ 2 |
| C6 | Loop engineering | 7 | ◕ 4 | ◕ 4 | ◕ 4 | ◑ 2 | ◕ 4 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C7 | Graph engineering | 4 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 |
| C8 | Autonomous execution safety | 6 | ◕ 4 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ○ 0 |
| C9 | Traceability end to end | 5 | ◑⁺ 3 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◔ 1 |
| C10 | Human governance | 6 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 | ◑ 2 |
| C11 | Security by default | 6 | ◑ 2 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◔ 1 | ◑ 2 | ◔ 1 | ◑ 2 | ◔ 1 |
| C12 | Release and operations | 6 | ◑⁺ 3 | ◑ 2 | ◑ 2 | ◑⁺ 3 | ○ 0 | ◔ 1 | ◔ 1 | ◔ 1 | ◔ 1 |
| C13 | Context engineering and token efficiency | 6 | ● 5 | ◕ 4 | ◕ 4 | ● 5 | ● 5 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑ 2 |
| C14 | Right-sizing and brownfield | 6 | ◑⁺ 3 | ◕ 4 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ◑⁺ 3 | ◑ 2 | ◑ 2 |
| C15 | Portability and extensibility | 4 | ◑ 2 | ● 5 | ◑ 2 | ◕ 4 | ◕ 4 | ◑ 2 | ◑⁺ 3 | ● 5 | ◑ 2 |
| C16 | Learning loop and measured outcomes | 4 | ◑⁺ 3 | ◑ 2 | ◑⁺ 3 | ○ 0 | ◑ 2 | ◑ 2 | ◑ 2 | ○ 0 | ○ 0 |
|  | Total (baseline) | 100 | 68.6 | 67.0 | 66.8 | 57.6 | 56.0 | 44.4 | 43.8 | 43.2 | 38.8 |

**Who leads each criterion** (benchmark set)

| # | Max | Leaders | Benchmark median | Target |
|---|---|---|---|---|
| C1 | 5 | BMad Method v7 | 3 | — |
| C2 | 4 | AWS AI-DLC, BMad Method v7, OpenSpec | 3 | — |
| C3 | 5 | Addy Osmani agent-skills | 3 | — |
| C4 | 5 | Agile V, AWS AI-DLC | 3 | — |
| C5 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers | 3 | — |
| C6 | 4 | Agile V, AWS AI-DLC, BMad Method v7, Superpowers | 2 | — |
| C7 | 3 | Agile V, AWS AI-DLC, BMad Method v7, AWS Kiro | 2 | — |
| C8 | 4 | AWS AI-DLC | 2 | — |
| C9 | 3 | Agile V, AWS AI-DLC, BMad Method v7 | 2 | — |
| C10 | 4 | Agile V | 2 | — |
| C11 | 3 | Addy Osmani agent-skills, Agile V | 2 | — |
| C12 | 3 | Addy Osmani agent-skills, AWS AI-DLC | 1 | — |
| C13 | 5 | Addy Osmani agent-skills, AWS AI-DLC, Superpowers | 4 | — |
| C14 | 4 | Agile V | 3 | — |
| C15 | 5 | Agile V, GitHub Spec Kit | 3 | — |
| C16 | 3 | AWS AI-DLC, BMad Method v7 | 2 | — |

## Features (L4)

**Key message:** Feature coverage is uneven across the nine groups; no method covers them all.

*Group cells show the share of the group's points (2 per feature); coverage is over all 34 features.*

| Group | AWS AI-DLC | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|
| Discovery | ● 100% | ● 88% | ● 100% | ● 88% | ◑ 62% | ◑ 62% | ◑ 38% | ◕ 75% | ◕ 75% |
| Design | ● 88% | ◕ 75% | ● 100% | ● 88% | ◕ 75% | ◑ 62% | ● 88% | ◕ 75% | ◑ 62% |
| Construction | ● 88% | ◕ 75% | ◕ 75% | ● 100% | ● 88% | ◑ 50% | ● 88% | ◑ 38% | ○ 0% |
| Verification | ◕ 75% | ● 88% | ● 88% | ● 100% | ◑ 62% | ◑ 50% | ◑ 50% | ◔ 25% | ◔ 25% |
| Autonomy | ◕ 70% | ◑ 40% | ◑ 60% | ◑ 60% | ◑ 60% | ◕ 70% | ◔ 30% | ◑ 50% | ◔ 30% |
| Governance | ◕ 67% | ◕ 67% | ◑ 50% | ◔ 17% | ◔ 17% | ◔ 33% | ◔ 17% | ◑ 50% | ○ 0% |
| Operations | ◕ 75% | ◑ 62% | ◕ 75% | ◑ 50% | ○ 12% | ◔ 25% | ◑ 38% | ○ 12% | ◑ 38% |
| Ecosystem | ● 100% | ◕ 83% | ◕ 83% | ● 100% | ◕ 83% | ◔ 33% | ◕ 83% | ● 100% | ● 100% |
| Economy | ● 100% | ◕ 67% | ◕ 67% | ◕ 67% | ◕ 67% | ◔ 33% | ◔ 33% | ◔ 17% | ◔ 33% |
| Coverage | 84% | 71% | 78% | 75% | 59% | 49% | 51% | 49% | 40% |

### All 34 features

| # | Feature | AWS AI-DLC | Agile V | BMad Method v7 | Addy Osmani agent-skills | Superpowers | AWS Kiro | Matt Pocock skills | GitHub Spec Kit | OpenSpec |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | Structured elicitation | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ◑ 1 |
| F2 | Spec template with testable acceptance criteria | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ● 2 | ● 2 |
| F3 | Independent spec critique | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 |
| F4 | Spec change control | ● 2 | ● 2 | ● 2 | ● 2 | ○ 0 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 |
| F5 | Task decomposition with explicit dependencies | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 |
| F6 | Decision records (ADR) | ◑ 1 | ◑ 1 | ● 2 | ● 2 | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 |
| F7 | Existing-code mapping (brownfield) | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F8 | Routing by size or risk | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ◑ 1 |
| F9 | Test-first | ◑ 1 | ◑ 1 | ◑ 1 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 |
| F10 | Systematic debugging | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F11 | Role-specialised agents | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ○ 0 | ○ 0 |
| F12 | Subagents with isolated context and brief | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 |
| F13 | Verification gate with fresh command evidence | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F14 | Review by a context independent of the author | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ○ 0 | ◑ 1 |
| F15 | Multiple review lenses with consolidation | ◑ 1 | ◑ 1 | ● 2 | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 |
| F16 | Security review or threat modelling | ◑ 1 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ○ 0 |
| F17 | Iteration loop with numeric bound and action | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ● 2 | ○ 0 |
| F18 | Multi-session execution without a human between tasks | ○ 0 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F19 | Execution isolation (branch, worktree, sandbox) | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 |
| F20 | Persisted state and resume | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ◑ 1 | ● 2 |
| F21 | Environment-enforced limits (hooks, permissions, sandbox) | ● 2 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 | ● 2 | ○ 0 | ○ 0 | ○ 0 |
| F22 | Recorded human approvals (who, when, version) | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 |
| F23 | Traceable IDs requirement→task→test | ◑ 1 | ● 2 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 |
| F24 | Exportable or tool-checked audit trail | ● 2 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ◑ 1 | ○ 0 | ◑ 1 | ○ 0 |
| F25 | Release with rollback | ◑ 1 | ◑ 1 | ◑ 1 | ● 2 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ◑ 1 |
| F26 | Incident and postmortem | ◑ 1 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 | ○ 0 |
| F27 | Retrospective that changes the environment | ● 2 | ◑ 1 | ● 2 | ○ 0 | ◑ 1 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 |
| F28 | Cross-session memory | ● 2 | ● 2 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ◑ 1 | ● 2 |
| F29 | Official support for 3+ agent platforms | ● 2 | ● 2 | ◑ 1 | ● 2 | ● 2 | ○ 0 | ● 2 | ● 2 | ● 2 |
| F30 | Versioned installer and update | ● 2 | ◑ 1 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 |
| F31 | Automatic validation of the method itself | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ○ 0 | ◑ 1 | ● 2 | ● 2 |
| F32 | Token or cost telemetry | ● 2 | ◑ 1 | ◑ 1 | ○ 0 | ◑ 1 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 |
| F33 | Context or artifact size budget | ● 2 | ● 2 | ● 2 | ● 2 | ● 2 | ◑ 1 | ● 2 | ◑ 1 | ● 2 |
| F34 | Evals that measure the method's behaviour | ● 2 | ◑ 1 | ◑ 1 | ● 2 | ◑ 1 | ○ 0 | ○ 0 | ○ 0 | ○ 0 |

## Autonomy × safety (C8) × maturity

**Key message:** Several methods offer more autonomy than their safety controls cover.

| Method | L3 autonomy | C8 safety | L1 (baseline) | Reading |
|---|---|---|---|---|
| AWS AI-DLC | A3 | 4 | 68.6 | orchestrates with partial protection |
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

**Key message:** AWS AI-DLC is first in 59% of centred weight draws; the lead depends on the weighting.

| Method | Baseline total (rank) | Equal total (rank) | Startup total (rank) | Regulated total (rank) | Autonomous total (rank) |
|---|---|---|---|---|---|
| AWS AI-DLC | 68.6 (1) | 66.2 (1) | 67.4 (3) | 68.4 (1) | 72.0 (1) |
| Agile V | 67.0 (2) | 66.2 (1) | 68.0 (2) | 65.6 (2) | 67.4 (3) |
| BMad Method v7 | 66.8 (3) | 65.0 (3) | 68.8 (1) | 65.2 (3) | 67.8 (2) |
| Addy Osmani agent-skills | 57.6 (4) | 55.0 (4) | 60.2 (4) | 54.6 (4) | 57.2 (5) |
| Superpowers | 56.0 (5) | 53.8 (5) | 58.4 (5) | 51.0 (5) | 60.2 (4) |
| AWS Kiro | 44.4 (6) | 45.0 (6) | 48.2 (6) | 41.6 (6) | 45.2 (6) |
| Matt Pocock skills | 43.8 (7) | 43.8 (7) | 46.6 (8) | 40.4 (7) | 44.6 (7) |
| GitHub Spec Kit | 43.2 (8) | 43.8 (7) | 48.2 (6) | 39.6 (8) | 43.2 (8) |
| OpenSpec | 38.8 (9) | 36.2 (9) | 40.6 (9) | 37.2 (9) | 36.8 (9) |
| Leader | AWS AI-DLC | AWS AI-DLC | BMad Method v7 | AWS AI-DLC | AWS AI-DLC |

**P(first)** over 10,000 draws per sampler (seed 20261127).

| Method | Centred | Uniform | Score perturbation | Mean rank (centred) |
|---|---|---|---|---|
| AWS AI-DLC | 0.591 | 0.401 | 0.616 | 1.52 |
| Agile V | 0.251 | 0.399 | 0.207 | 2.18 |
| BMad Method v7 | 0.158 | 0.189 | 0.177 | 2.32 |
| Addy Osmani agent-skills | 0.001 | 0.012 | 0.000 | 4.31 |
| Superpowers | 0.000 | 0.000 | 0.000 | 4.67 |
| AWS Kiro | 0.000 | 0.000 | 0.000 | 6.68 |
| Matt Pocock skills | 0.000 | 0.000 | 0.000 | 7.07 |
| GitHub Spec Kit | 0.000 | 0.000 | 0.000 | 7.39 |
| OpenSpec | 0.000 | 0.000 | 0.000 | 8.87 |

**Tornado** (each weight × 0.5 and × 1.5): methods whose rank moves, and who is first.

| # | Methods moved (max) | First under the change |
|---|---|---|
| C1 | 4 | AWS AI-DLC, BMad Method v7 |
| C2 | 4 | Agile V, AWS AI-DLC |
| C3 | 2 | AWS AI-DLC |
| C4 | 2 | AWS AI-DLC |
| C5 | 2 | AWS AI-DLC |
| C6 | 0 | AWS AI-DLC |
| C7 | 0 | AWS AI-DLC |
| C8 | 2 | AWS AI-DLC |
| C9 | 0 | AWS AI-DLC |
| C10 | 2 | AWS AI-DLC |
| C11 | 3 | AWS AI-DLC |
| C12 | 2 | AWS AI-DLC |
| C13 | 1 | AWS AI-DLC |
| C14 | 3 | AWS AI-DLC |
| C15 | 2 | AWS AI-DLC |
| C16 | 2 | AWS AI-DLC |

**Leave-one-out** (each criterion removed in turn).

| Removed | First |
|---|---|
| C1 | AWS AI-DLC |
| C2 | Agile V |
| C3 | AWS AI-DLC |
| C4 | AWS AI-DLC, BMad Method v7 |
| C5 | AWS AI-DLC |
| C6 | AWS AI-DLC |
| C7 | AWS AI-DLC |
| C8 | Agile V |
| C9 | AWS AI-DLC |
| C10 | AWS AI-DLC |
| C11 | AWS AI-DLC |
| C12 | AWS AI-DLC |
| C13 | AWS AI-DLC |
| C14 | AWS AI-DLC |
| C15 | AWS AI-DLC |
| C16 | AWS AI-DLC |

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

**Key message:** ranks 1 of 9 under baseline weights at 68.6 ± 3.1.

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

**Key message:** ranks 2 of 9 under baseline weights at 67.0 ± 3.6.

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

**Key message:** ranks 3 of 9 under baseline weights at 66.8 ± 2.7.

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

**Key message:** ranks 4 of 9 under baseline weights at 57.6 ± 2.9.

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

**Key message:** ranks 5 of 9 under baseline weights at 56.0 ± 2.3.

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

**Key message:** ranks 6 of 9 under baseline weights at 44.4 ± 2.7.

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

**Key message:** ranks 7 of 9 under baseline weights at 43.8 ± 2.8.

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

**Key message:** ranks 8 of 9 under baseline weights at 43.2 ± 2.6.

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

**Key message:** ranks 9 of 9 under baseline weights at 38.8 ± 2.6.

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

## Assumptions and limitations

**Key message:** The numbers are cited and reproducible; the weights and the field effect are not measured.

- **Isolation mode:** not applicable: no target run in this report.
- **Host and models:** the baseline references were scored in the reference round; per-stage model IDs are not part of the shipped data.
- **Accepted risk (#95):** `requests/log/` is writable throughout a run, so any agent could append log lines or submit an owner answer. The log is informational; owner answers are recorded as "via orchestrator" and the adjudicator treats them only as claims of fact that still need cited evidence.
- **Isolation note (#86):** scorer stages run per instance, but while they run in parallel and the hook cannot identify agents, one scorer could write into another's sealed folder. Write isolation between parallel scorers is then prompt-only.
- **Residual state-integrity risk (#78):** where the hook cannot tell sessions apart, non-privileged state commands for the running stage are bounded by declared-output and hash checks but not prevented.
- **Excluded directories:** none.
- **Comparison set:** the 9 frozen benchmarks; no additional references.
- **Cross-round status:** all methods are same-round.
- **Self-assessment:** none.
- **Krippendorff's α:** not applicable: no target run in this report.
- **Kiro:** scored from a 2026-11-26 documentation snapshot that cannot be re-fetched.
- **Calibration drift:** not applicable: no calibration in this report.
- **U_recorded versus derived u:** for the references, the baseline-profile U is the value recorded in the reference round; every other profile, and every target, uses the U derived from per-criterion u.
- **Tokenizer:** tiktoken o200k_base; counts are static proxies.
- **Evidence caps:** closed products scored mostly from documentation are capped at 4 (methodology §12); documentation-only targets are capped as their range assessment states.
- **Single-assessor ranges:** none in this report.
- **Confidence:** medium: scores rest on cited evidence and two independent scorers, but the weights are judgment and the field outcomes are not measured.

---

Generated by ai-sdlc-method-analyzer 0.1.0 on 2026-11-27.

Methodology v1.0 a6e39537 · rubric v2.0 8d5b63ea.

Code and shipped data are under the MIT licence; each reference method keeps its own licence and is not redistributed.

No telemetry: the tool sends nothing anywhere. The AI provider that runs the agents processes the files they read under its own terms.

Sources: [Addy Osmani agent-skills](https://github.com/addyosmani/agent-skills) · [Agile V](https://github.com/Agile-V/agile_v_skills) · [AWS AI-DLC](https://github.com/awslabs/aidlc-workflows) · [BMad Method v7](https://github.com/bmad-code-org/BMAD-METHOD) · [AWS Kiro](https://github.com/kirodotdev/Kiro) · [Matt Pocock skills](https://github.com/mattpocock/skills) · [OpenSpec](https://github.com/Fission-AI/OpenSpec) · [GitHub Spec Kit](https://github.com/github/spec-kit) · [Superpowers](https://github.com/obra/superpowers)
