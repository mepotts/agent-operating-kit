# Failure log

> TEMPLATE. One entry per incident that taught something, newest first. The goal is a mechanical guardrail for each entry, not a story. An entry with no guardrail yet stays open.

| Date | Failure (short) | Guardrail (type and path) | Status |
|---|---|---|---|
| `<YYYY-MM-DD>` | `<title>` | `<gate, guard, template field or instruction>`: `<path>` | open or closed |

## Entry template

### `<YYYY-MM-DD>` - `<short title>`
- **What happened:** `<observable facts; no blame>`
- **How it was detected:** `<who or what noticed, and how late>`
- **Blast radius:** `<what it touched, and what it could have touched>`
- **Mechanism:** `<why the process allowed it, not who did it>`
- **Guardrail:** `<the strongest that fits: deterministic gate, hard guard, template field, instruction line>`; lives in `<path>`
- **What the check prints:** `<it must state the fix>`
- **Break-it proof:** `<the command that turns the guardrail red on a failing fixture, and what you observed>`
- **Twins searched:** `<query, hits, what was done>`
- **Rule text, if a line went into AGENTS.md:** `<one line>`
- **Review date:** `<when to ask whether this rule still earns its place>`
