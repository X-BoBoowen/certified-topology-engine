# Phase C.1 Repair Summary

## Verdict

After the verification commands recorded in this bundle:

**REPAIRED RESTRICTED ENGINE**

## Historical failure

The audited legacy snapshot returned `VALID` for the red-team geometry when `r0` was supplied as Python float `0.7`, even though the true reach was strictly smaller than the exact real value of that float.

## Patched behavior

| Call | Patched status |
|---|---|
| `certify(circles, 0.7)` | `INPUT_INVALID` |
| `certify(circles, Fraction.from_float(0.7))` | `UNKNOWN` |
| `certify(circles, Fraction(7, 10))` | `UNKNOWN` |

No approximate conversion is performed inside `certify()`.

## Verification summary

- `py_compile`: PASS
- pytest: 48 passed
- executable scenario oracle: 22/22 expectations passed
- deterministic random exact-rational reference suite: 12/12 passed
- historical false-valid: reproduced on legacy snapshot
- patched float call: rejected before interval processing
- patched exact thresholds above the true reach: no `VALID`
- all logged box-accounting invariants: true

## Scope

This verdict applies only to the analytic-circle restricted reference engine and its enforced input contract.

It does not certify a general spline implementation or practical real-image feasibility.

## Required independent re-audit

Before a general spline atlas is started, the same red team should:

1. replay the historical float reproducer;
2. attack float, Decimal, bool, strings, numeric subclasses, and custom numeric objects;
3. inspect all exact-threshold predicates;
4. recheck external/internal tangency, intersection, duplicate, nested, and empty-link handling;
5. rerun the 48 pytest tests, 22 scenarios, and random exact-rational suite;
6. search for a new exact-input false-valid.
