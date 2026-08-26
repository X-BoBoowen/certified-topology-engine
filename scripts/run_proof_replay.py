from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from phase_c2a import EngineStatus, GeneralReachEngine
from phase_c2a.scenarios import base_circle_scenarios, make_field


ENGINE_BUDGETS = {
    'pieces_per_quarter': 4,
    'max_depth': 80,
    'max_boxes': 500_000,
}


def build_case():
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    engine = GeneralReachEngine(**ENGINE_BUDGETS)
    result = engine.certify(field, scenario.r0, proposal)
    case = {
        'schema': 'phase-c2b-replay-case-v1',
        'scenario_name': scenario.name,
        'r0': str(scenario.r0),
        'engine_budgets': ENGINE_BUDGETS,
        'proof_log': result.data.get('proof_log'),
    }
    return result, case


def run_replay_worker(case_path):
    try:
        process = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'replay_proof_case.py'), str(case_path)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, {'accepted': False, 'error': 'proof replay timed out'}, exc.stdout or ''
    try:
        output = json.loads(process.stdout)
    except json.JSONDecodeError:
        output = {'accepted': False, 'error': 'invalid replay-worker output'}
    return process.returncode, output, process.stdout


def main():
    results_dir = ROOT / 'results'
    results_dir.mkdir(exist_ok=True)
    result, case = build_case()
    case_path = results_dir / 'proof_replay_case.json'
    case_path.write_text(json.dumps(case, indent=2, sort_keys=True), encoding='utf-8')
    exit_code, replay, worker_output = run_replay_worker(case_path)
    output = {
        'source_status': result.status.value,
        'original_replay': replay.get('accepted') is True,
        'proof_root_hash': (case.get('proof_log') or {}).get('root_hash'),
        'generator_pid': os.getpid(),
        'replay_pid': replay.get('replay_pid'),
        'replay_exit_code': exit_code,
        'worker_output': worker_output,
    }
    (results_dir / 'proof_replay.json').write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding='utf-8'
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    passed = (
        result.status is EngineStatus.VALID
        and output['original_replay']
        and output['generator_pid'] != output['replay_pid']
        and exit_code == 0
    )
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
