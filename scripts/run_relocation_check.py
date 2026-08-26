from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'


def main():
    RESULTS.mkdir(exist_ok=True)
    scratch = ROOT / 'audit' / 'tmp'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='phase-c2b-relocation-', dir=scratch) as temp_dir:
        relocated_root = Path(temp_dir) / 'candidate'
        shutil.copytree(
            ROOT,
            relocated_root,
            ignore=shutil.ignore_patterns(
                '.git',
                '.venv',
                '__pycache__',
                '.pytest_cache',
                'audit',
                'dist',
                'logs',
                'results',
            ),
        )
        try:
            process = subprocess.run(
                [sys.executable, str(relocated_root / 'scripts' / 'run_proof_replay.py')],
                cwd=relocated_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
            )
            replay_exit_code = process.returncode
            replay_output = process.stdout
        except subprocess.TimeoutExpired as exc:
            replay_exit_code = 124
            replay_output = exc.stdout or ''
            if isinstance(replay_output, bytes):
                replay_output = replay_output.decode('utf-8', errors='replace')
        replay_path = relocated_root / 'results' / 'proof_replay.json'
        try:
            replay = json.loads(replay_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            replay = {'original_replay': False}
        output = {
            'source_root': str(ROOT.resolve()),
            'relocated_root': str(relocated_root.resolve()),
            'proof_replay_exit_code': replay_exit_code,
            'proof_replay': replay,
            'raw_output': replay_output,
        }
    (RESULTS / 'relocation.json').write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding='utf-8'
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    passed = (
        output['source_root'] != output['relocated_root']
        and output['proof_replay_exit_code'] == 0
        and output['proof_replay'].get('original_replay') is True
    )
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
