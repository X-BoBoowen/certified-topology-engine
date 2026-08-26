from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_VERSION = '0.2.0'
CANDIDATE_NAME = 'Phase_C2b_Proposal_Assisted_Runtime_Closure_0.2.0'
OUTER_SHA256 = '0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256 = '94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'


ROOT_FILES = (
    'AGENTS.md',
    'BOUNDARY_ZERO_FREE_CERTIFICATE.md',
    'FROZEN_PHASE_C1_HASHES.txt',
    'FINAL_VERDICT.txt',
    'GENERAL_FIELD_INPUT_CONTRACT.md',
    'KNOWN_LIMITATIONS.md',
    'PHASE_C2A_RESEARCH_STATUS.md',
    'PROOF_REPLAY.md',
    'PROPOSAL_ASSISTED_SCOPE.md',
    'README.md',
    'SCENARIO_TEST_MAPPING.md',
    'pyproject.toml',
    'requirements.txt',
)
FROZEN_FILES = (
    'frozen_phase_c1/Phase_C1_Exact_Input_Soundness_Repair_Bundle_20260823.zip',
    'frozen_phase_c1/phase_c_reach_engine_prototype.zip',
)
REQUIRED_LOG_FILES = (
    'logs/FINAL_STAGING_VERIFY_ALL.txt',
    'logs/VERIFY_FLOAT_PATH_AUDIT.txt',
    'logs/VERIFY_FROZEN_ARTIFACT_HASH.txt',
    'logs/VERIFY_GENERAL_SUITE.txt',
    'logs/VERIFY_INVALID_SUITE.txt',
    'logs/VERIFY_PROOF_REPLAY.txt',
    'logs/VERIFY_PROOF_TAMPER.txt',
    'logs/VERIFY_PROPERTY_SUITE.txt',
    'logs/VERIFY_PY_COMPILE.txt',
    'logs/VERIFY_PYTEST.txt',
    'logs/VERIFY_RELOCATION.txt',
    'logs/VERIFY_STATIC_UNDEFINED.txt',
)
REQUIRED_RESULT_FILES = (
    'results/VERIFY_ALL_EXIT_CODE.txt',
    'results/float_path_audit.json',
    'results/frozen_artifacts.json',
    'results/general_suite.json',
    'results/invalid_suite.json',
    'results/proof_replay.json',
    'results/proof_tamper.json',
    'results/property_suite.json',
    'results/relocation.json',
    'results/verification_summary.json',
)
REQUIRED_COMMANDS = {
    'py_compile',
    'static_undefined',
    'pytest',
    'property_suite',
    'general_suite',
    'invalid_suite',
    'float_path_audit',
    'proof_replay',
    'proof_tamper',
    'frozen_artifact_hash',
    'relocation',
}


def release_files(root):
    root = Path(root)
    paths = [
        root / relative
        for relative in [
            *ROOT_FILES,
            *FROZEN_FILES,
            *REQUIRED_LOG_FILES,
            *REQUIRED_RESULT_FILES,
        ]
    ]
    for directory, pattern in (
        ('docs', '*.md'),
        ('phase_c2a', '*.py'),
        ('scripts', '*.py'),
        ('tests', '*.py'),
        ('logs', '*.txt'),
    ):
        paths.extend((root / directory).rglob(pattern))
    paths.extend((root / 'results').glob('*.json'))
    paths.extend((root / 'results').glob('*.txt'))
    unique = sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())
    missing = [path for path in unique if not path.is_file()]
    if missing:
        raise RuntimeError(f'missing release file: {missing[0]}')
    return unique


def approved_frozen_hashes(root):
    root = Path(root)
    outer = root / FROZEN_FILES[0]
    inner = root / FROZEN_FILES[1]
    hashes = {
        'outer_sha256': hashlib.sha256(outer.read_bytes()).hexdigest(),
        'inner_sha256': hashlib.sha256(inner.read_bytes()).hexdigest(),
    }
    if hashes != {
        'outer_sha256': OUTER_SHA256,
        'inner_sha256': INNER_SHA256,
    }:
        raise RuntimeError('frozen Phase C.1 artifact hash mismatch')
    return hashes


def zip_info(name):
    info = zipfile.ZipInfo(name, date_time=(2026, 8, 26, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def create_release_archive(root, archive_path, commit_sha):
    root = Path(root).resolve()
    archive_path = Path(archive_path).resolve()
    files = release_files(root)
    frozen_hashes = approved_frozen_hashes(root)
    summary = json.loads(
        (root / 'results' / 'verification_summary.json').read_text(encoding='utf-8')
    )
    commands = summary.get('commands', {})
    summary_is_passed = (
        summary.get('all_passed') is True
        and summary.get('worker_status')
        == 'SELF-VERIFICATION PASS — INDEPENDENT AUDIT PENDING'
        and summary.get('general_semantic_gate') is True
        and summary.get('overall_bounded_gate') is True
        and set(commands) == REQUIRED_COMMANDS
        and all(record.get('exit_code') == 0 for record in commands.values())
        and all(
            0 < record.get('timeout_seconds', 0) <= 120
            for record in commands.values()
        )
        and (root / 'results' / 'VERIFY_ALL_EXIT_CODE.txt').read_text().strip()
        == '0'
        and (root / 'FINAL_VERDICT.txt').read_text(encoding='utf-8').strip()
        == summary.get('worker_status')
    )
    if not summary_is_passed:
        raise RuntimeError('verification summary is not passed or is inconsistent')
    file_records = []
    contents = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        contents[relative] = content
        file_records.append(
            {
                'path': relative,
                'sha256': hashlib.sha256(content).hexdigest(),
                'size': len(content),
            }
        )
    manifest = {
        'schema': 'phase-c2b-candidate-manifest-v1',
        'candidate_name': CANDIDATE_NAME,
        'candidate_version': CANDIDATE_VERSION,
        'commit_sha': commit_sha,
        'frozen_phase_c1': frozen_hashes,
        'files': file_records,
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode('utf-8')
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    prefix = f'{CANDIDATE_NAME}/'
    with zipfile.ZipFile(
        archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in sorted(contents):
            archive.writestr(zip_info(prefix + relative), contents[relative])
        archive.writestr(
            zip_info(prefix + 'CANDIDATE_MANIFEST.json'), manifest_bytes
        )
    return {
        'candidate_name': CANDIDATE_NAME,
        'candidate_version': CANDIDATE_VERSION,
        'commit_sha': commit_sha,
        'archive_path': str(archive_path),
        'archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        'archive_entries': len(contents) + 1,
    }


def git_output(*args):
    process = subprocess.run(
        ['git', *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stdout.strip())
    return process.stdout.strip()


def main():
    if git_output('branch', '--show-current') != 'codex/phase-c2b-worker':
        print('release build requires codex/phase-c2b-worker', file=sys.stderr)
        return 1
    if git_output('status', '--porcelain', '--untracked-files=all'):
        print('release build requires a clean worktree', file=sys.stderr)
        return 1
    commit_sha = git_output('rev-parse', 'HEAD')
    archive_path = ROOT / 'dist' / f'{CANDIDATE_NAME}.zip'
    release = create_release_archive(ROOT, archive_path, commit_sha)
    manifest_path = ROOT / 'dist' / 'release_manifest.json'
    manifest_path.write_text(
        json.dumps(release, indent=2, sort_keys=True), encoding='utf-8'
    )
    (archive_path.with_suffix('.zip.sha256')).write_text(
        f"{release['archive_sha256']}  {archive_path.name}\n", encoding='utf-8'
    )
    print(json.dumps(release, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
