# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-09-30

Initial pre-release. Not yet published, and not yet used on a real project.

### Added
- Plugin manifest and a single-plugin marketplace manifest in `.claude-plugin/`.
- Six skills: `sprint-spec`, `risk-tiers`, `refute-review`, `release-gate`, `handoff`, `failure-to-rule`.
- Six user-invoked commands: `sprint`, `refute`, `gate`, `checkpoint`, `resume`, `postmortem`.
- Two agents that cannot edit files: `refuting-reviewer` and `auditor` (finder and skeptic modes).
- Templates: `AGENTS.md`, `CLAUDE.starter.md`, `SPRINT.md`, `GATE.md`, `HANDOFF.md`, `FAILURE-LOG.md`.
- A worked, illustrative example with a runnable toy gate (`examples/expired-coupon`).
- `scripts/validate.py` and its self-test, plus a GitHub Actions workflow that runs both and `claude plugin validate`.
- An eval suite for `claude plugin eval` (`evals/`), and `VERIFICATION.md`, which records what was run and what was not.

### Notes
- `displayName` is deliberately absent from `plugin.json`: Claude Code 2.1.39 rejects it as an unrecognized key.
