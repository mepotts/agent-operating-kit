---
name: sprint-spec
description: Write a sprint spec before any code - outcome, file boundaries, risk tier, acceptance checks, isolation. Use when the user wants to plan, scope or spec work for an AI coding agent, asks for a definition of done or acceptance criteria, or is about to start a feature, fix, refactor or migration.
---

# Sprint spec

Specify before code. A spec is finished when someone who did not write it could tell, from files alone, whether the work is done.

Template: `${CLAUDE_PLUGIN_ROOT}/templates/SPRINT.md`. Command: `/agent-operating-kit:sprint`. Tiers: the `risk-tiers` skill.

## Checklist
1. **Outcome.** One to three sentences of observable behavior, plus what is out of scope.
2. **Risk tier (0-4).** The highest tier touched wins. It sets review depth and who signs off.
3. **File boundaries.** Owned paths; shared files that need coordination (schemas, shared types, CI, `AGENTS.md`); forbidden paths. One writer per file across parallel work.
4. **Acceptance.** For each outcome, an executable check named exactly (a command or a test title) and what it must show. Cover error, cancel and persistence states where they apply. Add the end-to-end check on the real run target, not only a typecheck.
5. **Pending criteria.** If runtime proof is not possible yet, list it as pending with a reason. A mock never closes a runtime criterion.
6. **Isolation.** Own worktree and branch; the data target set explicitly (production credentials never in a workspace); ports and shared resources reserved.
7. **Roles and effort.** Who implements and who reviews (never the same agent). Model and effort per workstream, with a one-line reason.
8. **Stop conditions.** Unrecognized files or branches, partial failures, unfamiliar response shapes, errors you did not cause: stop and report.
9. **Approvals.** List every irreversible action the work might need. Each needs approval of the exact change.

## Rules
- No code before the outcome and the tier are agreed.
- "Done" is written as checks, not adjectives. If a criterion cannot fail, rewrite it.
- Keep it under two pages. Link depth instead of pasting it.
- Save it at the spec path named in the project's `AGENTS.md` (default `sprints/<slug>.md`), then stop and ask the human to confirm outcome and tier.
