@AGENTS.md

# <FILL: project name>

<FILL: one line - what this is and who it is for>

> TEMPLATE. Copy to your repo root as `CLAUDE.md`, fill every `<FILL>`, delete what does not apply, then delete this note. The first line imports AGENTS.md, so Claude Code sees the shared rules while other agents read AGENTS.md directly. Put only Claude-specific and project-specific facts here, and keep the file under 200 lines. Anything another tool must obey belongs in AGENTS.md.

## Quick start
```
<FILL: the one command that runs the project locally>
```
- Entry point: `<FILL>`
- Other services, ports, dashboards: `<FILL>`

## Stack
- `<FILL: language, framework, runtime>`
- `<FILL: data store and driver, if any>`
- `<FILL: hosting, queue, auth, and so on>`

## Module boundaries
Who owns what, so parallel agents do not collide.

| Module | Directory | Owner or lock | Notes |
|---|---|---|---|
| `<FILL>` | `<FILL>` | `<FILL>` | `<FILL>` |

Shared files (coordinate before editing): `<FILL: schema, shared types, root layout, CI, AGENTS.md, this file>`

## Data (delete if none)
- Query access: `<FILL: how to run a read-only query>`
- Migrations: local first, rehearse on a copy of production, then production; commit a rollback. `<FILL: link your playbook>`
- Production data changes need approval of the exact change. Recovery path: `<FILL: backup, point-in-time restore>`

## Verify, build, test
- Verify (must pass before merge): `<FILL: lint and constraint gate command>`
- Build: `<FILL>`  Tests: `<FILL: command and where they live>`
- Real run target (a green typecheck is not enough): `<FILL: the deploy or run path that proves it works>`

## Kit commands (if the agent-operating-kit plugin is installed)
`/agent-operating-kit:sprint` spec first · `:refute` independent review · `:gate` exact-candidate gate · `:checkpoint` and `:resume` handoffs · `:postmortem` failure to rule.

## Known gotchas
- `<FILL: third-party quirks, infrastructure limits, foot-guns future agents will trip on>`
