Translation of rubric-v2.0.pt.md (sha256 8d5b63ea…). Non-normative: the Portuguese original prevails.

# Method Comparison Rubric v2.0 (frozen)

| Field | Value |
|---|---|
| Version | 2.0, frozen on 2026-11-26, before any measurement of the new lenses |
| Basis | Maturity rubric v1.0 (16 criteria), SHA-256 `a6e3953725b67db0189e188c1495ee9b54975e48f65c28baaa01f459b69cf9a4`, attached at `anexos/metodologia-v1.0.md` |
| Freeze rule | Any change after the first measurement requires a new version and a new measurement of every method |

## 0. What changes from v1 to v2

v2 **does not change** the 16 criteria, the anchors or the weights of v1. The maturity total remains the main number. v2 adds four **descriptive, unweighted** lenses, which answer questions that v1 did not answer:

| Lens | Question | Type |
|---|---|---|
| L1 Maturity (v1) | How mature is the method's default path for a professional team? | Weighted score 0–100 (main) |
| L2 Capability ceiling | How mature is the best path the method offers, even if opt-in? | Weighted score 0–100, shown **beside** L1 |
| L3 Autonomy level | How much of the work runs without a human? | Scale A0–A5, descriptive |
| L4 Feature matrix | Which features does the method deliver? | 34 items ●/◐/○, coverage in % |
| L5 Token footprint | How much context does the method consume by construction? | Tokens measured statically (proxy) |

No new lens enters the weighted total: autonomy and tokens already have criteria in v1 (C8, C13), and adding them again would count the same thing twice.

## 1. L2: capability ceiling

**Rule.** L1 caps at 2 the score of mechanisms that are opt-in or off the path the method chooses for reference scenario R (§2.2 of v1). L2 removes only that cap: each criterion gets the highest level supported by **any shipped path** of the method, with the same anchors and the same evidence rules as v1.

**Mechanical selection of cells.** Only the cells whose v1 scorecard cites, in the justification or in the first unmet requirement, the opt-in cap, the default path, the chosen route or an "optional" mechanism are re-examined. All other cells stay equal to L1.

**Reading.** L2 − L1 measures how much value the method leaves off the default path. The difference tends to favour methods with many optional skills; that is why L2 never replaces L1.

## 2. L3: autonomy level (cumulative, requires evidence)

Each level requires its own requirements and those of every previous level, with a file citation. Documentation-only evidence caps at A2 (open method) or A3 (closed product).

| Level | Name | Requirement |
|---|---|---|
| A0 | Prompt library | Isolated instructions; the human invokes each step |
| A1 | Guided workflow | Multi-step workflows are defined; the agent stops and waits for the human between steps |
| A2 | Complete task | The agent executes a whole task (plan → code → test) in one session, with defined stop conditions |
| A3 | In-session orchestration | The agent dispatches subagents with fresh context and chains several tasks without a human per task, within one session |
| A4 | Unattended multi-session execution | An external loop opens new sessions per task, with persisted state and resume, without a human between tasks |
| A5 | Continuous flow | A4 + parallel execution or integration of the tasks without a human, from backlog to integrated change |

**Mandatory reading.** Autonomy is not quality. L3 is always presented crossed with C8 (autonomous execution safety) and with the L1 total, in a two-dimensional chart. An A4 method with a low C8 is **riskier**, not better.

## 3. L4: feature matrix

The list was derived from a generic taxonomy of the development cycle (discovery → design → construction → verification → autonomy → governance → operations → ecosystem) and **not** from the features of any assessed method.

**Values.** ● = present on the default path for R (2 points) · ◐ = opt-in, partial or only documented (1 point) · ○ = absent (0). Each ● or ◐ requires a citation. **Coverage** = points ÷ 68.

*Translator's note: the Feature column uses fixed short English names; any parenthetical or qualifying words of the Portuguese feature name that the short name omits are carried in the Detail column.*

