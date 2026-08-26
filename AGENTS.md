# Phase C.2b Repository Instructions

These instructions apply to the entire repository.

## Mission

Close the packaging and runtime verification loop for the proposal-assisted Phase C.2a engine without expanding its mathematical or application scope.

## Coding principles

1. Think before coding. State assumptions, ambiguities, and trade-offs before implementation.
2. Make the smallest change that satisfies the current gate.
3. Touch only files directly related to the reproduced failure or required verification.
4. Define success through executable checks and continue until the observed evidence matches the claim.
5. Investigate root cause before proposing a fix. Preserve the failing reproduction.

## Immutable inputs

- Never modify `../aaa/`.
- The imported C.2a baseline is identified by commit `3b8c4eed06810f3f33f4c01fefc87de3f2521a16`.
- The source archive SHA-256 is `CFA83CCEE4D689E6FD936D486EB8C7241E58D027B555BDA82DEAD79D90C96DD2`.
- The frozen Phase C.1 outer and inner artifacts must retain the hashes specified in `docs/CURRENT_GATE_C2B.md`.

## Mathematical and numerical boundaries

- Certificate inputs remain exact built-in integers or `fractions.Fraction`; ordinary binary floats must not enter a VALID proof chain.
- The engine remains proposal-assisted. Candidate-free calls return `UNKNOWN`.
- A failed proof obligation, exhausted budget, invalid input, hash mismatch, or replay mismatch must fail closed.
- Do not weaken strict inequalities, scenario expectations, proof replay, or tamper rejection to obtain a passing result.
- Do not claim certification of raw pixel masks, arbitrary spline fields, complete topology, homeomorphism, or isotopy.

## Role separation

- `main` is the Supervisor checkout. After initialization, do not implement source fixes directly on `main`.
- `codex/phase-c2b-worker` is the Worker branch. Source and test fixes belong there.
- The Worker may report only `self-verification passed; awaiting independent audit`.
- Only the Supervisor may record formal Phase C.2b acceptance, after auditing a fixed commit and pristine archive.
- The Supervisor must not repair the candidate while auditing it. Findings return to the Worker as reproducible failures.

## Required workflow

1. Read `docs/FROZEN_THEOREM_LEDGER.md`, `docs/CURRENT_GATE_C2B.md`, and the role-specific handoff.
2. Reproduce the relevant baseline failure before editing.
3. Add or tighten a regression test before each bug fix.
4. Make one root-cause fix at a time.
5. Run the narrow test, then the full machine gate.
6. Commit a fixed candidate and identify it by full commit SHA and archive SHA-256.
7. Re-extract the archive in a fresh directory for the independent audit.

## Environment

- Use Python 3.11 or newer.
- Create a local `.venv` and install `requirements.txt`; do not rely on global packages.
- Generated caches and `.worktrees/` stay untracked.
- Do not add a GitHub remote unless the user explicitly supplies or authorizes one.

## Completion language

- Any non-zero required gate means the phase is not accepted.
- Worker success wording: `SELF-VERIFICATION PASS — INDEPENDENT AUDIT PENDING`.
- Supervisor failure wording: `PIVOT — PACKAGING / RUNTIME CLOSURE FAILED`.
- Supervisor success wording: `PASS — PHASE C.2B PACKAGING / RUNTIME CLOSURE ACCEPTED`.
