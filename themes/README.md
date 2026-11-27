# Themes

A theme is a CSS file that **only sets custom properties**. The report layout is built in to
`engine/report_html.py` and reads nothing but these tokens, so a theme changes colours and fonts and
nothing else. Use one with `python -m engine report … --theme <file>`; the default is `themes/neutral.css`.

## Allowed structure

- `:root { … }` blocks.
- `@media (prefers-color-scheme: …) { :root { … } }` blocks.
- Only `--name: value;` declarations inside them. Comments are allowed.

## Required tokens

`--ink`, `--ink-soft`, `--ink-faint`, `--paper`, `--wash`, `--accent`, `--accent-2`, `--pos`, `--neg`,
`--rule`, `--rule-soft`, `--font`, `--mono`.

## Forbidden

`url(`, `@import`, `@font-face`, `http`, `expression(` and the backslash `\`. Any other selector or
at-rule is refused. The validator exits 1 and prints the offending line.

## Contrast

`tests/test_theme.py` checks the neutral theme against WCAG 2 contrast ratios in light and dark:
ink, ink-soft and ink on wash against paper, and paper on ink (table headers), at least 4.5; ink-faint
at least 3.0. Check a new theme the same way before sharing a report built with it.