| ID | Group | Feature | Detail |
|---|---|---|---|
| F1 | Discovery | Structured elicitation | interview, mandatory questions |
| F2 | Discovery | Spec template with testable acceptance criteria | |
| F3 | Discovery | Independent spec critique | |
| F4 | Discovery | Spec change control | versioning, impact |
| F5 | Design | Task decomposition with explicit dependencies | |
| F6 | Design | Decision records (ADR) | ADR or equivalent |
| F7 | Design | Existing-code mapping (brownfield) | mapping of the existing code or project context |
| F8 | Design | Routing by size or risk | light and heavy paths |
| F9 | Construction | Test-first | failing test before the code |
| F10 | Construction | Systematic debugging | root-cause procedure |
| F11 | Construction | Role-specialised agents | agents or personas specialised by role |
| F12 | Construction | Subagents with isolated context and brief | the brief is explicit |
| F13 | Verification | Verification gate with fresh command evidence | |
| F14 | Verification | Review by a context independent of the author | |
| F15 | Verification | Multiple review lenses with consolidation | |
| F16 | Verification | Security review or threat modelling | |
| F17 | Autonomy | Iteration loop with numeric bound and action | action taken at the bound |
| F18 | Autonomy | Multi-session execution without a human between tasks | |
| F19 | Autonomy | Execution isolation (branch, worktree, sandbox) | branch, worktree or sandbox |
| F20 | Autonomy | Persisted state and resume | resume after interruption |
| F21 | Autonomy | Environment-enforced limits (hooks, permissions, sandbox) | |
| F22 | Governance | Recorded human approvals (who, when, version) | |
| F23 | Governance | Traceable IDs requirement→task→test | |
| F24 | Governance | Exportable or tool-checked audit trail | |
| F25 | Operations | Release with rollback | |
| F26 | Operations | Incident and postmortem | |
| F27 | Operations | Retrospective that changes the environment | instructions, checks |
| F28 | Operations | Cross-session memory | memory or knowledge base across sessions |
| F29 | Ecosystem | Official support for 3+ agent platforms | 3 or more agent platforms |
| F30 | Ecosystem | Versioned installer and update | |
| F31 | Ecosystem | Automatic validation of the method itself | CI, lint, schema |
| F32 | Economy | Token or cost telemetry | |
| F33 | Economy | Context or artifact size budget | |
| F34 | Economy | Evals that measure the method's behaviour | |

## 4. L5: token footprint (static measurement)

**Reference host.** The primary platform declared by the method (for multi-platform methods, the first one listed in the README).

| Measure | What it includes |
|---|---|
| T1 Always loaded | Instruction files that the host injects into every session (CLAUDE.md, AGENTS.md, copilot-instructions, always-on rules) + descriptions (frontmatter) of every skill/agent/command that the host preloads |
| T2 Entry | Body of the entry skill, command or agent + the files it tells the agent to read on activation |
| T3 Path R | Files that the default path for R tells the agent to read, from start to end of a medium feature (sum, without repetition) |
| T0 Corpus | All Markdown/YAML/TOML text of the method (size reference) |

**Procedure.** An assessor lists the files of T1, T2 and T3 with a citation of where the reading is required. A single script counts the tokens of every method with the same tokenizer (`tiktoken o200k_base`, or characters ÷ 4 if unavailable), locally. The result is a **proxy**: tokenizers of other models differ by about ±20%.

**Out of scope.** Consumption during execution (tokens spent to deliver a feature) is not measured in this version. §6 defines the pilot protocol to measure it.

## 5. Fairness rules (apply to every lens)

1. Same procedure and same output contract for every method.
2. Evidence by file; marketing, roadmap and "coming soon" do not count.
3. When in doubt, the lower level and the lower confidence.
4. Closed product: ceiling set by documentary evidence, marked in the table.
5. A calibration difference between rounds of assessors is shown as sensitivity, never as an adjustment.
6. One assessor per method in the descriptive lenses, with an audit of 15% of the cells drawn with a fixed seed.

## 6. Future protocol: token consumption during execution

Same reference task (feature R in a fixed public repository), same model and same host for every method, 3 runs each. Measure input, output and cache tokens per run from the host's telemetry; report the median and the range; discard a run that does not meet the acceptance criteria. A result is published only with the 3 runs complete.
