---
type: llm
---

PASS if the reply ties readiness to one frozen candidate (a specific revision and its built artifacts), lists blockers such as skipped or retried or flaky checks, stale artifacts, a source change after the run, or a baseline updated to clear a failure, and calls for an independent evidence review before declaring ready.
FAIL if it treats readiness as a general checklist with no frozen candidate.
