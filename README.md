# AI SDLC Method Analyzer

> **Status: v0.1.0.** The pipeline is complete (engine, report, agent briefs, guard) and has been tested end to end with simulated agents on a tiny fixture method (`docs/reviews/dry-run.md`). The live-session checks and the first real end-to-end scoring runs (re-scoring one reference, then GSD and Ralph) are planned for v0.2; see `TODO.md`.

## What it is

The AI SDLC Method Analyzer assesses an AI-assisted software development method (the skills, agents, prompts, templates and checks that tell coding agents how work goes from idea to production) against one frozen, 16-criterion methodology. It outputs a scored, evidence-cited assessment and a self-contained comparative report (HTML and Markdown) against a pinned baseline of nine public methods. It measures what a method specifies and implements on a reference scenario, not field outcomes such as productivity or defect rates.

## Prerequisites

- Python 3.10 or later. The engine uses the standard library only.
- git 2.30 or later.
- A supported agent host:
  - **Claude Code** for the primary path (spike 0.3 recorded version 2.1.332 on the maintainer machine; the live checks are v0.2);
  - or Copilot CLI, Codex or Gemini CLI through [`AGENTS.md`](AGENTS.md).
- About 5 GB free in the user data folder for the reference cache.
- Optional: `tiktoken==0.14.0` for exact token counts. Without it, counts are chars/4 and the report labels them "approx.".
- Optional: `pdftotext` (poppler) for PDF documentation.

## Quick start

Your source never leaves your machine except to the model provider your agent host already uses; the tool adds no network calls, no telemetry and no uploads.

| Step | macOS / Linux | Windows (PowerShell, cmd or Windows Terminal) |
|---|---|---|
| 1. Clone | `git clone https://github.com/ericgandrade/ai-sdlc-method-analyzer.git` | same |
| 2. Optional: exact tokens | `python3 -m pip install -r requirements-tokens.txt` | `py -3 -m pip install -r requirements-tokens.txt` |
| 3. Local host settings (before opening the folder) | `python3 -m engine setup` | `py -3 -m engine setup` |
| 4. Fetch the references | `python3 -m engine fetch --all --docs --tokenizer` | `py -3 -m engine fetch --all --docs --tokenizer` |
| 5. Check the baseline report | `python3 -m engine report --baseline-only` | `py -3 -m engine report --baseline-only` |
| 6. Open the folder in Claude Code and run | `/analyze` | `/analyze` |

- **Step 3** writes the git-ignored `.claude/settings.local.json`, which gives the host access to the data folder without prompts. If the folder is already open, reload the window or restart the session. `engine setup --check` verifies it, and `engine setup --remove` removes exactly what it added.
- **Step 4** is one of the two network commands. Without tiktoken, the tokenizer step is skipped with a notice.
- **Step 5** renders the shipped baseline report into your data folder, as a check that the engine works.
- **Step 6.** The project-scoped agents and the `/analyze` skill load with no install step.

**The marketplace plugin is the alternative path** (`.claude-plugin/marketplace.json`). **Use one path, not both**: both together load the agents and `/analyze` twice. For other hosts, see [`AGENTS.md`](AGENTS.md).

Runs, reports and the cache go to the per-user data folder `$AMA_HOME`, never inside the clone. The defaults are `~/Library/Application Support/ai-sdlc-method-analyzer` on macOS, `${XDG_DATA_HOME:-~/.local/share}/ai-sdlc-method-analyzer` on Linux and `%LOCALAPPDATA%\ai-sdlc-method-analyzer` on Windows. Set the `AMA_HOME` environment variable to override it; a folder inside the clone is refused.

Optionally, run `python3 -m engine hooks install`. For contributors it is mandatory (see `CLAUDE.md`).

## The menu, walked through

`/analyze` runs `engine setup --check` and `engine verify-freeze`, lists runs in progress (`[r]` resumes one), then shows:

