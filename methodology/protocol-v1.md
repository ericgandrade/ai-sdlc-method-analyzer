# Protocol v1: process addenda

Frozen at creation (2026-11-27). The hash is recorded in `FREEZE.md`.

These addenda are stricter than or complementary to the frozen texts. None of them relaxes a frozen rule.

1. **Lens audit at 100%.** Rubric v2 §5.6 requires a 15% sample. The tool audits **every** L2, L3 and L4 cell and every L5 list. This is stricter, so it is compatible.
2. **Calibration gate.**
   - Each L1 scorer first scores calibration reference(s) from the benchmark set. `cal_refs` is a list:
     - **implemented targets** use one reference, default `addyosmani`. It is mid-size (T0 199k), its scores are mid-range (57.6) and they spread across every level (0–5), so it discriminates leniency from harshness at moderate cost;
     - **design-only targets** use **two** references in the same round, as methodology §10.2 requires: one light (`mattpocock`) and one heavy (`bmad`), mirroring the §7.1 pilot rule.
   - The fallback order when a target is itself a calibration reference (menu 4) is `addyosmani → mattpocock → superpowers → bmad`. `engine state init` enforces `target ∉ cal_refs` and records the reason for the choice.
   - Report two deltas per scorer and reference:
     - **Δ_cal(reconciled)** = T(scorer, ref) − T(reconciled baseline, ref);
     - **Δ_cal(raw)** = T(scorer, ref) − mean T(original raw sheets, ref), using the pairs shipped in `baseline/l1.json`. This compares like with like, raw against raw.
   - Report the exact-agreement rate per cell against both.
   - Flag drift when |Δ_cal(raw)| or |Δ_cal(reconciled)| exceeds **U_ref** (the recorded ±U of that reference), or when exact agreement is below 50%. U_ref is the **single threshold** shared with the reproduction check A2 (#41).
   - Drift is **reported as sensitivity, never applied as an adjustment** (rubric §5.5). The report shows a "calibration-aligned reading", T(target) − mean Δ_cal(raw), labelled as sensitivity. Drift is also reported per model ID (§6.3).
   - An earlier isolated rescore found both isolated scorers 7–14 points harsher than the reference round on the same reference. This gate makes that visible.
3. **Reliability set.** α is computed over the pre-reconciliation ratings of the target **plus** the calibration reference(s): 32 cells for one target and one reference, 48 for design-only. Because the set is small, α is reported with a seeded bootstrap 90% interval over cells (2,000 resamples), and the report states that the set is small.
4. **Below α = 0.667.** Anchors are frozen and cannot be rewritten in a single-target run. Instead:
   - a third isolated scorer re-scores the cells that differ by 2 or more;
   - α is recomputed with the general ordinal Krippendorff α (three coders, missing values allowed; §7.3);
   - if α is still below 0.667, the target is reported as **"unreliable round"** and gets no rank. Its totals are shown only as a range from the minimum to the maximum scorer total.
5. **Red-team cadence.**
   - **Full audit of all 16 cells (methodology §10.3)** applies to a design-only target, and to a target that ranks in the **top two under baseline** among the 9 benchmarks plus the target.
   - **Every other target:** the red team contests every cell scored 4 or 5, every cell with Low confidence, and every cell that changes a rank, plus a 15% sample of the remaining cells, drawn with a seed recorded in `state.json`.
   - Every contest is logged, including the rejected ones.
6. **Single-assessor documentation-only runs** never enter the ranking as a point. They are reported as floor, centre and ceiling with positions.
7. **Seeds.** Every stochastic step uses a seed stored in `state.json`. The default seed is the run date as an integer, `YYYYMMDD`.
8. **Benchmark set and additional references.**
   - S1–S5, medians and best values use only the 9 references frozen with methodology v1.0 (`benchmark: true`), because the methodology header names that set.
   - Additional references are ranked and profiled but never enter the verdict set until a new methodology version re-freezes the set.
9. **Same-round versus cross-round (#41).** A run is **same-round** only if **both** of these hold:
   - (a) `baseline/rounds/<current>/reproduction.json` records an A2 pass within ±U for this pipeline version;
   - (b) **this run's own** `calibration.json` shows no drift under the U_ref threshold for every scorer and every calibration reference.

   Otherwise the run is **cross-round**: every target-versus-baseline comparison is labelled "cross-round" and carries **no superiority verdict**. The A2 fail branch (§13) re-scores the benchmarks in a new round. `state.json` records `round_id = <pipeline-version>+<baseline-round>`, and `results.json` carries `comparison` and `round_id`.
10. **Adjudicator.**
    - Contests marked `to-adjudicator` go to an adjudicator, as methodology §10.2 requires. The adjudicator is either a fresh agent that scored, audited and reconciled nothing in the run, or a named person who is not the method's owner.
    - Owners may answer factual questions in writing. Their answers are recorded in `runs/<id>/owner-answers.md` through `engine answers add --run <id> --request run:requests/log/answer.json` (#85). That file is engine-owned and append-only, and owners never adjudicate.
11. **Self-assessment.** When the user declares that they own or authored the target (menu question), or the intake detects it, the report labels the target **"self-assessment"**. The owner still never adjudicates.
12. **Session model for scorers.** One dispatch per scorer covers calibration and target, written progressively with section markers. A restart re-dispatches the same brief, which resumes after the last marker in each file.
13. **Interpretation I-2.**
    - Methodology §9 reads "S2 fails for at most one profile **or** S3 falls short" for *Conditionally superior*.
    - The engine implements: S2 failures ≤ 1, **and** at least one of S2 or S3 not fully passing.
    - Both readings are implemented behind `--interpretation strict|literal` (default `strict`; owner decision D6). Each has its own test.
14. **Lenses for design-only targets (#44).** Rubric v2 is silent on designs, so this addendum fixes the treatment:
    - L3 and L4 are assessed on the design, under the methodology §8.1 concreteness test, and carry `basis: "design"`.
    - L2 follows L1 (D-based, then RA).
    - L5 is `null` with `reason: "not measurable (design)"`.
    - Design-basis values are never shown in the same matrix column as implemented values without a "design" mark.
15. **Blind r (#45).** For design-only targets, the red team first receives `reconciled-blind.json`, which has no r, and writes `r_independent.json`. Only then does the engine release the full `reconciled.json` to it (stages S07r and S07).
16. **Verdict set (#47).** The S3 inputs (P(first) and leave-one-out) for a target's verdict are computed over the 9 benchmarks plus that target only. Display sensitivity, which may include additional references and other targets, never feeds a verdict.
17. **Interpretation I-1: "Conditionally superior" requires S5.**
    - Methodology §9 lists S1, S4, S6 and S7 for *Conditionally superior*.
    - The `strict` interpretation (the default, owner decision D6) also requires S5, because the verdict must not hold while "best in class" fails.
    - The `literal` interpretation reads the methodology text as written and does not require S5.
    - When S5 alone fails and every other condition passes, `literal` gives "Conditionally superior", while `strict` gives "Comparable" or "Not superior", according to the margin.
    - Interpretations I-1 and I-2 (item 13) are both implemented behind `--interpretation strict|literal`. `superiority.json` and the report state which reading produced the verdict, and every failed condition is listed, as methodology §9 requires.
