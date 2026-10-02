---
description: Run the exact-candidate release gate on a frozen revision and report its state, never declaring ready on its own
argument-hint: "[revision (default is HEAD of a clean tree)]"
disable-model-invocation: true
---

Run the release gate for: $ARGUMENTS

Follow the `release-gate` skill and the steps in the project's `GATE.md` (template: `${CLAUDE_PLUGIN_ROOT}/templates/GATE.md`).

1. Refuse to start on a dirty tree, or without an acceptance declaration that covers every changed file. Say which.
2. Freeze: record revision, dirty flag and content hash. Take the lease on shared ports, data stores and devices.
3. Run each step once, in order, writing output and hashes to a new evidence directory. Never retry to get a pass, never skip a step, never update a baseline to clear a failure.
4. Record revision and hash again at the end. If either moved, the run is void.
5. Report exactly one state (`blocked`, `checks-passed`, `review-pending` or `partial`) with evidence paths. You may not report `ready`. That needs the independent evidence review and the finalizer.
6. List what this gate does not certify. Publish, deploy and tag nothing.
