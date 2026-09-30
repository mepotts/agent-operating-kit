---
description: A request to plan work before coding should load the sprint-spec skill.
tags: [skill, trigger]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

We need to add per-user rate limiting to our public API. It is a small Node service: routes live in src/routes/, shared middleware in src/middleware/, and tests run with npm test. Before anyone writes code, help me write down exactly what we are building, which files the agent may touch, how risky it is, and how we will know it is done.
