# Fairness

1. Every method gets the same procedure, the same output contract, the same scenario R and the same rulings (`rulings-v1.md`).
2. Evidence is by file. Marketing, roadmaps, open pull requests and "coming soon" do not count.
3. When in doubt, take the lower level and the lower confidence.
4. Scorers never see totals, other scorers' sheets, the requester's hypothesis, or prior scores of the target, including a self-assessment shipped inside the target's repository. The intake strips known self-score files into `OFF_LIMITS`.
5. Calibration differences are shown as sensitivity and never applied.
6. A method designed explicitly against this rubric is at risk of credit for anchor-matching text that is not enforced. The red team must test every level 4 and 5 claim for: on the default path, shipped and reachable, and enforced as the anchor requires.
7. No ranking or evaluation of individual people. Origins are organisations or authors as stated in LICENSE or README.
8. **Boundary exclusions are disclosed and contestable.** The user confirms the method boundary at intake, but every exclusion is logged with its reason in `boundary.md`. The red team contests the exclusion of any shipped file that lies on R's path. The report lists the excluded directories (in the report's excluded-directories section).
9. **Self-assessment label.** When the user owns or authored the target, the report labels it "self-assessment" (protocol §11), and the owner never adjudicates (protocol §10).
10. **Comparison set.** Verdicts are computed against the 9 frozen benchmarks only. Additional references are context (protocol §8). Cross-round comparisons carry no verdict (protocol §9).
