# Proof Replay

A `VALID` log records the exact field/proposal identities, exact `r0`, package and
algorithm versions, work budgets, actual frozen Phase C.1 artifact hashes, field
and factor certificates, oracle transcript, and final decision. A canonical
SHA-256 root seals the complete log.

`scripts/run_proof_replay.py` writes a replay case and launches
`scripts/replay_proof_case.py` in a distinct process. The new process reconstructs
the exact deterministic input without access to the original engine object and
requires byte-equivalent canonical proof content. `scripts/run_proof_tamper.py`
re-seals changed verdict, numeric certificate, artifact hash, and factorization
certificate cases; every case must be rejected.
