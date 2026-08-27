from pathlib import Path
import shutil
from fractions import Fraction
from types import SimpleNamespace

import pytest

from phase_c2a import EngineStatus, GeneralReachEngine
from phase_c2a import engine as engine_module, frozen_oracle
from phase_c2a.scenarios import base_circle_scenarios, make_field


OUTER_SHA256 = '0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256 = '94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'


def test_resolver_reports_approved_frozen_artifact_hashes():
    artifacts = frozen_oracle.resolve_frozen_artifacts()
    assert artifacts == {
        'outer_sha256': OUTER_SHA256,
        'inner_sha256': INNER_SHA256,
    }


def test_resolver_rejects_missing_frozen_artifacts(tmp_path):
    with pytest.raises(RuntimeError, match='missing frozen Phase C.1 artifact'):
        frozen_oracle.resolve_frozen_artifacts(tmp_path)


def test_resolver_rejects_frozen_artifact_hash_mismatch(tmp_path):
    frozen_dir = tmp_path / 'frozen_phase_c1'
    frozen_dir.mkdir()
    (frozen_dir / 'Phase_C1_Exact_Input_Soundness_Repair_Bundle_20260823.zip').write_bytes(b'wrong outer')
    (frozen_dir / 'phase_c_reach_engine_prototype.zip').write_bytes(b'wrong inner')
    with pytest.raises(RuntimeError, match='frozen Phase C.1 artifact hash mismatch'):
        frozen_oracle.resolve_frozen_artifacts(tmp_path)


def test_loader_executes_reach_engine_from_the_verified_inner_archive(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'frozen_phase_c1'
    frozen_dir = tmp_path / 'frozen_phase_c1'
    frozen_dir.mkdir()
    shutil.copyfile(
        source / frozen_oracle.OUTER_FILENAME,
        frozen_dir / frozen_oracle.OUTER_FILENAME,
    )
    shutil.copyfile(
        source / frozen_oracle.INNER_FILENAME,
        frozen_dir / frozen_oracle.INNER_FILENAME,
    )
    (frozen_dir / 'reach_engine.py').write_text(
        "raise RuntimeError('untrusted unpacked source executed')\n",
        encoding='utf-8',
    )
    module = frozen_oracle.load_frozen_module(tmp_path)
    assert hasattr(module, 'Circle')
    assert hasattr(module, 'ReachEngine')


def test_engine_valid_path_calls_verified_frozen_oracle_with_budgets(monkeypatch):
    module = frozen_oracle.load_frozen_module()
    real_engine = module.ReachEngine
    calls = []

    class RecordingReachEngine(real_engine):
        def __init__(self, pieces_per_quarter, max_depth, max_boxes):
            calls.append(
                ('budgets', pieces_per_quarter, max_depth, max_boxes)
            )
            super().__init__(pieces_per_quarter, max_depth, max_boxes)

        def certify(self, circles, r0):
            circles = list(circles)
            calls.append(
                (
                    'certify',
                    [(c.cx, c.cy, c.radius) for c in circles],
                    r0,
                )
            )
            return super().certify(circles, r0)

    module.ReachEngine = RecordingReachEngine
    monkeypatch.setattr(engine_module, 'load_frozen_module', lambda: module)
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    result = GeneralReachEngine(max_depth=40, max_boxes=500000).certify(
        field, scenario.r0, proposal
    )
    assert result.status is EngineStatus.VALID, result.reason
    assert calls == [
        ('budgets', 4, 40, 10000),
        ('certify', [(Fraction(0), Fraction(0), Fraction(3))], Fraction(2)),
    ]
    assert result.data['proof_log']['oracle']['status'] == 'VALID'
    assert result.data['proof_log']['oracle']['stats']['patch_count'] == 16
    assert result.data['proof_log']['oracle']['budgets'] == {
        'pieces_per_quarter': 4,
        'max_depth': 40,
        'max_boxes': 10000,
    }
    assert result.data['proof_log']['oracle_numeric_certificate']['certified_r0'] == '2'


def test_engine_fails_closed_when_frozen_artifact_validation_fails(monkeypatch):
    def reject_artifacts():
        raise frozen_oracle.FrozenArtifactError('frozen Phase C.1 artifact hash mismatch')

    monkeypatch.setattr(engine_module, 'load_frozen_module', reject_artifacts)
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    result = GeneralReachEngine(max_depth=80, max_boxes=500000).certify(
        field, scenario.r0, proposal
    )
    assert result.status is EngineStatus.UNKNOWN
    assert result.reason == 'FROZEN_ARTIFACT_VALIDATION_FAILED'
    assert 'proof_log' not in result.data


@pytest.mark.parametrize('error', [RuntimeError('oracle failed'), TimeoutError('oracle timed out')])
def test_engine_fails_closed_when_frozen_oracle_raises(monkeypatch, error):
    module = frozen_oracle.load_frozen_module()

    class FailingReachEngine:
        def __init__(self, pieces_per_quarter, max_depth, max_boxes):
            pass

        def certify(self, circles, r0):
            raise error

    monkeypatch.setattr(
        engine_module,
        'load_frozen_module',
        lambda: SimpleNamespace(Circle=module.Circle, ReachEngine=FailingReachEngine),
    )
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    result = GeneralReachEngine(max_depth=40, max_boxes=500000).certify(
        field, scenario.r0, proposal
    )
    assert result.status is EngineStatus.UNKNOWN
    assert result.reason == 'FROZEN_ORACLE_EXECUTION_FAILED'
    assert 'proof_log' not in result.data


def test_engine_does_not_promote_real_frozen_unknown_to_valid():
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    result = GeneralReachEngine(max_depth=0, max_boxes=1).certify(
        field, scenario.r0, proposal
    )
    assert result.status is EngineStatus.UNKNOWN
    assert result.reason == 'interval box budget exhausted'
    assert result.data['proof_log']['oracle']['status'] == 'UNKNOWN'


def test_engine_fails_closed_when_frozen_result_identity_is_inconsistent(monkeypatch):
    module = frozen_oracle.load_frozen_module()
    real_engine = module.ReachEngine

    class InconsistentReachEngine(real_engine):
        def certify(self, circles, r0):
            result = super().certify(circles, r0)
            result.r0 = Fraction(99)
            return result

    module.ReachEngine = InconsistentReachEngine
    monkeypatch.setattr(engine_module, 'load_frozen_module', lambda: module)
    scenario = base_circle_scenarios()[0]
    field, proposal = make_field(scenario)
    result = GeneralReachEngine(max_depth=40, max_boxes=500000).certify(
        field, scenario.r0, proposal
    )
    assert result.status is EngineStatus.UNKNOWN
    assert result.reason == 'FROZEN_ORACLE_RESULT_INCONSISTENT'
    assert 'proof_log' not in result.data
