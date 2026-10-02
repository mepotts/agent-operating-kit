---
description: Get an independent reviewer to try to refute a claim that work is done
argument-hint: "[branch, commit or path (default is the current diff)]"
disable-model-invocation: true
---

Independently review: $ARGUMENTS (if that is empty, review the current branch's diff against its base).

1. Pin the candidate with read-only git: checkout path, branch, revision, dirty flag, merge base.
2. Collect the implementer's claims and the spec's acceptance checks, and note the risk tier.
3. Delegate to the `agent-operating-kit:refuting-reviewer` subagent with the brief described in the `refute-review` skill. Quote the claims verbatim and mark them untrusted. Do not add your own opinion on whether the work is good.
4. Return the reviewer's verdict, findings and "not verified" list unchanged. If the verdict is FAIL, do not fix the code in this step. Hand the findings to the implementer.
5. If this session wrote the code under review, say so in the brief.
