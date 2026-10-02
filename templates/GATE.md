# Release gate: <project or release name>

> TEMPLATE. Copy to the gate path named in AGENTS.md, fill every `<...>`, delete guidance. A gate is a deterministic check that passes or fails without a person. It publishes nothing. It produces evidence that a person or release process can rely on.

**Principle.** Readiness belongs to one exact candidate: a source revision and the artifacts built from it. "Implemented", "tested", "deployed", "enabled" and "healthy" are separate claims. Any source change after a run voids it. Missing evidence on a new machine means unavailable, not passed.

## 1. Candidate
Frozen before the first step.

| Field | Value |
|---|---|
| Revision | `<full sha>` |
| Dirty flag | `<no>` |
| Content hash | `<sha256 of tracked files, line endings normalized>` |
| Built artifacts | `<path>: <sha256>` |
| Platforms in scope | `<list: anything not listed is not certified>` |
| Comparison base | `<sha>` |

## 2. Acceptance declaration
Written before coding, one small file per change. It covers every changed product path, including deletions. The runner refuses a change whose files it does not cover. Each excluded platform needs a written reason, and a change may not exclude all of them.

```json
{
  "id": "<change-slug>",
  "files": ["<every changed product path>"],
  "criteria": [
    {
      "id": "c1",
      "intent": "<observable outcome, including cancel, error and persistence>",
      "checks": { "<platform>": [{ "file": "<test file>", "title": "<exact test title>" }] },
      "notApplicable": { "<platform>": "<why>" }
    }
  ],
  "pendingCriteria": [{ "id": "p1", "reason": "<why runtime proof is not possible yet>" }]
}
```

Pending means pending: a mock or an offline pass never closes a runtime criterion. A matching test name is not proof. The reviewer reads the assertions.

## 3. Steps
Run in order on the frozen candidate. Each must pass exactly once.

| # | Step | Passes when | Command |
|---|---|---|---|
| 1 | Gate self-test | Every rule fires on its failing fixture and stays silent on its passing one | `<cmd>` |
| 2 | Lint rules | Zero violations | `<cmd>` |
| 3 | Typecheck or static analysis | Zero errors | `<cmd>` |
| 4 | Build and smoke test | Built from the frozen source, smoke-tested against a disposable fixture data store, artifact hash recorded | `<cmd>` |
| 5 | Journeys or integration | Every declared check passed once: nothing skipped, retried, focused or flaky | `<cmd>` |
| 6 | Acceptance evidence | Every criterion's named checks appear in the results as passed | `<cmd>` |
| 7 | Source stability | Revision, dirty flag and content hash identical before and after | `<cmd>` |

## 4. What blocks
- Any skip, retry, focused test, expected failure or flaky pass. Declared skips are allow-listed by exact file, title and criterion id.
- Zero tests found.
- Capture-only or single-platform runs when more are required.
- Stale artifacts, or a source change mid-run.
- A snapshot or image baseline updated to clear a failure. Baseline changes are deliberate, reviewed, and committed with the reason.

## 5. Evidence
One private directory per run, `<path>/<timestamp>-<sha8>/`: a report (source, steps, results, limitations), raw logs, and every captured artifact with its SHA-256. Blocked runs are retained. Never overwrite them or relabel them as passes.

## 6. Independent evidence review
Use at least `<3>` reviewers, each in a fresh context. Split the evidence into contiguous slices with no gaps and no overlaps. Each reviewer recomputes every hash, then grades `<what matters for your product>`. Also report evidence quality: byte-identical captures under different names, captures taken mid-transition, mislabeled files. The review file records reviewer, verdict, notes, limitations and the item list, all bound to the report's hash.

## 7. Finalize
A separate step re-derives everything from files: source unchanged, evidence hashes matching, review bound to this report and covering every item. Only then may it print ready, and only for the platforms covered.

| State | Meaning |
|---|---|
| `blocked` | A step failed or the run was invalidated |
| `checks-passed` | Every step passed, no independent review yet |
| `review-pending` | Review missing, unbound or incomplete |
| `partial` | Not all required platforms ran |
| `ready` | The finalizer verified everything, for the covered platforms |

The runner can end a run as `checks-passed` at most. It never says ready itself.

## 8. Shared resource lease
Ports, fixture data stores and devices sit behind an exclusive-create lock that names the owner. Release verifies ownership. Recover only when the owner is provably dead on this host. A stale-looking timestamp is not proof. Refuse to start rather than share.

## 9. Repair loop
- Preserve the failing run and classify it: product assertion, fixture or setup, missing evidence, visual defect, infrastructure.
- Reproduce a product defect with an assertion before fixing it. Never weaken an assertion to pass.
- A wait can delay a failure, never convert one. After several distinct timing races, question the time budget.
- A failure that appears only when a phase runs alone is a real defect until disproven.
- Stop after three attempts on the same failure and report the evidence and the blocker.
- New source is a new candidate and a new run. Do not combine partial or historical runs.

## 10. Limits
This gate does not certify: `<other platforms, store signing, the production network, deployment, live health>`. A local pass is not permission to publish. Publishing stays a per-change human decision.
