---
description: Write or refresh HANDOFF.md so a fresh agent or another vendor can resume this work cold
argument-hint: "[why you are stopping, for example \"usage limit resets at 14:00\"]"
disable-model-invocation: true
---

Persist the state of this work now. Reason for stopping: $ARGUMENTS

Follow the `handoff` skill and fill `HANDOFF.md` from `${CLAUDE_PLUGIN_ROOT}/templates/HANDOFF.md`.

1. Take facts from the repository, not from memory: `git status`, `git log`, the worktree list, the newest run or evidence directories.
2. Record only commands you actually ran and their real results. Label hypotheses as hypotheses. Report unavailable proof as unavailable.
3. Copy the previous `HANDOFF.md` to a dated sibling before overwriting it. Keep the live file out of version control unless the project says otherwise.
4. List shared resources you hold (ports, data stores, devices) and either release them or record the lease with owner and ports.
5. End by printing the single next action and any blocker that needs a human.