```
AI SDLC Method Analyzer — methodology v1.0 (a6e39537), rubric v2.0 (8d5b63ea)
Runs in progress: <list or "none">   [r] resume a run

1  Assess a method from a local folder
2  Assess a private git repository (cloned with your own git; credentials never stored)
3  Assess a method from documentation only (PDF/HTML/Markdown) → range: floor / centre / ceiling
4  Re-run or refresh a bundled reference at its pin
5  Compare assessed targets with the reference baseline and build the report
6  Fit-gap and roadmap for a target: what it can learn from the best of each reference
q  Quit
```

Every question has a default. Before the first agent stage, the orchestrator restates your choices, prints the `engine estimate` output (sessions, time and corpus size, labelled a hypothesis), offers per-stage budgets and asks "proceed? (y/n)".

| # | Questions | What you get | In v0.1 |
|---|---|---|---|
| 1 | path (copied into the run) · display name · slug · implemented or design-only · "do you own or author this method?" · scorer model (auto-detected; you confirm) · method boundary | a snapshot, a default-path trace, two calibrated scorers, reconciliation and α, a red team, four lenses with a 100% audit, tokens, totals, ranking, sensitivity, superiority and a dense analysis; the run closes at S14 and offers 5 and 6 | pipeline built and dry-run with simulated agents; the first live run is v0.2 |
| 2 | URL (refused if it embeds credentials) · ref, branch or tag · name · slug · status · ownership · scorer model · boundary | as 1; intake clones with your own git | as 1 |
| 3 | files or folder · name · slug · closed product (cap 4, A3) or open method without its source (cap 3, A2) · second assessor? | a range: floor, centre and ceiling, with what could not be assessed | engine (`ranges`) and brief built; the live docs-only run and `engine convert` are v0.2 |
| 4 | which slug(s) · same pin (reproduce) or new pin | a reproduction delta against `baseline/` (within ±U?); `baseline promote` for a new pin | pipeline built; the first real reproduction (A2) is v0.2 |
| 5 | which closed runs · include additional references · title · theme · public or private · slide deck? | a compare run: `report.html` and `report.md` | `consolidate`, `rank`, `sensitivity`, `superiority` and `report` built; the run stops at S16b until the deck, `report --public` and `--copy-to` ship in v0.2 |
| 6 | which closed run · all references or a subset | a fit-gap run: `fitgap.md` and a report section | `fitgap` and the brief built; the run stops at S16b as 5 |

**Terminal steps (terminal).** Some steps must be typed by you in your own terminal, from the project folder. The orchestrator prints the exact command, with the recorded interpreter and run id, and waits. The host's in-chat shell escape will not do, because it is not an interactive terminal. The steps are:

- (terminal) person adjudication: `engine adjudication import --run <id> <file>`, then `engine state resume --run <id>` (menus 1 and 2);
- (terminal) `engine baseline promote` (menu 4);
- (terminal) aborts and forced closes: `engine state close --run <id> --abort` or `--force`.

**Windows:** use PowerShell, cmd or Windows Terminal. Git Bash (mintty) does not present a TTY to native Python. Run `py -3 -m engine tty-check` to test your terminal.

## Scenario R

The default path is judged against one scenario, quoted from methodology §2.2:

> **R:** A team of 3–8 professional engineers adds a medium-sized feature (roughly 3–10 tasks, 5–20 files touched) to an existing production web service that has version control, CI and a team rule that changes are reviewed before merge. The team uses one supported AI coding agent.

## The 16 criteria

Each criterion is scored 0–5 against written anchors, with an evidence citation for every level. The total is a weighted score from 0 to 100.

