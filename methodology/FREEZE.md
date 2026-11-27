# Freeze record

| File | SHA-256 | Frozen | Normative |
|---|---|---|---|
| methodology-v1.0.md | a6e3953725b67db0189e188c1495ee9b54975e48f65c28baaa01f459b69cf9a4 | 2026-11-20 | yes |
| evaluator-agent-v1.0.md | aa3a1f7072ac9200c08135e2f2f773226268870973fc7b908e793a972c31857a | 2026-11-20 | yes |
| rubric-v2.0.pt.md | 8d5b63ea22847d44bb2f60a8fb9f55f7f87d30d68af6cac76d79bebd51057b84 | 2026-11-26 | yes |

Rules
1. A frozen file never changes. A change is a new version (new file name, new hash) and invalidates comparison with every result scored under the old version, so the baseline must be re-scored under the new version before it can be compared.
2. Every run records the hashes it used in runs/<id>/state.json; `engine verify-freeze` (exit 4 on mismatch) runs as stage S00 of every pipeline and in CI.
3. PATHMAP.md, themes, templates and agent briefs are not frozen, but a brief change that alters scoring behaviour bumps the plugin **minor** version and is listed in CHANGELOG.md. Fixes that cannot change any score or verdict (docs, report layout, bug fixes covered by unchanged goldens) bump the **patch** version only. Reproduction records match on **major.minor** (#62).
