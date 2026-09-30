---
description: Draft a sprint spec (outcome, file boundaries, risk tier, acceptance checks) before any code is written
argument-hint: "<what to build or change>"
disable-model-invocation: true
---

Draft a sprint spec for: $ARGUMENTS

1. Read the repo's `AGENTS.md` and `CLAUDE.md` if they exist, for the verify command, the shared files, the tiers in force and the spec path.
2. Follow the `sprint-spec` skill and classify the risk with the `risk-tiers` skill.
3. Fill in `${CLAUDE_PLUGIN_ROOT}/templates/SPRINT.md` and save it at the spec path from `AGENTS.md` (default `sprints/<slug>.md`).
4. Write no product code. Show the spec, name the three things you are least sure about, and stop so the human can confirm the outcome and the risk tier.
