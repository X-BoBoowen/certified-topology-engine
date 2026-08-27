from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from phase_c2a import __version__
from phase_c2a.source_integrity import controlled_source_snapshot
from phase_c2a.verification_runtime import (
    run_bounded_command,
    verification_commands,
)


OVERALL_TIMEOUT_SECONDS = 600
GENERAL_COUNT_KEYS = (
    'circle_scenarios',
    'circle_valid',
    'circle_false_valid',
    'circle_failures',
    'knot_scenarios',
    'knot_valid',
    'knot_failures',
)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return {'error': repr(exc)}


def semantic_counts_gate(general_result):
    return (
        general_result.get('circle_scenarios') == 22
        and general_result.get('circle_failures') == 0
        and general_result.get('circle_false_valid') == 0
        and general_result.get('circle_valid', 0) > 0
        and general_result.get('knot_scenarios') == 9
        and general_result.get('knot_failures') == 0
    )


def overall_timeout_record(spec, logs_dir):
    log_path = logs_dir / f"VERIFY_{spec['name'].upper()}.txt"
    log_path.write_text(
        '\n'.join(
            [
                f"COMMAND={json.dumps(spec['command'])}",
                f"TIMEOUT_SECONDS={spec['timeout_seconds']}",
                'NOT RUN: complete verification budget exhausted',
                'EXIT_CODE=124',
                'RUNTIME_SECONDS=0.000000',
                '',
            ]
        ),
        encoding='utf-8',
    )
    return {
        'command': spec['command'],
        'exit_code': 124,
        'runtime_seconds': 0.0,
        'timed_out': True,
        'timeout_seconds': spec['timeout_seconds'],
        'log_path': str(log_path),
    }


def main():
    source_before = controlled_source_snapshot(ROOT)
    logs_dir = ROOT / 'logs'
    results_dir = ROOT / 'results'
    logs_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    started = time.perf_counter()
    command_records = {}
    for spec in verification_commands(ROOT, sys.executable):
        remaining = OVERALL_TIMEOUT_SECONDS - (time.perf_counter() - started)
        if remaining <= 0:
            record = overall_timeout_record(spec, logs_dir)
        else:
            timeout_seconds = min(spec['timeout_seconds'], remaining)
            record = run_bounded_command(
                spec['name'],
                spec['command'],
                ROOT,
                logs_dir,
                timeout_seconds,
            )
        record['log_path'] = Path(record['log_path']).relative_to(ROOT).as_posix()
        command_records[spec['name']] = record

    overall_runtime = time.perf_counter() - started
    source_after = controlled_source_snapshot(ROOT)
    source_stable = source_before == source_after
    general_exit_zero = command_records['general_suite']['exit_code'] == 0
    general_result = (
        load_json(results_dir / 'general_suite.json') if general_exit_zero else {}
    )
    semantic_gate = general_exit_zero and semantic_counts_gate(general_result)
    commands_passed = all(
        record['exit_code'] == 0 for record in command_records.values()
    )
    overall_bounded = overall_runtime <= OVERALL_TIMEOUT_SECONDS
    all_passed = (
        commands_passed and semantic_gate and overall_bounded and source_stable
    )
    worker_status = (
        'SELF-VERIFICATION PASS — INDEPENDENT AUDIT PENDING'
        if all_passed
        else 'PIVOT — PACKAGING / RUNTIME CLOSURE FAILED'
    )
    summary = {
        'schema': 'phase-c2b-verification-summary-v2',
        'package_version': __version__,
        'controlled_source': source_after,
        'controlled_source_stable_gate': source_stable,
        'python': sys.version,
        'platform': platform.platform(),
        'commands': command_records,
        'general_semantic_gate': semantic_gate,
        'general_counts': {
            key: general_result.get(key) for key in GENERAL_COUNT_KEYS
        },
        'overall_timeout_seconds': OVERALL_TIMEOUT_SECONDS,
        'overall_runtime_seconds': overall_runtime,
        'overall_bounded_gate': overall_bounded,
        'field_only_loop_discovery': (
            'NOT_IMPLEMENTED; candidate-free calls return UNKNOWN'
        ),
        'all_passed': all_passed,
        'worker_status': worker_status,
    }
    summary_json = json.dumps(summary, indent=2, sort_keys=True)
    (results_dir / 'verification_summary.json').write_text(
        summary_json, encoding='utf-8'
    )
    (ROOT / 'FINAL_VERDICT.txt').write_text(
        f'{worker_status}\n', encoding='utf-8'
    )
    exit_code = 0 if all_passed else 1
    (results_dir / 'VERIFY_ALL_EXIT_CODE.txt').write_text(
        f'{exit_code}\n', encoding='utf-8'
    )
    (logs_dir / 'FINAL_STAGING_VERIFY_ALL.txt').write_text(
        f'{summary_json}\nEXIT_CODE={exit_code}\n', encoding='utf-8'
    )
    print(summary_json)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
