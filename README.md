# Phase C.2b Packaging and Runtime Closure

This is a **proposal-assisted**, correctness-first piecewise-polynomial general-field reference engine.

It proves that an exact piecewise-polynomial field has exactly the zero set of an exact disjoint circle-link proposal by checking `F_c = h_c G` on every cell and certifying `h_c > 0`. It then delegates the DCSD certificate to the frozen, byte-for-byte Phase C.1 analytic-circle oracle.

It is **not** a field-only loop discovery engine. Candidate-free calls return `UNKNOWN`.
It does not include a certified BVH. It has not been evaluated on real images. It does not implement conformal certification.

## Exact input semantics

Certificate inputs accept only built-in `int` (not `bool`) and built-in `fractions.Fraction`. Floats, Decimal, NumPy scalars, strings, subclasses and unknown numeric objects are rejected. Decimal text must be parsed separately with `parse_rational`.

## Verify

From a newly extracted release archive, the one-command bootstrap is:

```bash
python scripts/verify_pristine.py
```

It first validates every path, size and SHA-256 in `CANDIDATE_MANIFEST.json`,
rejects missing/extra files, and checks the controlled-source digest before any
environment subprocess. It then creates the archive-local `.venv`, installs
`requirements.txt` with a 120-second subprocess limit, and runs the complete
machine gate with a 600-second limit. If the environment is already prepared,
run:

```bash
python -m pip install -r requirements.txt
python -m compileall -q phase_c2a tests scripts
python scripts/run_static_undefined_check.py
python -m pytest -q tests
python scripts/run_property_suite.py
python scripts/run_general_suite.py
python scripts/run_invalid_suite.py
python scripts/run_proof_replay.py
python scripts/run_proof_tamper.py
python scripts/run_float_path_audit.py
python scripts/run_frozen_hash_check.py
python scripts/run_relocation_check.py
python scripts/verify_all.py
```

`verify_all.py` sets its own project import path, gives every child gate a timeout
of at most 120 seconds, and derives `all_passed` and `FINAL_VERDICT.txt` from the
recorded exit codes and semantic counts. It may be launched from any working
directory.
