---
description: A request to stop a failure recurring should load the failure-to-rule skill.
tags: [skill, trigger]
max_turns: 12
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

An agent deleted a failing test to get CI green and nobody noticed for two weeks. What should we change so that cannot happen again?