| ID | Criterion | Meaning (one line) | Weight |
|---|---|---|---:|
| C1 | Ease of adoption | Human effort to a first successful use on the primary platform | 6 |
| C2 | Requirements and specification | Elicitation, testable acceptance criteria, scope, spec change control | 8 |
| C3 | Code quality practices | Test-first, test quality, design discipline, simplicity, anti-rationalization | 9 |
| C4 | Verification and evidence | Completion claims backed by fresh, version-bound evidence | 9 |
| C5 | Code review rigor | Independent review with multi-axis checklist and finding triage | 8 |
| C6 | Loop engineering | Bounded feedback loops with exit criteria, escalation and loopback routing | 7 |
| C7 | Graph engineering | Task dependency graphs and codebase maps that drive decisions | 4 |
| C8 | Autonomous execution safety | Preflight, isolation, halts, resume, budgets and authority limits for unattended runs | 6 |
| C9 | Traceability end to end | Stable IDs linking requirement → task → code → test → release → production | 5 |
| C10 | Human governance | Named decision points, recorded and enforced approvals, waivers | 6 |
| C11 | Security by default | Secure-development and agent-specific controls (SSDF, prompt injection) | 6 |
| C12 | Release and operations | Rollout, rollback, observability, incidents, production feedback | 6 |
| C13 | Context engineering and token efficiency | Progressive disclosure, hand-offs through files, budgets, fresh contexts | 6 |
| C14 | Right-sizing and brownfield | Process weight matched to change size and risk; entry into existing code | 6 |
| C15 | Portability and extensibility | Platforms supported, runtime dependencies, extension mechanisms | 4 |
| C16 | Learning loop and measured outcomes | Retrospectives that change the environment; outcome metrics | 4 |

Every anchor instantiates one generic ladder (methodology §3.2):

| Level | Generic meaning |
|---|---|
| 0 | Absent, or the method's text contradicts the practice |
| 1 | Mentioned as advice or principle; no procedure |
| 2 | A defined procedure, template or checklist exists, but it is optional, off the default path, or produces no record |
| 3 | Integrated: on the default path, with explicit criteria and a named artifact or record |
| 4 | Robust: level 3 plus independence, bounds, explicit failure handling and edge-case coverage |
| 5 | Mechanized or closed-loop: level 4 plus enforcement beyond prompts, or measured evidence that the mechanism works |

The weights above are the baseline profile. Four alternative profiles (methodology §5.3) test whether a conclusion depends on the weighting:

| ID | Equal | Startup speed | Regulated enterprise | Autonomous scale |
|---|---:|---:|---:|---:|
| C1 | 6.25 | 12 | 3 | 4 |
| C2 | 6.25 | 6 | 10 | 6 |
| C3 | 6.25 | 10 | 7 | 7 |
| C4 | 6.25 | 8 | 10 | 9 |
| C5 | 6.25 | 6 | 9 | 8 |
| C6 | 6.25 | 7 | 5 | 11 |
| C7 | 6.25 | 4 | 2 | 9 |
| C8 | 6.25 | 8 | 5 | 11 |
| C9 | 6.25 | 2 | 10 | 4 |
| C10 | 6.25 | 2 | 11 | 4 |
| C11 | 6.25 | 4 | 9 | 5 |
| C12 | 6.25 | 5 | 7 | 4 |
| C13 | 6.25 | 8 | 3 | 9 |
| C14 | 6.25 | 10 | 4 | 4 |
| C15 | 6.25 | 6 | 1 | 3 |
| C16 | 6.25 | 2 | 4 | 2 |

## The lenses

Four descriptive lenses sit beside the L1 score and are never added to it. Rubric v2 is normative in its frozen Portuguese original ([`methodology/rubric-v2.0.pt.md`](methodology/rubric-v2.0.pt.md)), because the hash freezes that text; the English translation ([`methodology/rubric-v2.0.en.md`](methodology/rubric-v2.0.en.md)) is provided for every reader, and if the two ever differ, the Portuguese prevails.

- **L2, capability ceiling:** the best path the method ships, even if opt-in. It is shown beside L1, never instead of it.
- **L3, autonomy A0–A5:** from a prompt library (A0) to continuous flow (A5). It is always read together with C8: an A4 method with a low C8 is riskier, not better.
- **L4, 34 features in 9 groups:** ● on the default path (2 points), ◐ opt-in or partial (1), ○ absent (0); coverage is points ÷ 68.

  | Group | Features |
  |---|---|
  | Discovery | F1–F4 |
  | Design | F5–F8 |
  | Construction | F9–F12 |
  | Verification | F13–F16 |
  | Autonomy | F17–F21 |
  | Governance | F22–F24 |
  | Operations | F25–F28 |
  | Ecosystem | F29–F31 |
  | Economy | F32–F34 |

