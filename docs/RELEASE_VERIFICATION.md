# Phase C.2b Release Verification

## Candidate

- Name: `Phase_C2b_Proposal_Assisted_Runtime_Closure_0.2.1`
- Version: `0.2.1`
- Role: Worker candidate; independent Supervisor audit remains required.

## Build

After all machine gates pass, commit the clean Worker tree and run:

```powershell
& '.\.venv\Scripts\python.exe' '.\scripts\build_release.py'
```

The builder refuses a dirty worktree or a branch other than
`codex/phase-c2b-worker`. It writes the ZIP, SHA-256 sidecar, and external release
manifest under `dist\`. It recomputes the deterministic controlled-source digest
and refuses a passed summary produced for different source bytes.

## Pristine extraction verification

Extract the release ZIP into a new directory, change into its single wrapper
directory, and run one command:

```powershell
python .\scripts\verify_pristine.py
```

Before creating an environment or starting a subprocess, the bootstrap validates
the v2 candidate-manifest schema, identity, every declared path, size and SHA-256,
the absence of extra/missing files, and the controlled-source digest. It then
creates an extraction-local `.venv`, bounds environment setup subprocesses at
120 seconds, and bounds `verify_all.py` at 600 seconds. The final machine record
is `results\verification_summary.json`; raw gate logs are under `logs\`.
