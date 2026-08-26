from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


COMMAND_TIMEOUT_SECONDS = 120


def verification_commands(root, python):
    root = Path(root)
    python = str(python)
    commands = [
        ('py_compile', [python, '-m', 'compileall', '-q', 'phase_c2a', 'tests', 'scripts']),
        ('static_undefined', [python, 'scripts/run_static_undefined_check.py']),
        ('pytest', [python, '-m', 'pytest', '-q', 'tests']),
        ('property_suite', [python, 'scripts/run_property_suite.py']),
        ('general_suite', [python, 'scripts/run_general_suite.py']),
        ('invalid_suite', [python, 'scripts/run_invalid_suite.py']),
        ('float_path_audit', [python, 'scripts/run_float_path_audit.py']),
        ('proof_replay', [python, 'scripts/run_proof_replay.py']),
        ('proof_tamper', [python, 'scripts/run_proof_tamper.py']),
        ('frozen_artifact_hash', [python, 'scripts/run_frozen_hash_check.py']),
        ('relocation', [python, 'scripts/run_relocation_check.py']),
    ]
    return [
        {
            'name': name,
            'command': command,
            'cwd': str(root),
            'timeout_seconds': COMMAND_TIMEOUT_SECONDS,
        }
        for name, command in commands
    ]


def run_bounded_command(name, command, cwd, logs_dir, timeout_seconds):
    cwd = Path(cwd)
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    timed_out = False
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
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        output = exc.stdout or ''
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
        output += f'\nTIMEOUT after {timeout_seconds} seconds\n'
    runtime = time.perf_counter() - started
    log_path = logs_dir / f'VERIFY_{name.upper()}.txt'
    log_path.write_text(
        '\n'.join(
            [
                f'COMMAND={json.dumps([str(part) for part in command])}',
                f'TIMEOUT_SECONDS={timeout_seconds}',
                output.rstrip(),
                f'EXIT_CODE={exit_code}',
                f'RUNTIME_SECONDS={runtime:.6f}',
                '',
            ]
        ),
        encoding='utf-8',
    )
    return {
        'command': [str(part) for part in command],
        'exit_code': exit_code,
        'runtime_seconds': runtime,
        'timed_out': timed_out,
        'timeout_seconds': timeout_seconds,
        'log_path': str(log_path),
    }
