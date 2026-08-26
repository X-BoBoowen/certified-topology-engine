# Scenario and Pytest Mapping

## Summary

- Legacy synthetic scenarios retained: **10**
- New adversarial/invalid-input scenarios: **12**
- Total executable suite scenarios: **22**
- Original pytest tests retained: **9**
- Additional pytest tests: **39**
- Total pytest tests after repair: **48**

The original 9 tests remain in `test_reach_engine.py`. One direct false-valid regression was added there, and the remaining tests are separated into numeric/input, adversarial, and accounting/suite files.

## Executable scenario semantics

| Expected label | Passing actual statuses |
|---|---|
| `VALID` | `VALID` only |
| `CURVATURE_FAIL` | `CURVATURE_FAIL` only |
| `INPUT_INVALID` | `INPUT_INVALID` only |
| `UNKNOWN_ALLOWED` | `VALID` or `UNKNOWN` |
| `NOT_VALID` | any status except `VALID` |

`run_suite.py` exits with code 1 if any scenario violates these rules.

## Scenario-to-test correspondence

| Scenario | Expected | Primary pytest coverage |
|---|---|---|
| `S1_single_circle` | `VALID` | `test_s1_single_circle_strict_margin_valid` |
| `S2_two_separated_circles` | `VALID` | `test_s2_two_separated_circles_valid` |
| `S3_concentric_annulus` | `VALID` | `test_s3_concentric_annulus_strict_margin_valid`; `test_nested_disjoint_circles_remain_valid_input` |
| `S3b_annulus_equality` | `UNKNOWN_ALLOWED` | `test_annulus_equality_has_independent_regression` |
| `S4_near_parallel_large_loops` | `VALID` | `test_s4_near_parallel_large_circles_below_bottleneck_valid` |
| `S5_exact_equality_pair` | `UNKNOWN_ALLOWED` | `test_s5_equality_never_false_valid` |
| `S6_high_curvature_fails` | `CURVATURE_FAIL` | `test_s6_curvature_branch_rejects_too_large_radius` |
| `S6b_high_curvature_strict_valid` | `VALID` | `test_s6_curvature_branch_allows_strictly_smaller_radius` |
| `S7_low_curvature_global_bottleneck` | `NOT_VALID` | `test_s7_low_curvature_global_bottleneck_not_false_valid` |
| `S8_nested_and_multiple_components` | `VALID` | `test_s8_nested_and_multiple_components_valid` |
| `A1_red_team_float_r0_rejected` | `INPUT_INVALID` | `test_float_r0_false_valid_regression_is_not_valid`; `test_red_team_float_counterexample_is_rejected`; `test_float_r0_is_input_invalid` |
| `A2_red_team_exact_binary_float_not_valid` | `NOT_VALID` | `test_red_team_exact_binary_float_value_is_not_valid` |
| `A3_red_team_exact_decimal_not_valid` | `NOT_VALID` | `test_red_team_exact_decimal_value_is_not_valid` |
| `A4_near_tangent_strict_margin_valid` | `VALID` | `test_near_external_tangency_strictly_disjoint_below_gap_is_valid` |
| `A5_near_tangent_above_reach_not_valid` | `NOT_VALID` | `test_near_external_tangency_above_true_reach_is_not_valid` |
| `A6_periodic_seam_bottleneck` | `NOT_VALID` | `test_periodic_seam_bottleneck_is_not_missed` |
| `A7_three_components_hidden_short_gap` | `NOT_VALID` | `test_three_components_hidden_short_gap_is_not_valid` |
| `A8_external_tangent_invalid` | `INPUT_INVALID` | `test_external_tangent_link_is_input_invalid` |
| `A9_internal_tangent_invalid` | `INPUT_INVALID` | `test_internal_tangent_link_is_input_invalid` |
| `A10_intersection_invalid` | `INPUT_INVALID` | `test_transversely_intersecting_link_is_input_invalid` |
| `A11_duplicate_invalid` | `INPUT_INVALID` | `test_duplicate_circle_is_input_invalid` |
| `A12_empty_invalid` | `INPUT_INVALID` | `test_empty_input_is_input_invalid` |

## Additional contract tests not tied to one scenario

### `test_input_contract.py`

- exact decimal/fraction text parsing;
- float `r0` rejection;
- `Decimal`, `bool`, custom numeric rejection;
- integer normalization;
- float circle-field rejection;
- nonpositive radius and `r0` rejection;
- nested-circle acceptance;
- defense-in-depth interval float rejection;
- rejection of `Fraction`/`int` subclasses;
- no silent string parsing inside `certify()`;
- rejection of nonfinite and zero-denominator text;
- exact squared-threshold type and value;
- public atlas link validation;
- NaN/Inf rejection;
- exact `Fraction` endpoints for position, tangent, distance-square, `G1`, and `G2`;
- rejection of `Circle` subclasses.

### `test_adversarial_repair.py`

- permanent high-depth red-team reproducer;
- exact binary-float and exact decimal thresholds;
- near tangency on both sides of the true reach;
- annulus continuous-family equality;
- periodic seam bottleneck;
- hidden gap among three components;
- deterministic random exact-rational links checked against analytic reach.

### `test_accounting_and_suite.py`

- closed cover-preserving bisection;
- max-depth unresolved accounting;
- max-box accounting with previously accumulated unresolved boxes;
- formal suite expectation rules;
- generated/processed/queued, processed-outcome, and unresolved accounting invariants;
- nonzero suite exit status on deliberate expectation mismatch.

## Random exact-rational reference runner

`run_adversarial_reference.py` independently generates 12 deterministic exact-rational links:

- 8 externally separated pairs;
- 4 strictly nested pairs.

For every case it computes the analytic reach exactly in collinear rational geometry, then checks:

```text
r0 = 3/4 * reference_reach  -> VALID
r0 > reference_reach        -> not VALID
```

Exact-equality behavior is covered separately by `S3b` and `S5`, because equality is allowed to remain `UNKNOWN`.
