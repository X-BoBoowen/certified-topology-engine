from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETUP_TIMEOUT_SECONDS = 120
VERIFY_TIMEOUT_SECONDS = 600


def run_step(command, cwd, timeout_seconds):
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_seconds,
        )
        exit_code = process.returncode
        output = process.stdout
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        output = exc.stdout or ''
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
        output += f'\nTIMEOUT after {timeout_seconds} seconds\n'
        timed_out = True
    return {
        'command': [str(part) for part in command],
        'exit_code': exit_code,
        'output': output,
        'runtime_seconds': time.perf_counter() - started,
        'timed_out': timed_out,
        'timeout_seconds': timeout_seconds,
    }


def venv_python_path():
    if sys.platform == 'win32':
        return ROOT / '.venv' / 'Scripts' / 'python.exe'
    return ROOT / '.venv' / 'bin' / 'python'


def main():
    logs_dir = ROOT / 'logs'
    results_dir = ROOT / 'results'
    logs_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    steps = {}
    python = venv_python_path()
    if python.is_file():
        steps['create_venv'] = {
            'command': [],
            'exit_code': 0,
            'output': 'existing local .venv reused',
            'runtime_seconds': 0.0,
            'timed_out': False,
            'timeout_seconds': SETUP_TIMEOUT_SECONDS,
        }
    else:
        steps['create_venv'] = run_step(
            [sys.executable, '-m', 'venv', str(ROOT / '.venv')],
            ROOT,
            SETUP_TIMEOUT_SECONDS,
        )
    if steps['create_venv']['exit_code'] == 0:
        steps['install_requirements'] = run_step(
            [str(python), '-m', 'pip', 'install', '-r', 'requirements.txt'],
            ROOT,
            SETUP_TIMEOUT_SECONDS,
        )
    else:
        steps['install_requirements'] = {
            'command': [],
            'exit_code': 1,
            'output': 'not run because virtual environment creation failed',
            'runtime_seconds': 0.0,
            'timed_out': False,
            'timeout_seconds': SETUP_TIMEOUT_SECONDS,
        }
    if steps['install_requirements']['exit_code'] == 0:
        steps['verify_all'] = run_step(
            [str(python), 'scripts/verify_all.py'],
            ROOT,
            VERIFY_TIMEOUT_SECONDS,
        )
    else:
        steps['verify_all'] = {
            'command': [],
            'exit_code': 1,
            'output': 'not run because dependency installation failed',
            'runtime_seconds': 0.0,
            'timed_out': False,
            'timeout_seconds': VERIFY_TIMEOUT_SECONDS,
        }
    all_passed = all(step['exit_code'] == 0 for step in steps.values())
    summary = {
        'schema': 'phase-c2b-pristine-bootstrap-v1',
        'steps': {
            name: {key: value for key, value in step.items() if key != 'output'}
            for name, step in steps.items()
        },
        'all_passed': all_passed,
    }
    (results_dir / 'pristine_bootstrap.json').write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8'
    )
    log_sections = []
    for name, step in steps.items():
        log_sections.extend(
            [
                f'===== {name} =====',
                json.dumps(
                    {key: value for key, value in step.items() if key != 'output'},
                    indent=2,
                    sort_keys=True,
                ),
                step['output'].rstrip(),
            ]
        )
    log_sections.append(json.dumps(summary, indent=2, sort_keys=True))
    (logs_dir / 'VERIFY_PRISTINE_BOOTSTRAP.txt').write_text(
        '\n'.join(log_sections) + '\n', encoding='utf-8'
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all_passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
