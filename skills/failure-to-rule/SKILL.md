---
name: failure-to-rule
description: Turn an agent failure into a mechanical guardrail instead of 'be more careful' - log the incident, find the mechanism, add a check that fails and states the fix, and prove it goes red. Use after an agent makes a mistake or a bug ships, or when asked how to stop something recurring, run a postmortem, or add a rule or lint.
---

# Failure to rule

"Be more careful" is not a fix. Each failure becomes a mechanism that makes the same mistake fail loudly next time.

Template: `${CLAUDE_PLUGIN_ROOT}/templates/FAILURE-LOG.md`. Command: `/agent-operating-kit:postmortem`.

If the incident is only described, with no repository, logs or diff at hand, work from the description: say what you could not verify, and give the guardrail as a design the user can adopt, including how to prove it goes red on a failing fixture and the `FAILURE-LOG.md` entry to record.

## Steps
1. **Reconstruct from evidence** (diff, logs, transcript excerpts), not from the agent's account of itself. Note how late it was detected.
2. **Find the mechanism.** Why did the process allow this? Not who did it.
3. **Pick the strongest guardrail that fits**, in this order: (a) a deterministic check in the verify or gate command; (b) a hard guard, such as a permission deny rule or a script that refuses by default; (c) a required field in a template that forces the evidence; (d) one line in `AGENTS.md`.
4. **Build it with two fixtures**: one that must fail and one that must pass. The failure message states the fix.
5. **Break it, confirm red.** Show the check going red on the failing fixture. A gate with no observed red is unproven. Suites generated from a directory or manifest can go silent when the target disappears, so drive cases from live discovery plus a committed snapshot, and never regenerate the snapshot to silence a failure.
6. **Search for twins**: the same defect shape nearby, such as duplicate implementations, sibling call sites, or the same guard at a small size. Fix or log each.
7. **Log it** in `FAILURE-LOG.md`: mechanism, guardrail, where it lives, the break-it proof, twins found, a review date.
8. **Keep `AGENTS.md` short.** Add a line only if removing it would cause a mistake. After review, merge or delete rules that no longer earn their place.

## Never
- Weaken or skip a gate to get a candidate through.
- Regenerate a snapshot or a baseline to silence a failure.
- Count rules as progress. Count failures that can no longer recur.
- Change shared files (`AGENTS.md`, CI config) without the owner's approval. Propose the diff.