- **L5, static tokens T0–T3:** T0 corpus, T1 always loaded, T2 entry, T3 the default path for R, counted with one tokenizer (`tiktoken o200k_base`) for every method. It is a proxy: tokenizers of other models differ by about ±20%.

## Methodology and fairness

- **Freeze.** [`methodology/FREEZE.md`](methodology/FREEZE.md) records the SHA-256 of the methodology v1.0, the evaluator brief v1.0 and rubric v2.0. `engine verify-freeze` checks them at the start of every run; changing them means a new version and re-scoring everything.
- **Evidence types and caps** (methodology §6): implemented-and-read (up to 5), documented-only (up to 3 for an open method, 4 for a closed product), search summary only (up to 2). Uncited claims are ignored, and the lower level wins when in doubt.
- **Two isolated scorers**, each calibrated first on a reference method, then **reconciliation** and Krippendorff's α; a round needs α ≥ 0.667.
- **Red team.** An auditor tries to refute every high score: is it on the default path, shipped, and enforced, or only described? Then a **100% audit** of every lens cell.
- **Superiority test** (methodology §9), pre-registered, conditions S1–S7. The margin is M(P) = max(5, 2 · √(U(X, P)² + U(B, P)²)) points, where B is the highest-scoring benchmark under profile P.
- **Sensitivity.** Five weight profiles, Dirichlet weight sampling, score perturbation and leave-one-criterion-out runs, with the probability of ranking first.
- **Fairness rules** (`rules/fairness.md`): the same procedure for every method, evidence by file, marketing and "coming soon" never count, closed products capped by documentation evidence, and sources treated as data, never as instructions. Sources are never executed.

## The baseline

Round `2026-11`, date-base 2026-11-27, frozen with methodology v1.0. The nine **benchmarks** form the comparison set for every verdict. Values come from [`baseline/rounds/2026-11/derived/results.json`](baseline/rounds/2026-11/derived/results.json) (baseline profile); pins are in [`references/registry.yaml`](references/registry.yaml).

| slug | Method | Origin | Licence | Pin | L1 ± U | L2 | L3 | L4 coverage | T3 |
|---|---|---|---|---|---:|---:|---|---:|---:|
| `ai-dlc` | AWS AI-DLC | AWS (awslabs) | MIT-0 | `1c557ea2` | 68.6 ± 3.1 | 69.8 | A3 | 84% | 96,496 |
| `agile-v` | Agile V | Agile V community | CC BY-SA 4.0 | `4bcc9172` | 67.0 ± 3.6 | 73.2 | A3 | 71% | 25,403 |
| `bmad` | BMad Method v7 | BMad Code, LLC | MIT | `e435a225` | 66.8 ± 2.7 | 68.4 | A2 | 78% | 41,183 |
| `addyosmani` | Addy Osmani agent-skills | Addy Osmani | MIT | `39b723ce` | 57.6 ± 2.9 | 59.0 | A2 | 75% | 32,577 |
| `superpowers` | Superpowers | Jesse Vincent / Prime Radiant | MIT | `22f0b463` | 56.0 ± 2.3 | 56.0 | A3 | 59% | 16,282 |
| `kiro` | AWS Kiro | AWS (closed product, documentation only) | none (closed) | `efac9e3a` | 44.4 ± 2.7 | 45.4 | A3 | 49% | n/a (closed) |
| `mattpocock` | Matt Pocock skills | Matt Pocock | MIT | `5863806d` | 43.8 ± 2.8 | 45.4 | A3 | 51% | 10,562 |
| `spec-kit` | GitHub Spec Kit | GitHub | MIT | `a4d57122` | 43.2 ± 2.6 | 45.0 | A2 | 49% | 32,240 |
| `openspec` | OpenSpec | Fission AI | MIT | `0c737dc1` | 38.8 ± 2.6 | 38.8 | A1 | 40% | 13,998 |

**Additional references** are registered but outside the verdict set. They are not scored in v0.1; their first scoring runs are v0.2.

