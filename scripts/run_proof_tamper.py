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


def tampered_cases(base_case):
    cases = {}
    changed_case = copy.deepcopy(base_case)
    changed_case['proof_log']['decision'] = 'UNKNOWN'
    changed_case['proof_log'] = seal(changed_case['proof_log'])
    cases['decision'] = changed_case

    changed_case = copy.deepcopy(base_case)
    changed_case['exact_input']['r0'] = '3/2'
    cases['r0_exact_input'] = changed_case

    changed_case = copy.deepcopy(base_case)
    changed_case['proof_log']['oracle_numeric_certificate']['interval_boxes'] += 1
    changed_case['proof_log'] = seal(changed_case['proof_log'])
    cases['numeric_certificate'] = changed_case

    changed_case = copy.deepcopy(base_case)
    changed_case['proof_log']['frozen_phase_c1']['outer_sha256'] = '0' * 64
    changed_case['proof_log'] = seal(changed_case['proof_log'])
    cases['artifact_hash'] = changed_case

    changed_case = copy.deepcopy(base_case)
    changed_case['proof_log']['zero_set_certificate']['factor_hash'] = '0' * 64
    changed_case['proof_log'] = seal(changed_case['proof_log'])
    cases['factorization_certificate'] = changed_case
    return cases


def main():
    results_dir = ROOT / 'results'
    results_dir.mkdir(exist_ok=True)
    source_result, base_case = build_case()
    (results_dir / 'proof_tamper_base_case.json').write_text(
        json.dumps(base_case, indent=2, sort_keys=True), encoding='utf-8'
    )
    rejections = {}
    details = {}
    for name, case in tampered_cases(base_case).items():
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
