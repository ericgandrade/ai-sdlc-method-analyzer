# AI SDLC Method Analyzer

**Assess any AI-assisted software development method with the same frozen rules, and compare it with the best public methods.**

> **Status: planned.** The implementation plan is final and reviewed; the code is being built phase by phase. Start with the [implementation plan](docs/plans/2026-11-27-ai-sdlc-method-analyzer.md).

Teams now write software with coding agents guided by a *method*: skills, agents, prompts, templates and checks that say how work goes from idea to production. There are dozens of them, and most are compared by opinion. This project turns the comparison into a repeatable assessment:

- one **frozen methodology** (16 weighted criteria with written level anchors, hashed before any scoring);
- a team of **agents** that score, reconcile, red-team and audit, each isolated from the others;
- a **deterministic engine** that does every number;
- a **comparative report** (self-contained HTML, Markdown and a slide deck) against a pinned baseline of public methods.

You point it at a method — a folder on your machine, a private git repository, or only its documentation — and get a scored, evidence-cited comparison. It is generic and unbranded, and your source stays on your machine.

---

## What you will be able to do

When you open the project in Claude Code and run `/analyze`, a start menu asks what you want:

| # | Option | What happens |
|---|---|---|
| 1 | Assess a **local folder** | The method is snapshotted, traced on a reference scenario and scored by two calibrated scorers, then reconciled, red-teamed and measured on four lenses |
| 2 | Assess a **private git repository** | Cloned with your own credentials at a commit you choose; then as option 1 |
| 3 | Assess from **documentation only** | For closed products or methods you cannot read: scored as a range (floor, centre, ceiling) with a list of what could not be assessed and what would be needed |
| 4 | **Refresh the references** | Fetch the public reference methods at their pins and re-check the baseline |
| 5 | **Compare and report** | Ranking, criteria matrix, features matrix, autonomy × safety, tokens and per-method profiles, as HTML, Markdown and slides |
| 6 | **Fit-gap and roadmap** | What a chosen method can learn from the best of each reference, ranked by points per effort |

**Privacy.** Your source never leaves your machine except to the model provider your agent host already uses; the tool adds no network calls, no telemetry and no uploads. The only network step is fetching public references.

## The 16 criteria

Each criterion is scored 0–5 against written anchors, with cumulative gates and an evidence citation (file and line) for every level. The total is a weighted score from 0 to 100.

| ID | Criterion | What it asks | Weight |
|---|---|---|---:|
| C1 | Ease of adoption | How fast a team gets a first successful use | 6 |
| C2 | Requirements and specification | Testable acceptance criteria, non-goals, independent critique, change control | 8 |
| C3 | Code quality practices | Test-first, design before code, simplicity, anti-rationalization | 9 |
| C4 | Verification and evidence | "Done" backed by fresh command output on the latest change | 9 |
| C5 | Code review rigor | Independent reviewer, multiple lenses, per-finding triage | 8 |
| C6 | Loop engineering | Every loop has a numeric bound and an escalation target | 7 |
| C7 | Graph engineering | Task dependencies and code maps that drive the work | 4 |
| C8 | Autonomous-run safety | Isolation, preflight, budgets and limits enforced by the environment | 6 |
| C9 | Traceability | Requirement → task → test → change → release | 5 |
| C10 | Human governance | Approvals recorded with who, when and which version | 6 |
| C11 | Security by default | Security on the default path, not as an add-on | 6 |
| C12 | Release and operations | Rollback, observability, incidents | 6 |
| C13 | Context management | Loading on demand, hand-offs, context budgets | 6 |
| C14 | Right-sizing and brownfield | Light paths for small changes; existing codebases | 6 |
| C15 | Portability and extensibility | Several agent hosts; a versioned extension interface | 4 |
| C16 | Learning loop | Retrospectives that change the method, not only minutes | 4 |

Weights above are the *baseline* profile. Four more profiles (equal, startup, regulated, autonomous) test whether a conclusion depends on the weighting.

