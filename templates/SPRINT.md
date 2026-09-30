# Sprint: <slug> - <one-line title>

> TEMPLATE. Copy to the spec path named in AGENTS.md (default `sprints/<slug>.md`). Fill every field, delete guidance lines, keep it under two pages. No code before the outcome and risk tier are agreed.

**Status:** draft | approved | in progress | in review | gated | merged
**Owner (human):** `<name>`  **Implementer:** `<agent or session>`  **Reviewer:** `<a different agent or a human>`
**Risk tier:** `<0-4>` because `<what the change can touch>` (the highest tier touched wins)

## Outcome
`<One to three sentences of observable behavior. Not "improve X"; what a user or caller sees.>`

**Out of scope:** `<what this deliberately does not do>`

## Files
| Path | Access | Note |
|---|---|---|
| `<path>` | owned | `<who may write it>` |
| `<path>` | shared, coordinate first | `<schema, shared types, CI, AGENTS.md>` |
| `<path>` | forbidden | `<why>` |

One writer per file across parallel work.

## Acceptance
Write "done" as checks. If a criterion cannot fail, rewrite it.

| ID | Observable outcome | Executable check (exact command or test title) | A pass proves |
|---|---|---|---|
| c1 | `<outcome, including cancel, error and persistence where relevant>` | `<command>` or `<file>::<title>` | `<what>` |

**End-to-end check on the real run target:** `<command>` should show `<result>`

**Pending criteria** (runtime proof not possible yet): `<id and reason>`. A mock never closes a runtime criterion.

## Isolation
- Worktree and branch: `<path>` / `<branch>`
- Data target: `<explicit; verify by count, not by trusting config>`. No production credentials in the workspace.
- Ports and shared resources, and who holds the lease: `<reserved>`

## Workstreams
| Stream | Owner | Model and effort | Why |
|---|---|---|---|
| `<name>` | `<agent>` | `<model / effort>` | `<one line>` |

## Stop and report if
- Unrecognized files or branches appear in scope
- A migration fails partway, or a response has an unfamiliar shape
- Errors exist that you did not cause
- A check cannot be run (report it as unavailable, never as passed)

## Irreversible actions this may need
`<List each. Every one needs approval of the exact change, showing the command or diff. "None" is a valid answer.>`

## Done means
- [ ] Every acceptance check ran, was not skipped, and passed (commands, output and exit codes pasted below)
- [ ] Independent refuting review: `<PASS | PASS WITH FOLLOW-UPS>` on revision `<sha>`
- [ ] Gate state for revision `<sha>`: `<state>`
- [ ] No files touched outside the table above

---

## Implementer report
Fill at the end, in this order.
1. What I did, per outcome
2. Decisions I made where the spec left a choice
3. What I deferred, stubbed or skipped, and why
4. Verification: each command, its output, its exit code
5. New dependencies, and files outside the table
6. Anything surprising

## Reviewer verdict
Filled by the reviewer, never the implementer.
