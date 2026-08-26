# Phase C.1 Independent Exact-Input Soundness Re-Audit

## Final verdict

**A. VALID REPAIRED RESTRICTED ENGINE**

Audited property:

```text
VALID => reach(circle link) >= exact r0
```

This verdict applies only to the attached analytic-circle restricted engine. It does not cover a spline atlas, general `delta_loc`, BVH soundness, real images, conformal prediction, or practical spline feasibility.

## Integrity

- Outer ZIP SHA-256: `0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0`
- Inner ZIP SHA-256: `94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe`
- Outer `unzip -t`: PASS
- Inner `unzip -t`: PASS
- `sha256sum -c SHA256SUMS.txt`: all 27 listed entries PASS
- `SHA256SUMS.txt` itself was independently hashed.
- All 24 files inside the inner ZIP are byte-identical to their corresponding outer files.

### All 28 pristine package-file hashes

```text
10dd1791b6cd61e03c9e7aecd494e49a301c6ef73a7e2a2df3b52a7b3be5ebab  ADVERSARIAL_REFERENCE_OUTPUT.txt
437029b58bbda40fba6a3bc9f3c243092c62e42f09b32d9e81960e5e806df797  API_NUMERIC_SEMANTICS.md
c1a852f9c66b0279f95fe6f05a8524e7d04b57d9eb939f74abd76d5a1b97c402  BEFORE_AFTER_REGRESSION.txt
54789c406a80847d47e3df0ba1b18163bbe0eb98a9ab0868e9f207425f2a821b  CODE_DIFF.patch
ec4fc01bb09706af8c609a4d73a6ff0737c87918bbafb362f439db12e1ec7f63  ENVIRONMENT.txt
1a53a1ec765c477b2eb9e932716849b5c82798f0f539eae1d1df73c9e5a25065  INPUT_VALIDATION.md
a14df0af1462d5cf30342164d03792ff8a25639d805aaf2f4f2973aebe5d3cf9  MANIFEST.json
4c561aca23e22e1e10d5bd3be2e695ba708ba8a324bd0a6d021edc2768a6a3a8  README.md
88f5973e287b302808e60b65730d226350dc0fe6d4f2b16dfd792b0f44a6f783  REPAIR_SUMMARY.md
d3761c0dd197f403b7df7b47b87c4d547cc755b12b42b42ca9be8fd42eabefb6  SCENARIO_TEST_MAPPING.md
693aed1b5d9bad1d6d16a0c2960fb28d0cd36d26ece9eb2bfb0f27e7edc2a2de  SHA256SUMS.txt
0b452ed20a3edd61d0fea954a2ba2bc18a047bf33373f4b90bb8fa469f95eff0  SYNTHETIC_SUITE_OUTPUT.txt
aaaf5837268c26dfebcccb20b543da9701274ee70a8158931bf8b7cba64b219a  TEST_OUTPUT.txt
93fbb93fb910a6f7eb317680c5e2dbb3c01169881aa7c43d4fca2bc7f98b248c  ZIP_LISTING.txt
829e588365cfcf60b00396208fd794877de55a5f162d733a74ad91f47d6bdf15  adversarial_reference_results.json
8b129176e6d3f573c3bd5d1cf18e84df5d555546fc8fff5f24331b62491dd95d  audit/RED_TEAM_FALSE_VALID_AUDIT.log
8552eb46fe6e33453261793029aedb38fa37c86fbfa5444277f143349d4ec74d  audit/legacy_unsound_reach_engine.py
94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe  phase_c_reach_engine_prototype.zip
5a8618b795234601a86db065428b5db10c584e2813a32368884766a0a31917ed  reach_engine.py
693d97bdd0fb5283060c3efadf25a90d0c3b59be09b25fac59f5f1c68a1f993b  requirements.txt
32f382d7204ee2f4dd6a6007e9321559c3f100713e6bf49f0d4836887b3385fb  run_adversarial_reference.py
9bf63773714307452643c69463af3cb568e0cb1b28f702060b4af25ca4f5f61a  run_before_after_regression.py
ef843c94ce09cffc4f1eeaa20c99a2fa110e912c409e9d8305680067ad116289  run_suite.py
8569be4d772eca0729aa6edefdcb55ba7cfb1ebd68ba2c8c0be088e8d617e2e6  synthetic_results.json
96da1b4dcaef17e157dbc893f2f704cade900331bf063060958399bf82d2e772  test_accounting_and_suite.py
bcb0070ba3e091f0b87ad1a9bf4634dd55cdd537a9502b494dc1d1d944cd5084  test_adversarial_repair.py
c99113b17c05f483b38cff26f51d1d5f989640a5dca9aa1c24229888e7a7a646  test_input_contract.py
d2141af4d2c2ac60b639b09cd8668a8b9e1e15ecb261874fa207ed130d06edea  test_reach_engine.py
```

