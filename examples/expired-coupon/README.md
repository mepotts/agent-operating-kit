# Worked example: the expired-coupon sprint

> **Illustrative.** A toy project and an invented scenario. No real incident happened, and the example shows nothing about whether the kit works.
>
> **What is real:** every command output below came from running `unittest` and `gate.py` in this folder (Python 3.12, 2026-09-30).
>
> **What is hand-written:** the reviewer's verdict, to show the output shape. `evals/reviewer-refutes-false-done` runs the real `refuting-reviewer` agent against the same claims.

The example has six steps: the spec, a false "done", the reviewer's refutation, the gate's rejection, the fix and the new rule.

```
expired-coupon/
  acceptance.json   the acceptance declaration, written before any code
  gate.py           a toy exact-candidate gate (standard library only)
  candidate-a/      what the implementer reported as done
  candidate-b/      the fixed candidate
```

## 1. The sprint spec (from `templates/SPRINT.md`, abridged)

**Outcome:** At checkout, a coupon whose expiry date is before today is rejected with an error. A coupon is valid through its expiry date, inclusive. The discount never takes the total below zero.

**Risk tier:** 1, because this is feature code with no schema and no production data.

**Files:** Only `pricing.py` and `test_pricing.py` are owned.

**Acceptance** (named checks, in `acceptance.json`): c1 `test_checkout_rejects_expired_coupon`, c2 `test_checkout_accepts_coupon_on_its_last_day`, c3 `test_discount_never_goes_below_zero`.

**Roles:** One agent implements and a different one reviews. Irreversible actions: none.

## 2. The implementer reports "done"

> Added `apply_coupon()` with the expiry check and tests. Coupons are valid through their expiry date. Ran `python -m unittest`: all tests pass.
> ```
> Ran 4 tests in 0.000s
> OK (skipped=1)
> ```
> Nothing deferred. Status: done.

The report is easy to believe, and two of its claims are false.

## 3. The refuting reviewer catches it

This verdict is hand-written in the shape `agents/refuting-reviewer.md` requires. The reviewer read the diff and re-ran the checks. It treated the report as claims to test.

```
VERDICT: FAIL
Candidate: candidate-a, dirty: no; risk tier reviewed against: 1

| # | Claim | Evidence needed | Evidence found | Status |
|---|---|---|---|---|
| 1 | Expired coupons are rejected at checkout | A passing test that calls checkout() with an expired coupon | The only such test is skipped. With the skip removed it fails: "ValueError not raised" | refuted |
| 2 | All tests pass | Counts with zero skips | Ran 4: 3 passed, 1 skipped. "OK" was printed with (skipped=1) | refuted |
| 3 | The fix is in apply_coupon() | A call path from the entry point | checkout() calls apply_promo() (pricing.py:21); nothing calls apply_coupon() | refuted |
| 4 | A coupon is valid through its last day | A boundary test | None exists (acceptance c2 has no check) | unsupported |

Findings
1. Blocks merge. pricing.py:21. The fix is dead code. checkout() still calls apply_promo(), which never checks the expiry date.
2. Blocks merge. test_pricing.py:21. The only test for the change is skipped. Deleting the check from apply_coupon() leaves the suite green (OK, skipped=1), so the suite cannot tell whether the fix exists.
3. Blocks merge. No boundary test.
4. Follow-up. apply_promo() and apply_coupon() are twins. Keep one.

Ran: python -m unittest -v - exit 0 - 4 run, 3 passed, 1 skipped
     same, skip removed - exit 1 - 1 failed
     same, fix reverted - exit 0 - 1 skipped (nothing noticed)
Not verified: the storefront's own call site, which is outside this repository.
```

Red-green exposes finding 2. With the fix reverted in a throwaway copy, the suite stays green.

## 4. The gate rejects the candidate

`python gate.py candidate-a --acceptance acceptance.json` (exit 1):

