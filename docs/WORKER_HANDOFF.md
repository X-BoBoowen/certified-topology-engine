# Worker Handoff: Phase C.2b Runtime Closure

## Role

You are the implementation owner. Work only in the `codex/phase-c2b-worker` worktree. You may change source, tests, configuration, and packaging files within the scope of `docs/CURRENT_GATE_C2B.md`.

You do not have authority to formally accept the phase.

## Starting point

- Supervisor checkout: repository root on `main`.
- Worker checkout: `.worktrees/phase-c2b-worker`.
- Failed baseline commit: `3b8c4eed06810f3f33f4c01fefc87de3f2521a16`.
- Fresh failed-baseline evidence: `audit/baseline/2026-08-26/`.
- Mathematical interface: `docs/FROZEN_THEOREM_LEDGER.md`.
- Binding implementation scope: `docs/CURRENT_GATE_C2B.md`.

The baseline is intentionally failed. Do not interpret its non-zero verification result as a setup error.

## Supported engine scope

The engine is proposal-assisted. It proves exact cellwise factorization `F_c = h_c G`, proves `h_c > 0`, and delegates analytic circle-link reach certification to frozen Phase C.1 artifacts. Candidate-free requests return `UNKNOWN`.

Do not turn C.2b into field-only loop discovery or a real-data system.

## Reproduced failures

- pytest exits 2 because duplicate frozen tests are recursively collected and produce four import-file mismatches.
- general suite exits 1 at `phase_c2a/engine.py` because `frozen_outer` is undefined.
- proof replay exits 1 at the same undefined name.
- general semantic counts are absent, so the semantic gate is false.
- compile, property, invalid-input, and float-path gates pass in the reproduced baseline.

## Required working method

1. Create a local `.venv` in the Worker worktree and install `requirements.txt`.
2. Run the failing narrow command before editing.
3. Trace the failure to its root cause.
4. Add a regression test that fails for the observed reason.
5. Implement the smallest repair.
6. Run the narrow test and inspect the full output.
7. Continue one failure class at a time.
8. Add the remaining static, timeout, replay-tamper, relocation, and hash gates.
9. Run the complete self-verification from a pristine archive extraction.
10. Commit the candidate and report its full commit SHA and archive SHA-256.

## Prohibitions

- Do not edit `../aaa/`.
- Do not change frozen artifact bytes or accepted hashes.
- Do not relax exact input rules.
- Do not weaken or remove adversarial scenarios.
- Do not catch broad exceptions merely to force exit code zero.
- Do not hand-edit `all_passed` or a PASS verdict.
- Do not modify `main`.
- Do not claim that proposal-assisted success establishes a field-only general engine.

## Required handoff to Supervisor

Provide exactly:

- Candidate name and version.
- Full commit SHA.
- Release archive path and SHA-256.
- One pristine-extraction verification command.
- Machine-readable summary and raw logs.
- Known limitations.
- A concise list of source changes and their regression evidence.

If local gates all pass, use only:

`SELF-VERIFICATION PASS — INDEPENDENT AUDIT PENDING`

If any required gate fails, use:

`PIVOT — PACKAGING / RUNTIME CLOSURE FAILED`