| slug | Method | Origin | Licence | Pin | Status |
|---|---|---|---|---|---|
| `gsd` | GSD Core ("Get Shit Done") | Open GSD | MIT | `e3dcca27` | to score (v0.2) |
| `ralph` | Ralph (snarktank implementation of the Ralph loop) | Ryan Carson; technique by Geoffrey Huntley | MIT | `6c53cb0b` | to score (v0.2) |

The shipped baseline report is [`docs/report/index.html`](docs/report/index.html) (Markdown: [`docs/report/report.md`](docs/report/report.md)). The data, scorecards, lenses and audits are in [`baseline/`](baseline/); `engine baseline verify` checks them against `MANIFEST.json`.

Scores refer to the pinned versions only. A method may have changed since its pin.

## Privacy and security

Your source never leaves your machine except to the model provider your agent host already uses; the tool adds no network calls, no telemetry and no uploads.

- **Snapshot.** A local folder is copied, and a private repository is cloned, into the run folder in `$AMA_HOME`. The snapshot is never copied into `baseline/`, a report (except as relative citations) or a commit.
- **Credentials** are handled only by your own git (credential helper or SSH agent). The tool never asks for, stores or logs a token, and `intake` refuses URLs that embed credentials.
- **Two network commands only:** `engine fetch` (public references at their pins, the documentation pages of the registry and the tokenizer file) and `engine intake --mode git` (a clone of the URL you gave). With `--offline` or `AMA_OFFLINE=1`, both exit 6 instead of touching the network.
- **The guard hook.** In Claude Code, a default-deny PreToolUse hook (`hooks/guard.py`) allows agents only `python -m engine …` calls and writes to their stage's outputs while a run is active, and fails closed. On other hosts the guard is prompt-only.
- **Leak gate.** `engine leakcheck` scans for private terms (your own denylist), secrets, absolute home paths and CC BY-SA text. Run it before sharing anything.
- To report a leak or a vulnerability privately, see [`SECURITY.md`](SECURITY.md).

## How to add a reference

1. Add the entry to `references/registry.yaml` on a branch, while no run is active.
2. Run `python3 -m engine fetch --slug <slug>`.
3. Run menu option 4 with the new slug.
4. (terminal) Run `python3 -m engine baseline promote`.
5. Add the `CHANGELOG.md` line that names the run.
6. Open a pull request with the run's `review.json` verdict.
7. **To undo a bad promotion,** `git revert` the promotion commit; `engine baseline verify` must pass afterwards.
8. New references join as *additional references* (`benchmark: false`). Only a new methodology version can change the benchmark set.

In v0.1 no reference has yet been promoted by this route; the first promotions (GSD and Ralph) are v0.2.

## Pointing it at your own method

1. **Assess** with menu option 1 (local folder) or 2 (private repository). Declare `design-only` if the method exists only as a plan; the methodology §8 rules (design score D, realization factor r, risk-adjusted RA = D·r) then apply at every stage. Answer "yes" to "do you own or author this method?": the run is labelled **self-assessment**, and you may answer factual questions but never adjudicate.
2. **Read the verdict honestly:** the position with ±U, the superiority verdict with every failed condition, the three weakest criteria against the benchmark median, and whether the comparison is same-round or cross-round.
3. **Fit-gap** with menu option 6: for each criterion below the best reference, the leading references, your first unmet requirement, a concrete mechanism to build, its effort and impact in weighted points.
4. **Build the mechanisms** in your method's own repository. Describe ideas, never copy text; `rules/licences.md` applies.
5. **Re-assess as a new run** at the new pin, with new scorers; the earlier scorecards are off limits.
6. **Guard against teaching to the test.** The red team contests every new 4–5, and the report labels the run "method revised against this rubric".
7. **Share safely:** run `leakcheck` with your own denylist before sharing anything.

## How to cite

Cite the software with [`CITATION.cff`](CITATION.cff) (GitHub shows a "Cite this repository" button). Suggested text:

