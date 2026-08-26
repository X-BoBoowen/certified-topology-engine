# Phase C.2b Packaging and Runtime Closure Gate

## Frozen verdict entering this gate

Phase C.2a is not accepted. Its machine verdict is:

`PIVOT — SELF-VERIFICATION FAILED`

Fresh reproduction on 2026-08-26 is recorded in `docs/BASELINE_PROVENANCE.md` and `audit/baseline/2026-08-26/`.

## Objective

Produce a relocatable, self-verifying, proposal-assisted C.2b package whose machine status is internally consistent and whose required gates all terminate with exit code zero in a pristine re-extraction.

This gate repairs packaging, runtime closure, test isolation, bounded execution, and proof-log reproducibility. It does not add a new geometric method.

## Known baseline failures

1. `phase_c2a/engine.py` references undefined `frozen_outer` and `frozen_inner` when writing proof metadata.
2. Unscoped pytest recursively collects duplicate frozen Phase C.1 tests and terminates with import-file mismatches.
3. The general differential oracle lacks an explicit external timeout and uses very high internal depth/box budgets.
4. General-suite failure prevents generation of semantic counts, so `general_semantic_gate` is false.

## Allowed changes

- Explicit resolution and validation of frozen Phase C.1 artifacts.
- Removal of implicit global-name dependencies in the proof-log path.
- Pytest collection isolation through project configuration.
- A static undefined-name gate.
- Deterministic work limits and subprocess timeouts for verification commands.
- Proof replay, proof tamper rejection, and relocation verification.
- Machine-generated summaries, manifests, hashes, environment records, and packaging scripts.
- Minimal regression tests directly covering the failures above.

Changes to field mathematics, Sturm logic, factorization semantics, exact-input semantics, or VALID conditions require separate Supervisor approval because they are outside this runtime-closure gate.

## Explicit non-goals

- Field-only loop discovery.
- Automatic general spline atlas construction.
- BVH acceleration.
- Three-dimensional surfaces.
- Real medical-image experiments.
- A complete certified XOR engine.
- Conformal calibration or model training.
- New topology theorems.
- Refactoring unrelated frozen Phase C.1 code.

## Immutable artifact hashes

```text
outer = 0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0
inner = 94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe
```

The resolver must verify hashes before loading. A mismatch, missing artifact, or ambiguous fallback path must fail closed.

## Required machine gates

The final `verify_all` must execute and record every gate below:

1. Python compilation of `phase_c2a`, `tests`, and `scripts`.
2. Static undefined-name check covering production code, verification scripts, and tests.
3. Scoped pytest that collects only the target test tree.
4. Property suite.
5. General scenario suite with the required circle and knot counts.
6. Invalid-input suite.
7. Float-path audit.
8. Proof replay in a new process.
9. Tampered-proof rejection.
10. Relocation test from a different extraction path.
11. Frozen artifact hash validation.
12. Overall bounded execution.

Every subprocess must have a declared timeout no greater than 120 seconds. The complete reference verification must have a declared timeout no greater than 600 seconds. Budget exhaustion is a failure or `UNKNOWN`; it cannot become VALID.

The general semantic gate remains:

```text
circle_scenarios == 22
circle_failures == 0
circle_false_valid == 0
circle_valid > 0
knot_scenarios == 9
knot_failures == 0
```

## Proof-log requirements

- Record exact input identity and exact numeric values.
- Record the actual frozen outer/inner artifact hashes.
- Record algorithm/package version and relevant work budgets.
- Replay without access to the original in-memory engine object.
- Reject a changed verdict, changed numeric certificate, changed artifact hash, or changed proof-critical field.
- Continue to replay after the package is moved to another directory.

## Required candidate deliverables

- One clean release archive.
- Release archive SHA-256.
- Full Git commit SHA.
- Frozen artifact hash report.
- `verification_summary.json` with commands, exit codes, runtimes, semantic counts, and `all_passed`.
- Raw logs for every gate.
- Proof replay and tamper logs.
- Relocation log.
- `KNOWN_LIMITATIONS.md` preserving proposal-assisted scope.
- One documented command that verifies a pristine extraction.

## Acceptance semantics

Worker self-verification is necessary but not sufficient.

The Supervisor may accept the phase only when a fixed commit and release archive are independently checked in a new directory and every required gate exits zero with mutually consistent logs and summaries.

If any required condition fails, the formal verdict is:

`PIVOT — PACKAGING / RUNTIME CLOSURE FAILED`

If all conditions pass, the formal verdict is:

`PASS — PHASE C.2B PACKAGING / RUNTIME CLOSURE ACCEPTED`
