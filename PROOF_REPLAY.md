# Proof Replay

A VALID log records exact field/proposal hashes, frozen Phase C.1 hashes, all field and factor certificates, the oracle transcript and the final decision. A canonical SHA-256 root seals the full log. Replay re-runs the complete certification from the original exact field and proposal and requires byte-equivalent canonical log content; changing a decision or certificate invalidates replay.
