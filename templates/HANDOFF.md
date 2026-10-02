# Handoff checkpoint

> TEMPLATE. Keep the live file out of version control (it holds machine-local paths and session ids) unless your project decides otherwise. It points at the canonical work record. It is neither a permanent lock nor a second task queue. Before overwriting, copy the previous version to `HANDOFF.<date>.md`.

| Field | Value |
|---|---|
| Coordinator | `<vendor:session-id>` |
| Updated | `<ISO time>` |
| Status | `<one line>` |
| Checkout / branch / revision | `<absolute path>` / `<branch>` / `<sha>` |
| Frozen candidate | `<sha, or none>` |
| Resume trigger | `<usage-limit reset time, or the event to wait for>` |

## Objective and acceptance
`<What is being built and the checks that say it is done. Link the spec.>`

## State
- Completed commits: `<sha: subject>`
- Uncommitted files and who owns them: `<path: owner>`
- Lanes: `<lane: session, worktree, branch, head>`
- Shared resources (ports, data stores, devices): `<resource: owner, range>`

## Verified so far
`<Each command run, its result, the evidence path or hash, and the platform limits. Only what was actually run.>`

## Failed approaches
`<What was tried and the diagnosed cause. Label hypotheses as hypotheses.>`

## Next action
`<One concrete step.>`

## Blockers and pending approvals
`<What needs a human decision or approval, from whom, since when.>`

## Obligations that outlive local completion
`<Observing a release, recovery, follow-ups: who carries each and what triggers it. A local pass does not close live health.>`

---

## Resume checklist (for the incoming agent)
1. Copy this file to a dated sibling, then write your own identity and plan into the live file.
2. Confirm the other session actually stopped: processes, containers, lock files, run directories, the last record of its transcript. A stale timestamp is not proof. A recorded run-ended event is. When unsure, treat the lease as live.
3. Reconstruct from the most durable source first: worktrees (ahead, behind, dirty), this file's next action, the work record and evidence, the newest run directories. Transcripts fill gaps. They do not outrank durable records.
4. Do not rerun a completed expensive gate on an unchanged frozen candidate. Confirm the revision and reuse its proof.
5. One integration coordinator at a time. Approval boundaries (no push, no merge to main, no production change, no publishing) do not change with the coordinator.
6. Say who you are, what you verified, and what you will do first.
