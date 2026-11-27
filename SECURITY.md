# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | yes |

## Report privately

Report a vulnerability, or a **leak** (a private name, a credential, an absolute home path, copied CC BY-SA text, or anything that identifies a private method, company or client) **privately**:

- Use GitHub's private vulnerability reporting: the **Security** tab of this repository, then **Report a vulnerability**.
- If that form is not available, open a public issue that says only "security contact requested", with **no details**. The maintainer will reply with a private channel.

Never paste the leaked text, a denylist term or a secret into a public issue, pull request, commit message or log. Describe a leak by file path and line only.

## What to expect

- An acknowledgement within 7 days.
- For a leak: the file is fixed on the working branch, and history is rewritten before the next release when the leak reached a published commit (see `TODO.md`, release scan).
- For a vulnerability: a fix and a `CHANGELOG.md` entry; credit if you want it.

## Scope

- **In scope:** the engine (`engine/`), the guard hook (`hooks/`), the agent briefs and skills (`.claude/`), the CI workflow and everything in the shipped `baseline/` and `docs/report/`.
- **Design limits, not vulnerabilities:** the guard is prompt-only on hosts without hooks, and a hook process that fails to start does not block (see the limitations in `README.md` and `TODO.md`).
