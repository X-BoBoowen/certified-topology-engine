# Phase C.2a Research Status

## Final verdict

```text
PIVOT — SELF-VERIFICATION FAILED
```

## Automatic gate

- Staging `verify_all.py` exit: `1`
- `all_passed`: `False`
- `float_path_audit`: exit `0`
- `general_suite`: exit `1`
- `invalid_suite`: exit `0`
- `proof_replay`: exit `1`
- `property_suite`: exit `0`
- `py_compile`: exit `0`
- `pytest`: exit `2`

## General-suite semantic counts

```json
{
  "circle_failures": null,
  "circle_false_valid": null,
  "circle_scenarios": null,
  "circle_valid": null,
  "knot_failures": null,
  "knot_scenarios": null,
  "knot_valid": null
}
```

## Repaired boundary certificate

The former whole-edge natural interval predicate has been replaced by exact rational univariate restriction plus Sturm root counting on every outer-domain edge segment. Endpoint roots are rejected exactly. A strictly zero-free polynomial with interval dependency can therefore pass without sampling.

## Proposal-assisted scope

A VALID result requires an exact per-cell identity `F_c = h_c G`, a certified strictly positive multiplier on every cell, an exact pairwise-disjoint circle-link proposal, and a strict exact reach margin. Candidate-free field calls remain `UNKNOWN`; automatic field-only loop discovery is not implemented.

## Proof replay

A replay reruns the complete exact field, factorization and reach certificate and compares the sealed canonical proof transcript. A tampered decision fails replay.