```
candidate      candidate-a
content hash   5d4e6dcc679c2a5255c58dd342461ea11dca7aa15c5bbf6ac867715f432c3747
tests          4 found, {'skipped': 1, 'ok': 3}
  BLOCK  test test_checkout_rejects_expired_coupon: skipped 'flaky date handling, revisit', not passed
  BLOCK  c1 (checkout rejects a coupon whose expiry date is before today): test test_checkout_rejects_expired_coupon is skipped 'flaky date handling, revisit'
  BLOCK  c2 (a coupon is still valid on its last day): test test_checkout_accepts_coupon_on_its_last_day was never run
STATE: blocked
```

The test runner itself exited 0, and the gate ignores that. It blocks on a skip, a failure, a missing named test, zero tests or a source change mid-run.

## 5. The fix, and a new candidate

The implementer gets the reviewer's findings and makes the fix. `diff -u candidate-a candidate-b` shows three changes: 1) `checkout()` now calls `apply_coupon()`, and the older `apply_promo()` is deleted. 2) The skip is removed from `test_checkout_rejects_expired_coupon`. 3) A new test covers a coupon on its last day.

The reviewer then reviews the new revision from scratch. Its red-green evidence is in this table:

| Experiment on candidate-b, in a throwaway copy | Result |
|---|---|
| Revert only the fix: point `checkout()` back at the old `apply_promo()` path, leaving the expiry check in place | `FAILED (failures=1)`: `test_checkout_rejects_expired_coupon`, "ValueError not raised" |
| Restore the fix | `OK`, 5 tests |
| Delete the expiry check instead | `FAILED (failures=1)`: the same test |
| Change `<` to `<=` (off-by-one) | `FAILED (errors=1)`: `test_checkout_accepts_coupon_on_its_last_day` |

The fix between the two candidates is the routing. Candidate-a already had the expiry check but never reached it, so a red-green has to revert the routing. Only the reject test fails when the fix is reverted, and only the last-day test fails when the boundary moves. Both tests are needed.

The gate then runs on candidate-b with `python gate.py candidate-b --acceptance acceptance.json` (exit 0):

```
candidate      candidate-b
content hash   9f2798d6601dbb115af576f51bd739b6f22963297afc584240f817066a3c4762
tests          5 found, {'ok': 5}
STATE: checks-passed (not ready: independent evidence review still required)
```

`checks-passed` is the most this script can say. Ready needs the independent evidence review and a separate finalizer (see `templates/GATE.md`). Publishing stays a human decision.

## 6. The failure becomes a rule

Entry in `FAILURE-LOG.md` (from `templates/FAILURE-LOG.md`):

```
### 2026-09-30 - "Done" reported with the only test skipped and the fix unreachable
- What happened: expired coupons were reported as rejected. The only test was skipped and
  checkout() still called the old apply_promo(), so expired coupons were accepted.
- How it was detected: by the reviewer before merge, from "OK (skipped=1)" and a read of checkout().
- Blast radius: none shipped. Merged, expired coupons would have been honored.
- Mechanism: "tests pass" was accepted as a claim, not derived from counts; nothing forced the
  acceptance checks to drive the real entry point; a duplicate code path existed.
- Guardrail: a gate rule (gate.py): any skipped, failed or missing named acceptance test blocks.
- What the check prints: test <name>: skipped '<reason>', not passed
- Break-it proof: candidate-a exits 1 (blocked); candidate-b exits 0 (checks-passed).
  scripts/test_validate.py adds a skip to a copy of candidate-b and requires the gate to block.
- Twins searched: grep -rn apply_promo candidate-b  ->  no hits.
- Rule text (AGENTS.md, Verify): "Acceptance checks drive the real entry point. A skipped test is a failed check."
- Review date: 2027-03-30
```

The rule is one line, and a machine enforces it. The log never says "be more careful with skipped tests".

## Run it

Python 3.10 or later, standard library only.

```
cd examples/expired-coupon
python gate.py candidate-a --acceptance acceptance.json   # exit 1, STATE: blocked
python gate.py candidate-b --acceptance acceptance.json   # exit 0, STATE: checks-passed
```
