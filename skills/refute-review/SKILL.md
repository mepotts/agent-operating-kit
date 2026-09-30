---
name: refute-review
description: Verify that an agent's work is really done by trying to refute it - re-run the checks, read the assertions, run a red-green proof, demand evidence. Use when an agent or person claims work is done, fixed, passing or ready to merge, or when asked to review, double-check, audit or independently verify a change.
---

# Refute review

Goal: find what would make "done" false. Approval is the absence of a refutation, not the presence of a summary.

Agents: `refuting-reviewer` for one change; `auditor` (finder, then skeptic) for a broad sweep. Command: `/agent-operating-kit:refute`.

## Independence
- A fresh context that is not the implementer and is told to refute, not bless.
- It reads the diff, the assertions and the direct artifacts, and re-runs the checks itself. The implementer's report is a list of claims to test, never evidence.
- A different model, extra votes or a title does not make a review independent.

## Brief
- The outcome under review; checkout path, branch and exact revision; the files it may touch.
- The claims, verbatim, marked untrusted. The acceptance checks and the risk tier.
- "Try to refute this. Report what you could not verify."
- If it is pinned to one branch, say so: a claim that needs another branch is reported unsupported, not guessed.

## What the reviewer does
1. Pin the candidate (revision, dirty flag). Review the diff, not the summary.
2. Re-run every acceptance check. Record command, exit code and counts. "Skipped" and "0 tests found" are failures until shown otherwise.
3. Read each assertion. A matching test name is not proof; an at-most check cannot show a bound got tighter.
4. **Red-green.** Revert the fix in a throwaway copy: the new test must fail. Restore it: the test must pass.
5. **Hollow gate.** Break what the gate exists to catch: it must go red. Cases generated from a directory or manifest can vanish instead of failing.
6. **Grader fault injection.** An eval or model judge earns trust only if it fails when the behavior it grades is deliberately broken.
7. Trace from the real entry point to the changed code and confirm the shipped artifact contains it.
8. Look beside the fix for the same defect shape.
9. Check scope: files touched, new dependencies, weakened assertions, regenerated baselines.

## Verdict
PASS, PASS WITH FOLLOW-UPS or FAIL; a status per claim; findings with reproduction steps; the commands run; what was not verified.

## After
- A FAIL goes back to the implementer, not to the reviewer. Re-review the new revision from scratch.
- After a batch merges, review the merged branch as a whole. Per-change reviewers attack only their own diff, so regressions live between changes.
- For a high-severity finding use two skeptics with different lenses (for example reachability from the entry point, and correctness against existing mitigations). Drop it only if both refute it. Settle disagreement by reading code or running the check, not by vote.
- For a broad audit, give each `auditor` finder a slice with no gaps and no overlaps, then run skeptics on the strongest model available.
- Depth follows the risk tier. Agent count is not a success metric.
