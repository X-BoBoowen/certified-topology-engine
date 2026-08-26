# Phase C.2a Baseline Provenance

## Source identity

```text
Source archive:
D:/29722/Desktop/弱小但是有梦想的BoBoo文/paper/paper7/aaa/Phase_C2a_Self_Verification_Boundary_Repair_Bundle_20260824.zip

SHA-256:
CFA83CCEE4D689E6FD936D486EB8C7241E58D027B555BDA82DEAD79D90C96DD2

Archive entries: 113
Archive wrapper root: Phase_C2a_Self_Verification_Repair_20260824
Unsafe absolute or traversal paths: 0
```

The archive was extracted into the short-path repository `paper7/c2b` with the single wrapper directory stripped. The original archive under `aaa` was not modified.

The imported copy's five `.pytest_cache` files were removed before the baseline commit. No source, test, frozen artifact, supplied log, supplied result, or archive content was edited during import.

## Git identity

```text
Repository branch: main
Failed-baseline commit: 3b8c4eed06810f3f33f4c01fefc87de3f2521a16
Commit subject: chore: import failed phase c2a baseline
Git: git version 2.54.0.windows.1
Remote: none
```

## Verification environment

```text
Operating system: Windows
Python: 3.12.13
Virtual environment: .venv
pytest: 9.1.1
Declared requirement: pytest>=8.0
Fresh verification date: 2026-08-26 Asia/Shanghai
```

An initial run with the bundled Python executable found that pytest was not installed. That run is an environment diagnostic, not the canonical baseline result. A repository-local `.venv` was then created and `requirements.txt` installed before the canonical reproduction.

## Canonical fresh reproduction

Command:

```powershell
& '.\.venv\Scripts\python.exe' '.\scripts\verify_all.py'
```

Observed overall exit code: `1`.

| Gate | Exit code | Observed result |
|---|---:|---|
| `py_compile` | 0 | Passed |
| `pytest` | 2 | Four duplicate frozen-test import-file mismatches during collection |
| `property_suite` | 0 | Passed |
| `general_suite` | 1 | `NameError: frozen_outer is not defined` |
| `invalid_suite` | 0 | Passed |
| `proof_replay` | 1 | `NameError: frozen_outer is not defined` |
| `float_path_audit` | 0 | Passed |
| `general_semantic_gate` | false | General counts were not generated |
| `all_passed` | false | Correct failed-baseline verdict |

The general and proof-replay traces both reach `phase_c2a/engine.py` while constructing proof metadata and fail on the undefined `frozen_outer` name. The pytest output shows duplicate test-module names under `frozen_phase_c1/` and `frozen_phase_c1/prototype/`.

## Preserved evidence

Fresh machine outputs are copied to:

```text
audit/baseline/2026-08-26/logs/
audit/baseline/2026-08-26/results/
```

The normal `logs/` and `results/` directories also contain the latest local verification output and may be overwritten by future Worker runs. The `audit/baseline/2026-08-26/` copy is the immutable comparison point.

## Baseline verdict

`PIVOT — SELF-VERIFICATION FAILED`

This provenance record establishes only that the intended failed baseline was imported and reproduced. It does not establish that Phase C.2b is implemented or accepted.
