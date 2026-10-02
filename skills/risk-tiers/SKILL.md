---
name: risk-tiers
description: Pick how much review a change needs by risk tier 0 to 4 (docs, feature code, schema or shared state, production data or irreversible actions, security surface). Use when asked how much review, testing or sign-off a change needs, or before merging anything that touches migrations, auth, deletes, publishing, spending or user data.
---

# Risk tiers

Verification depth matches risk. Classify by what the change can touch, not by how big it is. When a change spans tiers, the highest applies. When unsure, take the higher tier.

| Tier | Change | Required before merge | Human sign-off |
|---|---|---|---|
| 0 | Docs, copy, non-behavioral | Self-check, build and typecheck | Spot-check |
| 1 | Feature code: no schema, no production data | One independent refuting review, the lint gate, tests that ran (not skipped) | Integrator merges |
| 2 | Schema, persistent, shared or client-shipped state | Tier 1, plus a forward and rollback round trip on production-shaped data, a rehearsal against a copy of production, a committed rollback | Explicit yes before production |
| 3 | Production data writes, destructive actions, publishing, spending | Tier 2, plus the exact command or diff, a logged read-only count of what it touches, a known recovery path | Per-change approval by the human, never delegated |
| 4 | Security surface: auth, uploads, callbacks, parsing, permissions, privacy | The change's own tier, plus a review briefed with a threat model | Security review |

## How to classify
1. List what the change can touch: files, schema, stored data, shared state, credentials, users, money, published artifacts.
2. Take the highest matching tier. A "small dry run" that writes one row is a write.
3. Add your domain's top-risk row. Library or SDK: a public API break is Tier 3. Research or ML: a change that affects evaluation gates on a metric threshold on held-out data. Client-shipped state has no rollback after ship, so go forward-only, keep a kill switch, and treat it as Tier 2 at least.
4. Re-tier when scope grows. Record the tier and the reason in the spec.

## Rules
- Do not audit a copy change like a migration. Never ship a production-data change on one pass.
- Reviewers get capability that matches the tier: the strongest model and higher effort for Tier 2 and up, security, and ambiguous cross-cutting work, cheaper models for mechanical work.
- Tier 3 approval is per change and never delegated: show the exact command or diff and the read-only count of what it touches.
- To run the review, use the `refute-review` skill or `/agent-operating-kit:refute`.

Answer as: "Tier N because <what it can touch>. Required: <checks>. Sign-off: <who>."
