# Proof Replay

A `VALID` log records the exact field/proposal hashes, exact `r0`, package and
algorithm versions, work budgets, actual frozen Phase C.1 artifact hashes, field
and factor certificates, the real frozen-oracle status/reason/deterministic
stats, an oracle numeric certificate, and the final decision. A canonical SHA-256
root seals the complete log.

`scripts/run_proof_replay.py` writes a replay case and launches
`scripts/replay_proof_case.py` in a distinct process. The replay case contains
all exact field breakpoints, every piecewise-polynomial coefficient, every
proposal circle and multiplier, exact `r0`, and both input hashes. The new process
reconstructs only from those values; it does not import scenario factories or
fixtures. It rechecks both hashes and requires byte-equivalent canonical proof
content. `scripts/run_proof_tamper.py` separately changes exact `r0` and a real
numeric-certificate count, and also re-seals changed verdict, artifact-hash, and
factorization-certificate cases; every case must be rejected.
