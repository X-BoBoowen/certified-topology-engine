from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SETUP_TIMEOUT_SECONDS = 120
VERIFY_TIMEOUT_SECONDS = 600
CANDIDATE_NAME = 'Phase_C2b_Proposal_Assisted_Runtime_Closure_0.2.1'
CANDIDATE_VERSION = '0.2.1'
OUTER_SHA256 = '0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256 = '94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'


def _source_digest(records):
    encoded = json.dumps(
        records, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _manifest_path(text):
    if type(text) is not str or '\\' in text:
        raise RuntimeError('candidate manifest contains an invalid file path')
    path = PurePosixPath(text)
    if (
        not text
        or path.is_absolute()
        or path.as_posix() != text
        or any(part in ('', '.', '..') for part in path.parts)
        or text == 'CANDIDATE_MANIFEST.json'
    ):
        raise RuntimeError('candidate manifest contains an unsafe file path')
    return path


def verify_candidate_manifest(root):
    root = Path(root).resolve()
    manifest_path = root / 'CANDIDATE_MANIFEST.json'
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError('candidate manifest is missing or invalid JSON') from exc
    if type(manifest) is not dict or set(manifest) != {
        'schema','candidate_name','candidate_version','commit_sha',
        'frozen_phase_c1','controlled_source','files',
    }:
        raise RuntimeError('candidate manifest schema fields are invalid')
    if manifest['schema'] != 'phase-c2b-candidate-manifest-v2':
        raise RuntimeError('candidate manifest schema is unsupported')
    if (
        manifest['candidate_name'] != CANDIDATE_NAME
        or manifest['candidate_version'] != CANDIDATE_VERSION
        or type(manifest['commit_sha']) is not str
        or re.fullmatch(r'[0-9a-f]{40}', manifest['commit_sha']) is None
    ):
        raise RuntimeError('candidate manifest identity is invalid')
    if manifest['frozen_phase_c1'] != {
        'outer_sha256': OUTER_SHA256,
        'inner_sha256': INNER_SHA256,
    }:
        raise RuntimeError('candidate manifest frozen hashes are invalid')
    source = manifest['controlled_source']
    if (
        type(source) is not dict
        or set(source) != {'schema','sha256','file_count'}
        or source.get('schema') != 'phase-c2b-controlled-source-v1'
        or type(source.get('sha256')) is not str
        or re.fullmatch(r'[0-9a-f]{64}', source['sha256']) is None
        or type(source.get('file_count')) is not int
        or source['file_count'] < 1
    ):
        raise RuntimeError('candidate manifest controlled-source record is invalid')
    records = manifest['files']
    if type(records) is not list or not records:
        raise RuntimeError('candidate manifest file records are invalid')
    declared = {}
    for record in records:
        if type(record) is not dict or set(record) != {'path','sha256','size','role'}:
            raise RuntimeError('candidate manifest file record schema is invalid')
        path = _manifest_path(record['path'])
        if path.as_posix() in declared:
            raise RuntimeError('candidate manifest contains duplicate file paths')
        if (
            type(record['sha256']) is not str
            or re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is None
            or type(record['size']) is not int
            or record['size'] < 0
            or record['role'] not in ('source','evidence')
        ):
            raise RuntimeError('candidate manifest file record is invalid')
        declared[path.as_posix()] = record
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob('*')
        if path.is_file() and path != manifest_path
    }
    if set(declared) != actual_paths:
        raise RuntimeError('candidate manifest paths do not match the extracted tree')
    source_records = []
    for relative in sorted(declared):
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink():
            raise RuntimeError('candidate manifest rejects symbolic links')
        content = path.read_bytes()
        actual = {
            'path': relative,
            'sha256': hashlib.sha256(content).hexdigest(),
            'size': len(content),
        }
        record = declared[relative]
        if actual['sha256'] != record['sha256'] or actual['size'] != record['size']:
            raise RuntimeError(f'candidate manifest hash/size mismatch: {relative}')
        if record['role'] == 'source':
            source_records.append(actual)
    if (
        len(source_records) != source['file_count']
        or _source_digest(source_records) != source['sha256']
    ):
        raise RuntimeError('candidate manifest controlled-source digest mismatch')
    return manifest


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
    try:
        candidate_manifest = verify_candidate_manifest(ROOT)
    except RuntimeError as exc:
        print(
            json.dumps(
                {
                    'schema':'phase-c2b-pristine-preflight-v1',
                    'all_passed':False,
                    'error':str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
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
        'candidate_commit_sha': candidate_manifest['commit_sha'],
        'controlled_source_sha256': candidate_manifest['controlled_source']['sha256'],
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
