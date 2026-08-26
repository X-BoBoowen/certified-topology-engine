from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from phase_c2a.proof_log import seal
from run_proof_replay import build_case, run_replay_worker


def tampered_logs(original):
    cases = {}
    changed = copy.deepcopy(original)
    changed['decision'] = 'UNKNOWN'
    cases['decision'] = seal(changed)
    changed = copy.deepcopy(original)
    changed['r0'] = '3/2'
    cases['numeric_certificate'] = seal(changed)
    changed = copy.deepcopy(original)
    changed['frozen_phase_c1']['outer_sha256'] = '0' * 64
    cases['artifact_hash'] = seal(changed)
    changed = copy.deepcopy(original)
    changed['zero_set_certificate']['factor_hash'] = '0' * 64
    cases['factorization_certificate'] = seal(changed)
    return cases


def main():
    results_dir = ROOT / 'results'
    results_dir.mkdir(exist_ok=True)
    source_result, base_case = build_case()
    rejections = {}
    details = {}
    for name, proof_log in tampered_logs(base_case['proof_log']).items():
        case = copy.deepcopy(base_case)
        case['proof_log'] = proof_log
        case_path = results_dir / f'proof_tamper_case_{name}.json'
        case_path.write_text(json.dumps(case, indent=2, sort_keys=True), encoding='utf-8')
        exit_code, replay, worker_output = run_replay_worker(case_path)
        rejected = exit_code == 1 and replay.get('accepted') is False
        rejections[name] = rejected
        details[name] = {
            'exit_code': exit_code,
            'replay_pid': replay.get('replay_pid'),
            'worker_output': worker_output,
        }
    output = {
        'source_status': source_result.status.value,
        'tamper_rejections': rejections,
        'details': details,
    }
    (results_dir / 'proof_tamper.json').write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding='utf-8'
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if rejections and all(rejections.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