## Independent execution

| Command | Result |
|---|---|
| `python -m py_compile` on all 9 Python files | PASS |
| all pytest tests | `48 passed in 21.14s` |
| `run_before_after_regression.py` | PASS; printed `REGRESSION_REPAIR_VERIFIED` |
| `run_suite.py` | PASS; exit 0; 22/22 expectations |
| `run_adversarial_reference.py` | PASS; exit 0; 12/12 exact-rational cases |

Freshly generated `synthetic_results.json` and `adversarial_reference_results.json` match the pristine packaged JSON in every field except wall-clock runtime.

## Historical regression

Using `max_depth=130` and `max_boxes=2_000_000`:

| Call | Patched result | Boxes | Unresolved |
|---|---:|---:|---:|
| `r0 = 0.7` | `INPUT_INVALID` | 0 | 0 |
| `r0 = Fraction.from_float(0.7)` | `UNKNOWN` | 2162 | 6 |
| `r0 = Fraction(7,10)` | `UNKNOWN` | 2162 | 6 |

The included legacy snapshot independently reproduced the historical `float 0.7 -> VALID` result, while the patched implementation rejected the float before atlas construction.

## Exact-input contract audit

The runtime boundary is closed as follows:

- `exact_fraction` accepts only exact built-in `Fraction` and non-boolean exact built-in `int` (`reach_engine.py:19-36`).
- `r0` is normalized before all geometry and must be positive (`470-488`).
- every record must have exact type `Circle`; `cx`, `cy`, and `radius` are normalized through the same exact gate; radius must be positive (`335-356`).
- `threshold2` is computed as `Fraction(2) * r0`, squared in exact rational arithmetic, and type-checked (`415-422`).
- no float literal exists in `reach_engine.py`; `perf_counter()` affects only `runtime_seconds`.

Independent unsupported-type testing covered float, `Decimal`, bool, string, bytes, complex, `None`, `Fraction` subclass, `int` subclass, NumPy float/int/bool scalars, a `Circle` subclass, a circle-like record, a tuple, and a custom numeric object whose arithmetic/comparison protocols raise immediately. Result: **89 / 89 checks passed**, NumPy available: `True`, failures: `0`. Unsupported values returned `INPUT_INVALID` before patch or interval generation, and the custom object's numeric protocols were never invoked.

## Circle-link validator

For each pair the code computes exact squared center distance and accepts only:

```text
D² > (R1 + R2)²          external separation
D² < (R1 - R2)²          strict nesting
```

It rejects duplicate circles, external tangency, internal tangency, transverse intersection, nonpositive radii, and empty input (`358-387`). Legal concentric nesting, off-centre nesting, and four-level nesting were accepted. The pairwise condition is necessary and sufficient for a finite collection of positive-radius circle boundaries to be a pairwise-disjoint embedded circle link.

## All paths capable of reaching VALID

