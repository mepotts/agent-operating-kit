# Eval suite

Cases for `claude plugin eval` (Claude Code 2.1.269 or later). Every run is a real model call on your account.

```
claude plugin eval . --trust-plugin --no-publish --ablation none --model sonnet --judge-model sonnet -j 3 --max-cost-usd 10
```

Results go to `evals/results/`, which is git-ignored. `--no-publish` keeps the HTML report local. Three runs per case is the default.

| Case | Expects |
|---|---|
| `sprint-spec-fires`, `risk-tiers-fires`, `refute-review-fires`, `release-gate-fires`, `handoff-fires`, `failure-to-rule-fires` | The named skill fires on natural phrasing, and the answer has the right shape |
| `unrelated-request-quiet` | No skill fires on an ordinary rename |
| `reviewer-refutes-false-done` | The reviewer returns FAIL on a planted false "done" and names the defects |
| `reviewer-accepts-true-claim` | The same reviewer does not FAIL a true claim. This control checks that the graders can go both ways |

The reviewer cases embed the `examples/expired-coupon` candidates verbatim. `scripts/validate.py` rule E07 fails if they drift. [VERIFICATION.md](../VERIFICATION.md) records the results and what they do and do not show.