> AI SDLC Method Analyzer, version 0.1.0 (2026-11-27), methodology v1.0 (SHA-256 prefix a6e39537), rubric v2.0 (8d5b63ea). https://github.com/ericgandrade/ai-sdlc-method-analyzer

When citing a score, name the round (`2026-11`), the reference pin and the methodology version.

## Licences and third parties

- This repository is under the [MIT licence](LICENSE).
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) lists every reference method, its licence and how it is used.
- References are not vendored: they are fetched at their pins into your local cache and never redistributed here.
- Agile V is CC BY-SA 4.0: this repository cites its paths only and never quotes its text (`engine leakcheck --ccbysa` checks it).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A guard denial (stderr names the rule) | agents may only run `<python> -m engine …`; the recorded interpreter may differ | `python3 -m engine setup --check` |
| `setup --check` fails (exit 3) | settings missing, or `AMA_HOME` moved | `python3 -m engine setup`, then reload the window or restart the session |
| A recovery command is denied inside the host | while a run is active the guard denies other Bash inside the host | type every *(terminal)* command below in your own terminal, from the project folder |
| A stale run after a crash *(terminal)* | the run's process ended without closing | `python3 -m engine state list`, then `state list --cleanup` and confirm; the run becomes `failed` and can be resumed |
| An interrupted or `waiting-external` run *(terminal)* | stopped, or waiting for a person's adjudication | `python3 -m engine state resume --run <id>` |
| You want to abort a run *(terminal)* | — | `python3 -m engine state close --run <id> --abort` |
| A private repository clone fails or stalls (menu 2) *(terminal)* | git wants credentials; the tool never answers a credential prompt | `ssh-add` (or set up an HTTPS credential helper), check with `GIT_TERMINAL_PROMPT=0 git ls-remote <url>`, then retry |
| "not an interactive terminal" inside a terminal | Windows Git Bash (mintty) | switch to PowerShell, cmd or Windows Terminal; `py -3 -m engine tty-check` confirms it |
| Privileged commands refused (`state reset`, `adjudication import`, `baseline promote`, `state close --force`) *(terminal)* | they need an interactive terminal by design | run them in your own terminal |
| Offline errors (exit 6) | the cache is missing something | run `python3 -m engine fetch --all --docs --tokenizer` once while online |
| Tokens marked "approx." | tiktoken is not installed | `python3 -m pip install -r requirements-tokens.txt`, then `python3 -m engine fetch --tokenizer` |
| Two `/analyze` entries | both the project folder and the plugin are loaded | use one install path |
| Verdicts unavailable for this version | the reproduction check (A2) has not run for 0.1 | see `CHANGELOG.md` |
| `engine slides`, `read`, `list`, `convert`, `git-log`, `git-show`, `git-ls` or `build-plugin` exits 2 "not implemented" | registered for v0.2, not built in v0.1 | see `TODO.md` |

## Limitations

- It measures specification and implementation on scenario R, not outcomes in the field. Prompt compliance depends on the model.
- **v0.1 has not yet run a real end-to-end assessment.** The pipeline is tested with simulated agents only; the first real runs (re-scoring one reference, then GSD and Ralph) and the live-session checks of the guard, setup and plugin path are v0.2.
- **Verdicts are unavailable for version 0.1 until the reproduction check (A2) is run; all comparisons are cross-round.**
- Weights are judgment; the four alternative profiles test them.
- Closed products are capped at 4 by documentation evidence.
- Integer anchors are coarse.
- Scorers are AI agents. Isolation, calibration, agreement statistics and a red team reduce, but do not remove, shared bias.
- Isolation is prompt-only outside Claude Code: other hosts do not run the guard hook.
- **U_recorded.** For references, U under the baseline profile is the value the reference round recorded. Recomputing it from the shipped scorecards reproduces 6 of 9; it differs for ai-dlc (3.8 against 3.1), bmad (2.9 against 2.7) and openspec (2.7 against 2.6).
- Runtime token consumption is not measured; T0–T3 are a static proxy. Rubric v2 §6 defines the future protocol.
- Comparisons with additional references and cross-round comparisons carry no superiority verdict.
- Self-assessments are labelled as such.
