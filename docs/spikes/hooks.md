# Spike 0.3: hook capabilities in Claude Code

**Status: partial.** The checks that run without a live host session are done and recorded below. Every item marked **LIVE** still needs a check in an interactive Claude Code session before Phase 4 (Task 4.2, the guard) starts. No live-session result is claimed here.

- Host version seen on the maintainer machine: Claude Code `2.1.332`.
- Date: 2026-11-27.

## 1. What was verified locally

A scratch `PreToolUse` hook script (below) was run outside the host, with JSON fixtures piped to stdin. The fixtures follow the documented hook-input shape. The script appends each input to a JSONL file and denies one test command.

```python
import json, os, sys, tempfile, pathlib
raw = sys.stdin.read()
data = json.loads(raw)
out = pathlib.Path(os.environ.get("SPIKE_OUT", tempfile.gettempdir())) / "hook-dump.jsonl"
with out.open("a", encoding="utf-8") as f:
    f.write(json.dumps(data, sort_keys=True) + "\n")
if data.get("tool_name") == "Bash" and "DENYME" in data.get("tool_input", {}).get("command", ""):
    print("spike: denied by test rule", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```

| Fixture | Content | Exit | Result |
|---|---|---:|---|
| Bash, allowed | `tool_name: Bash`, `tool_input.command`, `cwd`, `session_id`, `tool_use_id` | 0 | dumped |
| Bash, denied | command contains the test token | 2 | dumped; message on stderr |
| Read with agent fields | `tool_name: Read`, `tool_input.file_path`, `agent_id`, `agent_type` | 0 | dumped |
| Not JSON | plain text | 1 | uncaught exception |

**Finding F1 (design-relevant).** An uncaught exception exits 1. In Claude Code only exit 2 blocks a call; other non-zero codes are non-blocking errors. The guard must therefore wrap its whole body, and **fail closed with exit 2** on any exception or unparsable input while a run is active. Task 4.2 adds a test for this.

**Finding F2.** The dumped input contains `cwd` and `transcript_path`, which are absolute paths. The guard must never log them into `runs/` or any shipped file. Records in this file are redacted (`<project>`, `<redacted>`).

## 2. Documented behaviour, to confirm LIVE

These rows come from the host's documentation, not from a live run.

| # | Question (plan Task 0.3) | Documented answer | Live check |
|---|---|---|---|
| 1 | Fields in `PreToolUse` input | `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`, `tool_input`, `tool_use_id` | **LIVE**: dump a real input from the main session and from a subagent |
| 2 | Agent identity in a subagent's call | recent host versions add `agent_id` and `agent_type` for calls made inside a subagent | **LIVE**: decides guard mode (a) or (b) |
| 3 | Does exit 2 block the call? | yes; stderr is fed back to the model | **LIVE**: confirm with the deny fixture command |
| 4 | Does the input carry the cwd (#68)? | yes, `cwd` | **LIVE** |
| 5 | Project-directory variable for `.claude/settings.json` hook commands | `$CLAUDE_PROJECT_DIR` | **LIVE** |
| 6 | Plugin-root variable for `hooks/hooks.json` | `${CLAUDE_PLUGIN_ROOT}` | **LIVE** |
| 7 | Do project-scoped agents and skills load on open, with no install step? | yes, `.claude/agents/` and `.claude/skills/` load from the opened project | **LIVE** |
| 8 | Does `plugin.json` accept custom component paths? | yes: `agents`, `skills`, `commands`, `hooks` path fields | **LIVE**: decides whether `build-plugin` copies are needed |
| 9 | Does an additional directory added to `.claude/settings.local.json` take effect in an open session (#70)? | not documented clearly | **LIVE**: test without and with a restart |
| 10 | Can a subagent be resumed across stages, or only re-dispatched (protocol §12)? | not settled by documentation | **LIVE**: step 6 of the task |

## 3. Decision on the guard mode

**Provisional: mode (b), global rules only. Sealing stays prompt-only.** Mode (a), per-agent sealing, is adopted only if live check 2 shows that `agent_id` or `agent_type` is present and reliable on subagent calls. The plan already treats the per-instance write scope as a residual limit when agents cannot be told apart (§4.5, #86), so mode (b) is safe to build against.

## 4. Hostile nested instructions (#40): not run

Step 5 needs the tiny-method fixture with hostile `CLAUDE.md`, `AGENTS.md` and `.claude/` files, and a live session.
- (a) data directory outside the project, attached as `engine setup` attaches it: **LIVE, not run**.
- (b) snapshot inside the project: **LIVE, not run**.

Until both are recorded, `--allow-inside-project` stays disabled (plan §0.3). If (a) loads any canary, stop and redesign before Phase 4.

## 5. Session-model check (protocol §12): not run

Step 6 (interrupt a progressive writer and re-dispatch it) needs a live session: **LIVE, not run**.

## 6. Open items

All **LIVE** rows above are listed in `TODO.md` and block Task 4.2.
