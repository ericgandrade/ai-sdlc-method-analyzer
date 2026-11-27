"""Constants of methodology v1.0 and rubric v2.0 (plan §7.2)."""

CRITERIA = [f"C{i}" for i in range(1, 17)]
CRITERION_NAMES = ["Ease of adoption", "Requirements and specification", "Code quality practices",
    "Verification and evidence", "Code review rigor", "Loop engineering", "Graph engineering",
    "Autonomous execution safety", "Traceability end to end", "Human governance", "Security by default",
    "Release and operations", "Context engineering and token efficiency", "Right-sizing and brownfield",
    "Portability and extensibility", "Learning loop and measured outcomes"]
PROFILES = {  # methodology-v1.0 §5.1 and §5.3
    "baseline":   [6, 8, 9, 9, 8, 7, 4, 6, 5, 6, 6, 6, 6, 6, 4, 4],
    "equal":      [6.25] * 16,
    "startup":    [12, 6, 10, 8, 6, 7, 4, 8, 2, 2, 4, 5, 8, 10, 6, 2],
    "regulated":  [3, 10, 7, 10, 9, 5, 2, 5, 10, 11, 9, 7, 3, 4, 1, 4],
    "autonomous": [4, 6, 7, 9, 8, 11, 9, 11, 4, 4, 5, 4, 9, 4, 3, 2],
}
CORE = ["C2", "C3", "C4", "C5", "C6"]
FEATURES = [f"F{i}" for i in range(1, 35)]
FEATURE_NAMES = ["Structured elicitation", "Spec template with testable acceptance criteria",
    "Independent spec critique", "Spec change control", "Task decomposition with explicit dependencies",
    "Decision records (ADR)", "Existing-code mapping (brownfield)", "Routing by size or risk", "Test-first",
    "Systematic debugging", "Role-specialised agents", "Subagents with isolated context and brief",
    "Verification gate with fresh command evidence", "Review by a context independent of the author",
    "Multiple review lenses with consolidation", "Security review or threat modelling",
    "Iteration loop with numeric bound and action", "Multi-session execution without a human between tasks",
    "Execution isolation (branch, worktree, sandbox)", "Persisted state and resume",
    "Environment-enforced limits (hooks, permissions, sandbox)", "Recorded human approvals (who, when, version)",
    "Traceable IDs requirement→task→test", "Exportable or tool-checked audit trail", "Release with rollback",
    "Incident and postmortem", "Retrospective that changes the environment", "Cross-session memory",
    "Official support for 3+ agent platforms", "Versioned installer and update",
    "Automatic validation of the method itself", "Token or cost telemetry", "Context or artifact size budget",
    "Evals that measure the method's behaviour"]
GROUPS = {"Discovery": range(1, 5), "Design": range(5, 9), "Construction": range(9, 13),
          "Verification": range(13, 17), "Autonomy": range(17, 22), "Governance": range(22, 25),
          "Operations": range(25, 29), "Ecosystem": range(29, 32), "Economy": range(32, 35)}
LEVELS = ["A0", "A1", "A2", "A3", "A4", "A5"]
U_CONF = {"H": 0.25, "M": 0.5, "L": 1.0}
CONF_ORDER = "HML"           # worse = later
EXIT_OK, EXIT_GATE, EXIT_USAGE, EXIT_MISSING, EXIT_INTEGRITY, EXIT_LEAK, EXIT_OFFLINE = 0, 1, 2, 3, 4, 5, 6
