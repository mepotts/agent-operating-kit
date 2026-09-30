---
description: 'A request to independently verify an agent''s claim should load the refute-review skill.'
tags: [skill, trigger]
max_turns: 12
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Another agent just told me the retry-logic bug is fixed and all the tests pass. I do not fully trust that. How should I verify it independently before I merge?
