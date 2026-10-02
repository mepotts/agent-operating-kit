---
name: release-gate
description: Run an exact-candidate release gate (freeze one source revision, run the declared checks once each, keep hashed evidence, get an independent evidence review, and only then call it ready). Use when asked whether something is ready to release or ship, to freeze a candidate, or to set up or run a release gate.
---

# Exact-candidate release gate

Readiness belongs to one exact candidate: a source revision plus the artifacts built from it. "Implemented", "tested", "deployed", "enabled" and "healthy" are separate claims. The gate produces evidence. It publishes nothing, and a local pass is not permission to publish.

Template (declaration schema, step table, state table): `${CLAUDE_PLUGIN_ROOT}/templates/GATE.md`. Command: `/agent-operating-kit:gate`.

Asked a general question with no candidate in scope: answer from the sequence and the blocker list below. Do not go looking for a repository to gate. Use the command when there is one.

## Sequence
1. **Declare before coding.** List every changed product path and, per outcome, the named executable checks per platform, with a written reason for each exclusion. The runner refuses a change whose files are not covered.
2. **Freeze.** Record revision, dirty flag and content hash. Refuse a dirty tree. Take a lease on shared ports, data stores and devices. Refuse to start rather than share.
3. **Run the steps in order, each passing exactly once.** Gate self-test first: every rule must fire on its failing fixture and stay quiet on its passing one.
4. **Keep evidence.** One private directory per run with the report, raw logs, and every artifact with its SHA-256. Keep blocked runs. Never overwrite or relabel them.
5. **Re-check stability.** Revision and hash unchanged at the end, or the run is void.
6. **Review independently**, in fresh contexts. Partition the evidence with no gaps or overlaps, recompute every hash, grade what matters, and report evidence quality (byte-identical captures under different names, mislabeled files).
7. **Finalize separately.** A step that re-derives everything from files decides `ready`, and only for the platforms covered.

## What blocks
Skips, retries, focused tests, expected failures, flaky passes, zero tests found, stale artifacts, a source change mid-run, capture-only or partial-platform runs, and a baseline updated to clear a failure.

## States
`blocked`, `checks-passed`, `review-pending`, `partial`, `ready`. The runner can reach `checks-passed` at most. It never declares ready itself.

## Repair loop
Classify the failure. Reproduce a product defect with an assertion before fixing it. Never weaken an assertion. A wait can delay a failure but not convert one. A failure that appears only when a phase runs alone is a defect until disproven. Stop after three attempts on the same failure and report. New source is a new candidate and a new run.

## State the limits
List what the gate does not certify: other platforms, signing, the production network, deployment, live health.