1. **Curvature:** every radius is compared exactly with `r0`; any `R < r0` returns `CURVATURE_FAIL`; equality is allowed (`505-514`).
2. **Local patch exclusion:** only same-circle same/adjacent cyclic patches are removed (`189-199`, `518-523`). With `pieces_per_quarter >= 2`, their common angular span is strictly below `pi`; a nonzero circle chord is tangent-orthogonal at an endpoint only at antipodal separation, so this prune cannot remove a nonzero doubly-critical pair. Quarter seams and the cyclic seam are included.
3. **Distance threshold:** `distance2.lo >= (2*r0)^2` uses an exact `Fraction` threshold (`533`, `562-572`). Equality is correctly safe because the forbidden condition is strict distance `< 2*r0`.
4. **Position/tangent enclosures:** the rational circle parameterization and its derivatives are algebraically correct (`170-187`); denominators are positive on every internal parameter interval `[0,1]`.
5. **`d²`, `G1`, `G2`:** natural exact-rational interval extensions are inclusion-preserving; a box is orthogonality-pruned only when at least one enclosure excludes zero (`568-581`).
6. **Subdivision:** each closed child pair shares the exact midpoint and their union covers the parent (`136-144`, `587-597`). Overlap can duplicate work but cannot omit a point.
7. **Budgets/unresolved:** box-budget exhaustion immediately returns `UNKNOWN`; max-depth leaves are counted unresolved; any unresolved leaf forces `UNKNOWN` (`535-556`, `583-617`).
8. **Final status:** the only `Status.VALID` construction in the source is the final return after the queue is empty and `max_depth_unresolved_boxes == 0` (`619-635`). Static AST inspection found zero float literals and exactly one `Status.VALID` reference in the engine implementation.

## Interval and geometric stress tests

- Position-coordinate inclusions: **69988**
- Tangent-coordinate inclusions: **69988**
- `d²/G1/G2` point-in-enclosure checks: **159726**
- cover-preserving bisection checks: **20000**
- Total interval/cover checks: **319702**
- Threshold/seam geometry cases: **25**, false VALID: **0**
- Structural exact-rational geometry cases: **36**, false VALID: **0**

The 61 new geometry cases covered `pieces_per_quarter = 2,3,4,5,7`, internal patch seams, quarter/cyclic seams, thresholds differing from true reach by `10^-20`, hidden short gaps among five circles, concentric nonisolated root families, four-level nesting, off-centre nesting, mixed nested/external links, extremely small rational gaps, and very large numerator/denominator Fractions. Every above-reach case returned `UNKNOWN` or `CURVATURE_FAIL`, never `VALID`.

## Accounting and suite oracle

All implemented invariants were checked on every returned result:

```text
initial_pair_boxes + subdivision_children_enqueued
  = interval_boxes + queued_boxes_at_exit

interval_boxes
  = distance_pruned + normal_pruned
  + max_depth_unresolved_boxes + subdivision_parent_boxes

unresolved_boxes
  = max_depth_unresolved_boxes + queued_boxes_at_exit
```

`run_suite.py` formalizes all expected labels, writes per-case `expectation_passed`, returns exit code 1 on any mismatch, and independently returned exit 0 for all 22 cases (`run_suite.py:239-300`). `NOT_VALID` is deliberately a one-sided safety oracle; exact-input acceptance is checked separately by dedicated tests.

## Source immutability

The audit did not patch the project. Post-audit byte comparisons confirmed that the engine, runners, tests, and legacy snapshot in the run directory remained identical to the pristine extraction. The pristine `SHA256SUMS.txt` verification was repeated after all testing and still passed.

## Required confirmations for verdict A

- Historical float precision issue is permanently covered by high-depth regression tests: **confirmed**.
- Exact-input runtime contract is closed: **confirmed**.
- Circle-link validator is correct for the declared restricted input class: **confirmed**.
- All packaged tests/runners and all finalized independent stress tests pass: **confirmed**.
- New incorrect `VALID` found: **no**.
- Scope is only the attached analytic-circle restricted engine: **confirmed**.
