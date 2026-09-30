---
type: regex
pattern: 'VERDICT\W{0,4}FAIL'
flags: i
match: not_contains
target: last_message
---
