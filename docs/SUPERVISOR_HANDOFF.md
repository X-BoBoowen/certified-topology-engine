# Supervisor Handoff: Phase C.2b Independent Gate

## Role

You are the independent gate owner. Use the `main` checkout for governance and audit records. Do not implement fixes in the Worker candidate while auditing it.

Your decision must come from a fixed commit, a fixed archive, and fresh machine evidence rather than the Worker's explanation.

## Authoritative inputs

- `AGENTS.md`
- `docs/FROZEN_THEOREM_LEDGER.md`
- `docs/CURRENT_GATE_C2B.md`
- `docs/BASELINE_PROVENANCE.md`
- Worker candidate commit and archive, once supplied

The currently imported C.2a baseline is failed and must not be accepted.

## Audit order

1. Record the candidate filename, byte size, archive SHA-256, and full commit SHA.
2. Compare the candidate diff against the approved gate and flag scope expansion.
3. Create a new empty audit directory outside the Worker worktree.
4. Extract the archive without using Worker caches or `.venv`.
5. Install dependencies from the candidate's declared environment files.
6. Verify the frozen outer and inner hashes before running the engine.
7. Run the candidate's documented full verification command.
8. Independently run the critical narrow gates where useful.
9. Check proof replay and deliberate tampering.
10. Move or re-extract the package to a different path and repeat the relocation gate.
11. Compare raw logs, exit codes, semantic counts, summary JSON, and prose verdict.
12. Issue PASS or PIVOT with the first reproducible blocking evidence.

Read the Worker's explanatory narrative only after obtaining the first independent machine result.

## Required checks

- Archive and frozen artifact identity.
- Compilation and static undefined-name analysis.
- Scoped pytest collection.
- Property, general, invalid-input, and float-path suites.
- Expected general semantic counts and zero false-valid cases.
- Proof replay in a new process.
- Rejection of tampered proof-critical data.
- Relocation independence.
- Declared command and total timeouts.
- No hidden dependency on an absolute author-machine path.
- No weakening of exact-input or fail-closed semantics.
- No expansion from proposal-assisted to field-only claims.

## Immediate rejection conditions

- Any required non-zero exit code.
- Hash mismatch or unverified fallback artifact.
- Missing gate reported as PASS.
- Manual status text contradicting machine output.
- Tests deleted, skipped, or weakened without gate approval.
- Proof replay that merely reruns certification without validating the recorded proof.
- Candidate works only in the Worker directory.
- Timeout or budget exhaustion reported as VALID.
- Any false-valid case.

## Report format

Record:

1. Artifact identity.
2. Environment.
3. Commands, exit codes, and runtimes.
4. Prioritized technical findings.
5. Claim audit: supported, overstated, unsupported, or contradicted.
6. Final verdict.
7. The smallest permitted next repair scope if the verdict is PIVOT.

The formal failure verdict is:

`PIVOT — PACKAGING / RUNTIME CLOSURE FAILED`

The formal success verdict is:

`PASS — PHASE C.2B PACKAGING / RUNTIME CLOSURE ACCEPTED`

Do not use intermediate language such as “mostly passed” as the phase decision.
