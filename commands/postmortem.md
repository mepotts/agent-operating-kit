---
description: Turn a failure into a logged incident and a mechanical guardrail
argument-hint: "<what went wrong>"
disable-model-invocation: true
---

Run a postmortem on: $ARGUMENTS

Follow the `failure-to-rule` skill.

1. Reconstruct what happened from evidence (diff, logs, transcript excerpts), not from the agent's own account.
2. Append an entry to `FAILURE-LOG.md` (template: `${CLAUDE_PLUGIN_ROOT}/templates/FAILURE-LOG.md`).
3. Propose the strongest guardrail that fits (gate, guard, template field, instruction line) and show the exact diff. Do not change shared files such as `AGENTS.md` or CI config without approval.
4. For a new check, write a failing fixture and a passing fixture, run both, and show the check going red on the failing one.
5. Search for twins of the defect shape and list what you found.
