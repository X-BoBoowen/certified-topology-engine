# Scenario/Test Mapping

- `tests/test_general_scenarios.py::test_22_circle_differential_expectations` executes all 22 circle scenarios.
- `tests/test_general_scenarios.py::test_9_knot_expectations` executes all 9 knot/corner scenarios.
- `tests/test_boundary_sturm.py` covers strict zero-free and true boundary-zero behavior.
- `tests/test_proof_replay.py` covers a real VALID proof and tampering.
- `scripts/run_general_suite.py` enforces `VALID`, `NOT_VALID`, and `UNKNOWN_ALLOWED` semantics and exits nonzero on mismatch.
