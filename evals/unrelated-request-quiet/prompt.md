---
description: Negative control. An ordinary small edit must not load any kit skill.
tags: [skill, negative]
max_turns: 6
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Rename the variable usr to user in this function and keep everything else the same:

```python
def greet(usr):
    return f'hello {usr}'
```
