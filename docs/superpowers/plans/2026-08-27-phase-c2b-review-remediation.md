# Phase C.2b Review Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a new 0.2.1 candidate whose proof replay is exact-input self-contained, whose production VALID path delegates to the verified frozen oracle, and whose evidence is cryptographically bound to the packaged source.

**Architecture:** Add strict canonical reconstruction alongside the existing canonical field and proposal encodings, then make replay consume only that serialized input. Replace the simulated production oracle transcript with a real bounded frozen `ReachEngine` result. Bind `verify_all`, release construction, and pristine bootstrap through a deterministic controlled-source digest and a strict pre-execution manifest validator.

**Tech Stack:** Python 3.12, `fractions.Fraction`, pytest, stdlib JSON/SHA-256/ZIP/subprocess.

**Spec:** `docs/CURRENT_GATE_C2B.md` plus the 2026-08-27 independent read-only review supplied by the user.

## Global Constraints

- Work only in `.worktrees/phase-c2b-worker` on `codex/phase-c2b-worker`.
- Do not edit `main`, `aaa`, or either frozen Phase C.1 artifact.
- Preserve exact rational inputs, strict inequalities, fail-closed semantics, semantic counts, proof replay, and all 120/600 second limits.
- Remain proposal-assisted; candidate-free calls return `UNKNOWN`.
- Use version `0.2.1`; do not reuse the withdrawn `0.2.0` candidate identity or evidence.

---

### Task 1: Self-contained exact-input proof cases

**Files:**
- Create: `phase_c2a/exact_serialization.py`
- Modify: `scripts/run_proof_replay.py`
- Modify: `scripts/replay_proof_case.py`
- Test: `tests/test_proof_replay.py`
- Test: `tests/test_verification_scripts.py`

**Interfaces:**
- Produces: `serialize_exact_input(field, proposal, r0) -> dict` and `deserialize_exact_input(record) -> tuple[field, proposal, Fraction]`.
- The record contains exact field breakpoints, every polynomial coefficient, proposal circles and multipliers, exact `r0`, plus field/proposal hashes.

- [ ] Add tests asserting literal canonical record content and round-trip hashes.
- [ ] Run the tests and record the expected failure because reconstruction APIs and `exact_input` are absent.
- [ ] Implement strict schema/type/key checking and canonical round-trip validation.
- [ ] Replace `scenario_name` replay with reconstruction from `exact_input` only.
- [ ] Copy the replay runtime without `phase_c2a/scenarios.py` and verify an existing case still replays.
- [ ] Run the narrow proof replay tests and record green evidence.

### Task 2: Real frozen-oracle production delegation

**Files:**
- Modify: `phase_c2a/engine.py`
- Modify: `scripts/run_general_suite.py`
- Test: `tests/test_frozen_artifacts.py`
- Test: `tests/test_proof_replay.py`

**Interfaces:**
- Consumes: `load_frozen_module()` and the engine's existing `pieces_per_quarter`, `max_depth`, and `max_boxes` budgets.
- Produces: a proof-log `oracle` record containing the real frozen status, reason, deterministic stats, budgets, and an `oracle_numeric_certificate` derived from the real result.

- [ ] Add tests proving a production VALID call reaches the frozen `ReachEngine` with the requested budgets.
- [ ] Add tests proving loader failure, oracle exception/timeout, non-VALID output, and inconsistent output cannot produce VALID.
- [ ] Run the tests and record failures against the simulated analytic transcript.
- [ ] Load the hash-verified module, create frozen circles from exact proposal values, call the real engine, validate its result, and map all failures closed.
- [ ] Remove the local analytic circle decision as a substitute oracle.
- [ ] Make the general suite check the real production transcript without a redundant decision oracle.
- [ ] Run narrow engine/general tests and record green evidence.

### Task 3: Real numeric-certificate tamper rejection

**Files:**
- Modify: `scripts/run_proof_tamper.py`
- Modify: `tests/test_proof_replay.py`
- Modify: `tests/test_verification_scripts.py`

**Interfaces:**
- Consumes: `oracle_numeric_certificate` in the sealed proof log.
- Produces: separate `r0_exact_input` and `numeric_certificate` tamper cases.

- [ ] Add a test requiring distinct exact-input and numeric-certificate mutations.
- [ ] Run it and record failure because the old numeric case mutates `r0`.
- [ ] Mutate and reseal one real oracle numeric count while retaining a separate exact `r0` case.
- [ ] Run the independent replay tamper gate and record green evidence.

### Task 4: Source/evidence binding and pristine preflight

**Files:**
- Create: `phase_c2a/source_integrity.py`
- Modify: `scripts/verify_all.py`
- Modify: `scripts/build_release.py`
- Modify: `scripts/verify_pristine.py`
- Modify: `tests/test_verification_scripts.py`

**Interfaces:**
- Produces: `controlled_source_records(root)` and `controlled_source_digest(root)` over code, tests, scripts, static docs/config, and frozen artifacts, excluding generated results/logs.
- The verification summary and v2 candidate manifest contain the identical controlled-source SHA-256 and file count.
- `verify_candidate_manifest(root)` performs strict schema/path/size/hash/extra-file checks before any environment or verification subprocess.

- [ ] Add negative tests for a stale passed summary paired with changed source, malformed manifest, missing/extra paths, and a modified packaged file.
- [ ] Run them and record the expected failures against the unbound v1 flow.
- [ ] Implement deterministic records/digest and record it before/after `verify_all`.
- [ ] Require exact digest equality in the builder and write it with commit identity to the v2 manifest.
- [ ] Implement a stdlib-only manifest preflight and invoke it before creating `.venv`, logs, results, or any subprocess.
- [ ] Run the narrow release/pristine tests and record green evidence.

### Task 5: Nested subprocess timeout

**Files:**
- Modify: `tests/test_import_environment.py`

**Interfaces:**
- The clean-working-directory subprocess has `timeout=120`; `TimeoutExpired` is converted into an explicit assertion failure.

- [ ] Add the bounded timeout and explicit failure handling.
- [ ] Run `tests/test_import_environment.py` and record green evidence.

### Task 6: Versioned verification and release

**Files:**
- Modify: `phase_c2a/version.py`
- Modify: release documentation and machine-generated `logs/`/`results/` evidence.

**Interfaces:**
- Produces candidate `Phase_C2b_Proposal_Assisted_Runtime_Closure_0.2.1`, its v2 manifest, deterministic archive, and pristine bootstrap evidence.

- [ ] Change package/candidate version to `0.2.1` and update version-specific assertions/docs.
- [ ] Run compilation, static checking, scoped pytest, semantic suites, invalid/float audits, proof replay/tamper, frozen hashes, relocation, and the overall 600-second gate.
- [ ] Commit source and fresh evidence, then build the clean-worktree 0.2.1 archive.
- [ ] Extract into a new empty directory and run the single pristine verification command.
- [ ] Independently inspect manifest records, machine summary, all raw logs, semantic counts, timeouts, commit identity, archive SHA-256, and frozen hashes.
- [ ] Commit any final tracked evidence update, confirm a clean worktree, and report only Worker self-verification status.
