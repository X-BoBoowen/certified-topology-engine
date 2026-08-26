# Phase C.1 Exact-Input Soundness Repair Bundle

## Final status

**REPAIRED RESTRICTED ENGINE**

The red-team false-valid reproducer is now a permanent high-depth regression test. The certified API rejects Python `float` inputs instead of guessing whether a caller intended the decimal value or the exact binary floating-point value.

> **This is still an analytic-circle restricted reference engine.**
> **It is not a general spline reach engine.**

The bundle does not implement a spline atlas, a general local-diagonal radius, a certified BVH, real-image processing, conformal calibration, or a full vision pipeline.

## What was repaired

The original implementation allowed `r0=0.7` to enter the certified path. The expression

```python
threshold2 = (2 * r0) * (2 * r0)
```

was then evaluated in binary floating point and could round downward. A true short doubly-critical pair could consequently satisfy the incorrectly weakened pruning predicate

```python
if d2.lo >= threshold2:
```

and be discarded, causing a false `VALID`.

The patched implementation now:

1. admits only `fractions.Fraction` and non-boolean built-in `int` values at the certified numeric boundary;
2. rejects `float`, `Decimal`, `bool`, numeric subclasses, strings, and unknown numeric types;
3. provides `parse_rational()` as an explicit exact text adapter;
4. validates `r0`, `Circle.cx`, `Circle.cy`, and `Circle.radius` before atlas construction or certificate arithmetic;
5. computes the squared distance threshold exactly as a `Fraction`;
6. verifies that the input circles form a nonempty pairwise-disjoint embedded circle link;
7. returns the explicit `INPUT_INVALID` status for contract violations;
8. fixes unresolved-box accounting at a box-budget exit;
9. records three independent box-accounting invariants;
10. describes interval subdivision as closed, cover-preserving bisection rather than a disjoint partition;
11. turns `run_suite.py` into an executable oracle that exits nonzero on an expectation mismatch.

## Status semantics

- `VALID`: all nonlocal parameter boxes were soundly excluded and the circle-link reach is certified to be at least the exact input `r0`.
- `UNKNOWN`: the input is valid, but the finite depth/box budget did not close the certificate.
- `CURVATURE_FAIL`: the input is valid, but a circle radius is smaller than `r0`, so the local curvature condition fails.
- `INPUT_INVALID`: the call violates the certified numeric or embedded-link input contract.

`UNKNOWN` must never be interpreted as invalid geometry, and `INPUT_INVALID` must never be merged with `UNKNOWN` in audit logs.

## Exact numeric API

Accepted directly by `ReachEngine.certify()`:

```python
from fractions import Fraction

Fraction(7, 10)
7  # converted explicitly to Fraction(7, 1)
```

Rejected:

```python
0.7
Decimal("0.7")
True
"0.7"
numpy.int64(7)
custom_numeric
```

Exact decimal text must be parsed outside `certify()`:

```python
from reach_engine import parse_rational

r0 = parse_rational("0.7")
assert r0 == Fraction(7, 10)
```

See `API_NUMERIC_SEMANTICS.md` for the full contract.

## Input geometry contract

For each pair of circles with exact center-distance square `D2` and radii `R_i,R_j`, the boundaries are accepted only when

```text
D2 > (R_i + R_j)^2
```

or

```text
D2 < (R_i - R_j)^2.
```

Thus externally separated and strictly nested circles are allowed. External tangency, internal tangency, transverse intersection, and duplicate circles return `INPUT_INVALID`. The empty circle list is unsupported and also returns `INPUT_INVALID`.

See `INPUT_VALIDATION.md` for examples and exact predicates.

## Installation

The engine itself uses only the Python standard library. Tests require pytest.

```bash
python -m pip install -r requirements.txt
```

Verified environment is recorded in `ENVIRONMENT.txt`.

## Complete verification commands

Run from the extracted bundle directory:

```bash
python -m py_compile \
  reach_engine.py \
  test_reach_engine.py \
  test_input_contract.py \
  test_adversarial_repair.py \
  test_accounting_and_suite.py \
  run_suite.py \
  run_adversarial_reference.py \
  run_before_after_regression.py
```

```bash
python -m pytest -q \
  test_reach_engine.py \
  test_input_contract.py \
  test_adversarial_repair.py \
  test_accounting_and_suite.py
```

```bash
python run_before_after_regression.py
```

```bash
python run_suite.py
```

```bash
python run_adversarial_reference.py
```

The suite runner writes `synthetic_results.json` and returns exit code 1 if any scenario violates its formal expected-status rule.

## Formal suite expectations

- `VALID`: actual status must be exactly `VALID`.
- `CURVATURE_FAIL`: actual status must be exactly `CURVATURE_FAIL`.
- `INPUT_INVALID`: actual status must be exactly `INPUT_INVALID`.
- `UNKNOWN_ALLOWED`: actual status may be `VALID` or `UNKNOWN`; this is used for exact equality cases.
- `NOT_VALID`: any status except `VALID` is accepted.

## Box-accounting invariants

Every returned result records and checks:

```text
initial_pair_boxes + subdivision_children_enqueued
    = interval_boxes + queued_boxes_at_exit
```

```text
interval_boxes
    = distance_pruned
    + normal_pruned
    + max_depth_unresolved_boxes
    + subdivision_parent_boxes
```

```text
unresolved_boxes
    = max_depth_unresolved_boxes + queued_boxes_at_exit
```

A violation raises an internal assertion rather than producing a certificate.

## Regression evidence

`run_before_after_regression.py` replays the exact red-team geometry against:

- the audit-only unsound snapshot in `audit/legacy_unsound_reach_engine.py`;
- the patched engine.

Expected comparison:

```text
before: float 0.7                  -> VALID       (the reproduced bug)
after:  float 0.7                  -> INPUT_INVALID
after:  Fraction.from_float(0.7)   -> UNKNOWN
after:  Fraction(7, 10)            -> UNKNOWN
```

The legacy file is included only to reproduce the historical failure. Do not import it as an engine.

## Included verification evidence

- `BEFORE_AFTER_REGRESSION.txt`
- `TEST_OUTPUT.txt`
- `SYNTHETIC_SUITE_OUTPUT.txt`
- `ADVERSARIAL_REFERENCE_OUTPUT.txt`
- `synthetic_results.json`
- `adversarial_reference_results.json`
- `SCENARIO_TEST_MAPPING.md`
- `CODE_DIFF.patch`
- `audit/RED_TEAM_FALSE_VALID_AUDIT.log`

## Scope boundary

The repaired statement is limited to the analytic circle reference engine:

```text
VALID => reach(circle link) >= exact r0
```

under the enforced input contract and finite exact-rational interval computation.

It does **not** establish:

- soundness of a general spline atlas;
- a general certified `delta_loc` implementation;
- practical complexity on real implicit curves;
- real-image feasibility;
- a certified BVH;
- any conformal or segmentation guarantee.

The same red team that found the false-valid should replay the original counterexample and independently attack the patched exact-input boundary before any work begins on a general spline adapter.
