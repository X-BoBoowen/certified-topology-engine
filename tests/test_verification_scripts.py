import json
import importlib.util
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def run_script(name, timeout=120):
    return subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / name)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )


def run_static_check(*paths):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'run_static_undefined_check.py'),
            *[str(path) for path in paths],
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
    )


def test_static_undefined_name_gate_rejects_a_real_undefined_name(tmp_path):
    broken = tmp_path / 'broken.py'
    broken.write_text('result = missing_name\n', encoding='utf-8')
    process = run_static_check(broken)
    assert process.returncode == 1, process.stdout
    assert "undefined name 'missing_name'" in process.stdout


def test_static_undefined_name_gate_accepts_the_target_tree():
    process = run_static_check()
    assert process.returncode == 0, process.stdout


def test_general_suite_completes_with_required_semantic_counts():
    try:
        process = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'run_general_suite.py')],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError('general suite exceeded 30 seconds') from None

    assert process.returncode == 0, process.stdout
    result = json.loads((ROOT / 'results' / 'general_suite.json').read_text())
    assert result['circle_scenarios'] == 22
    assert result['circle_failures'] == 0
    assert result['circle_false_valid'] == 0
    assert result['circle_valid'] > 0
    assert result['knot_scenarios'] == 9
    assert result['knot_failures'] == 0


def test_proof_replay_script_replays_in_a_new_process():
    process = run_script('run_proof_replay.py')
    assert process.returncode == 0, process.stdout
    result = json.loads((ROOT / 'results' / 'proof_replay.json').read_text())
    assert result['original_replay'] is True
    assert result['generator_pid'] != result['replay_pid']
    assert result['replay_exit_code'] == 0


def test_proof_tamper_script_rejects_resealed_critical_changes():
    process = run_script('run_proof_tamper.py')
    assert process.returncode == 0, process.stdout
    result = json.loads((ROOT / 'results' / 'proof_tamper.json').read_text())
    assert set(result['tamper_rejections']) == {
        'decision',
        'numeric_certificate',
        'artifact_hash',
        'factorization_certificate',
    }
    assert all(result['tamper_rejections'].values())


def test_bounded_command_runner_times_out_fail_closed(tmp_path):
    spec = importlib.util.find_spec('phase_c2a.verification_runtime')
    assert spec is not None
    verification_runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verification_runtime)
    record = verification_runtime.run_bounded_command(
        'timeout_probe',
        [sys.executable, '-c', 'import time; time.sleep(2)'],
        ROOT,
        tmp_path,
        timeout_seconds=0.1,
    )
    assert record['exit_code'] == 124
    assert record['timed_out'] is True
    assert record['runtime_seconds'] < 1
    assert (tmp_path / 'VERIFY_TIMEOUT_PROBE.txt').is_file()


def test_required_verification_commands_have_bounded_timeouts():
    spec = importlib.util.find_spec('phase_c2a.verification_runtime')
    assert spec is not None
    verification_runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verification_runtime)
    commands = verification_runtime.verification_commands(ROOT, sys.executable)
    assert [command['name'] for command in commands] == [
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
    ]
    assert all(0 < command['timeout_seconds'] <= 120 for command in commands)


def test_frozen_hash_script_writes_approved_machine_report():
    process = run_script('run_frozen_hash_check.py')
    assert process.returncode == 0, process.stdout
    result = json.loads((ROOT / 'results' / 'frozen_artifacts.json').read_text())
    assert result == {
        'inner_sha256': '94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe',
        'outer_sha256': '0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0',
        'status': 'PASS',
    }


def test_relocation_script_replays_proof_from_a_different_path():
    process = run_script('run_relocation_check.py')
    assert process.returncode == 0, process.stdout
    result = json.loads((ROOT / 'results' / 'relocation.json').read_text())
    assert result['source_root'] != result['relocated_root']
    assert result['proof_replay_exit_code'] == 0
    assert result['proof_replay']['original_replay'] is True


def test_release_archive_contains_only_the_runtime_closure_candidate(tmp_path):
    spec = importlib.util.find_spec('scripts.build_release')
    assert spec is not None
    build_release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_release)
    archive_path = tmp_path / 'candidate.zip'
    release = build_release.create_release_archive(
        ROOT, archive_path, commit_sha='0' * 40
    )
    assert len(release['archive_sha256']) == 64
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        prefix = f"{build_release.CANDIDATE_NAME}/"
        assert prefix + 'CANDIDATE_MANIFEST.json' in names
        assert prefix + 'results/verification_summary.json' in names
        assert prefix + 'logs/VERIFY_RELOCATION.txt' in names
        assert prefix + 'frozen_phase_c1/Phase_C1_Exact_Input_Soundness_Repair_Bundle_20260823.zip' in names
        assert prefix + 'frozen_phase_c1/phase_c_reach_engine_prototype.zip' in names
        assert prefix + 'phase_c2a_proposal_assisted_prototype.zip' not in names
        assert not any('/.venv/' in name or '/audit_inputs/' in name for name in names)


def copy_release_tree(build_release, destination):
    for source in build_release.release_files(ROOT):
        target = destination / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_release_builder_rejects_a_missing_machine_summary(tmp_path):
    spec = importlib.util.find_spec('scripts.build_release')
    build_release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_release)
    candidate = tmp_path / 'candidate'
    copy_release_tree(build_release, candidate)
    (candidate / 'results' / 'verification_summary.json').unlink()
    with pytest.raises(RuntimeError, match='missing release file'):
        build_release.release_files(candidate)


def test_release_builder_rejects_a_failed_machine_summary(tmp_path):
    spec = importlib.util.find_spec('scripts.build_release')
    build_release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_release)
    candidate = tmp_path / 'candidate'
    copy_release_tree(build_release, candidate)
    summary_path = candidate / 'results' / 'verification_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    summary['all_passed'] = False
    summary_path.write_text(json.dumps(summary), encoding='utf-8')
    with pytest.raises(RuntimeError, match='verification summary is not passed'):
        build_release.create_release_archive(
            candidate, tmp_path / 'failed.zip', commit_sha='0' * 40
        )


def test_pristine_bootstrap_times_out_fail_closed():
    spec = importlib.util.find_spec('scripts.verify_pristine')
    assert spec is not None
    verify_pristine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify_pristine)
    record = verify_pristine.run_step(
        [sys.executable, '-c', 'import time; time.sleep(2)'],
        ROOT,
        timeout_seconds=0.1,
    )
    assert record['exit_code'] == 124
    assert record['timed_out'] is True
    assert record['runtime_seconds'] < 1


def test_final_verdict_matches_the_machine_summary():
    summary = json.loads((ROOT / 'results' / 'verification_summary.json').read_text())
    verdict = (ROOT / 'FINAL_VERDICT.txt').read_text(encoding='utf-8').strip()
    assert verdict == summary['worker_status']
