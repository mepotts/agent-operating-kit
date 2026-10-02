---
description: Resume unfinished work from HANDOFF.md as a fresh agent, verifying before trusting
argument-hint: "[path to the checkpoint (default is ./HANDOFF.md)]"
disable-model-invocation: true
---

Resume the work described by: $ARGUMENTS (default `HANDOFF.md`).

Follow the resume steps of the `handoff` skill.

1. Read the checkpoint, copy it to a dated sibling, then write your own identity and plan into the live file.
2. Confirm the previous session actually stopped: processes, containers, lock files, run directories. A stale timestamp is not proof. When unsure, treat the lease as live and stop.
3. Reconstruct from durable sources first (worktrees, the checkpoint's next action, the work record and evidence, the newest run directories) and from transcripts last.
4. Do not rerun an expensive gate on an unchanged frozen candidate. Confirm the revision and reuse its evidence.
5. Approval boundaries do not change with the agent: no push, no merge to main, no production change, no publishing without the human.
6. Report what you verified, what you could not verify, and the first action you will take. If a blocker needs a human, stop there.