**Four descriptive lenses** sit beside the score and are never added to it: **capability ceiling** (the best path the method ships, even if opt-in), **autonomy** (A0 prompt library … A5 continuous flow, always read together with C8), **34 features** in nine groups, and **static token footprint** (always loaded, entry, default path).

## How the assessment works

1. **Freeze.** Methodology, scorer brief and lenses rubric are hashed before any scoring. Changing them means a new version and re-scoring everything.
2. **Pin and isolate.** The target is snapshotted; scorers never see earlier scores of it.
3. **Trace the default path** on a reference scenario (a team of 3–8 adding a medium feature to an existing service). Opt-in mechanisms are capped.
4. **Score twice.** Two scorers work separately, each calibrated first on a reference method.
5. **Reconcile and measure agreement** (Krippendorff's α). A difference of one level takes the lower score.
6. **Red team.** An auditor tries to refute every high score: is it on the default path, shipped, and enforced — or only described?
7. **Lenses and a full audit** of every lens cell; static token counts with one tokenizer for every method.
8. **Consolidate.** Totals per profile with an uncertainty band, a pre-registered superiority test, sensitivity and the probability of ranking first under random weights.
9. **Report and review.** The report builder renders; a reviewer checks every claim against the data and scans for leaks.

Fairness rules apply to every method: same procedure, evidence by file, marketing and "coming soon" never count, the lower level when in doubt, closed products capped by documentation evidence, and sources treated as data — never as instructions.

## Reference methods

Fetched at their pins into a local cache; never copied into this repository.

| Method | Origin | Licence | Role |
|---|---|---|---|
| [AWS AI-DLC](https://github.com/awslabs/aidlc-workflows) | AWS | MIT-0 | benchmark |
| [Agile V](https://github.com/Agile-V/agile_v_skills) | Agile V community | CC BY-SA 4.0 (cited, never quoted) | benchmark |
| [BMad Method v7](https://github.com/bmad-code-org/BMAD-METHOD) | BMad Code | MIT | benchmark |
| [Addy Osmani agent-skills](https://github.com/addyosmani/agent-skills) | Addy Osmani | MIT | benchmark |
| [Superpowers](https://github.com/obra/superpowers) | Jesse Vincent / Prime Radiant | MIT | benchmark |
| [AWS Kiro](https://kiro.dev) | AWS (closed product, documentation only) | — | benchmark |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | Matt Pocock | MIT | benchmark |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | GitHub | MIT | benchmark |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Fission AI | MIT | benchmark |
| [GSD Core](https://github.com/open-gsd/gsd-core) ("Get Shit Done") | Open GSD | MIT | additional reference, to be scored |
| [Ralph](https://github.com/snarktank/ralph) | snarktank (Ralph loop technique) | MIT | additional reference, to be scored |

The nine **benchmarks** form the frozen comparison set for verdicts. **Additional references** are ranked and profiled but stay outside verdicts until a new methodology version re-freezes the set. Pins are listed in the plan, §3.

## Limits, stated up front

- It measures **documented and implemented mechanisms** on a reference scenario, not productivity or defect rates in the field.
- Scorers are AI agents. Isolation, calibration, agreement statistics and a red team reduce, but do not remove, shared bias.
- Token counts are a static proxy, not runtime consumption.
- A method assessed by its own author is labelled **self-assessment**.

## Roadmap

The [plan](docs/plans/2026-11-27-ai-sdlc-method-analyzer.md) has eight phases with exit gates: foundations and frozen files → baseline and leak gate → engine → HTML report and slide deck → agents and guard → portability → end-to-end verification (re-score one reference within its uncertainty band, then score GSD and Ralph) → release.

## Contributing

Issues are welcome, especially: a reference method you think was scored wrong (cite the file and line), a method you want added to the reference set, or a criterion anchor you find ambiguous. Corrections with evidence change the numbers.

## Licence

[MIT](LICENSE). Third-party methods keep their own licences and are never redistributed here.
