# Rulings v1: the common yardstick

Frozen at creation (2026-11-27). The hash is recorded in `FREEZE.md`.

These rulings were fixed by earlier audits and applied to every method. They interpret the anchors and change no anchor text.

| ID | Ruling |
|---|---|
| R-F1 | F1 = 2 only if structured elicitation runs on R's path (a feature in an existing system), not only at project creation |
| R-F8 | F8 = 2 only with explicit size or risk criteria for choosing the path |
| R-F15 | F15 = 1 when multiple lenses act only on the spec and not on the code diff |
| R-F18 | F18 = 1 when the external loop is only documented, with no shipped runner |
| R-F22 | F22 = 2 only if the record says who approved, when, and which version. The same who+when+version test applies to "recorded approvals" in C10 |
| R-F23 | F23 = 2 only if IDs link requirement → task → **test** on the default path |
| R-F33 | F33 = 2 when there is a numeric budget for artifact or hand-off size on the default path |
| R-F30/31 | Parity of boundary: an installer (F30) and CI or validation (F31) shipped **in the method's own repository** count for every method alike. Third-party or host-provided tooling does not count |
| R-A23 | A2/A3 boundary, strict: A3 requires **both** dispatch of a subagent with fresh context **and** chaining of several tasks without a human per task. The chaining may come from an external loop with a fresh session per task. Fresh-context dispatch stays mandatory |
| R-A34 | A3/A4 boundary: A4 requires the external loop to be a **shipped runner** (not only documented), with persisted state and resume |
| R-REACH | Reachability: a file reachable only through a broken reference does not count |
| R-DESC | A mechanism that is only described (no template, script, check or mandatory step on the default path) is a documentation claim, not enforcement |
| R-SCRIPT | "Verified by a script" earns credit only if the script ships in the method and the default path invokes it. Scripts are read, never run |
| R-LOW | When two levels are defensible, take the lower (methodology §1.6) |
| R-T1 | T1 excludes skill or command frontmatter carrying `disable-model-invocation: true`, because the host does not preload it |
| R-NM | For closed products, L5 is "not measurable" (`null`). It is never 0 and never "lightest" |

