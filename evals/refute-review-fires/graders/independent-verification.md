---
type: llm
---

PASS if the reply says to use a separate reviewer that is told to refute (not approve), to re-run the tests itself, to read the assertions, to do a red-green check (revert the fix and confirm the new test fails), and to treat skipped tests or zero tests found as failures.
FAIL if it recommends trusting the report or asking the same agent to confirm its own work.
