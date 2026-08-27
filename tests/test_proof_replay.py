import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from phase_c2a import GeneralReachEngine,EngineStatus
from phase_c2a.proof_log import seal
from phase_c2a.scenarios import base_circle_scenarios,make_field
from scripts.run_proof_replay import build_case
from scripts.run_proof_replay import run_replay_worker

OUTER_SHA256='0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256='94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'

ROOT=Path(__file__).resolve().parents[1]


def test_replay_case_records_complete_literal_exact_input():
    _,case=build_case()
    assert case['schema']=='phase-c2b-replay-case-v2'
    assert 'scenario_name' not in case
    assert 'r0' not in case
    exact=case['exact_input']
    assert exact=={
        'schema':'phase-c2b-exact-input-v1',
        'r0':'2',
        'field':{
            'x_breaks':['-6','6'],
            'y_breaks':['-6','6'],
            'pieces':{'0,0':[[0,0,'-9'],[0,2,'1'],[2,0,'1']]},
            'label':'S1_single_circle',
        },
        'proposal':{
            'circles':[['0','0','3']],
            'multipliers':{'0,0':[[0,0,'1']]},
        },
        'field_hash':'df4599f52f7b742eda25c56df64c038d53bf0156110611f0227964cc5a07f8fc',
        'proposal_hash':'bb086b713d3677184698defd6d65a253116ec49ee6dde9f460c9addbd6b0d1bb',
    }


def test_existing_replay_case_does_not_need_scenario_factories(tmp_path):
    _,case=build_case()
    candidate=tmp_path/'candidate'
    shutil.copytree(ROOT/'phase_c2a',candidate/'phase_c2a')
    shutil.copytree(ROOT/'frozen_phase_c1',candidate/'frozen_phase_c1')
    (candidate/'scripts').mkdir()
    shutil.copyfile(
        ROOT/'scripts'/'replay_proof_case.py',
        candidate/'scripts'/'replay_proof_case.py',
    )
    (candidate/'phase_c2a'/'scenarios.py').unlink()
    case_path=candidate/'proof_case.json'
    case_path.write_text(json.dumps(case),encoding='utf-8')
    process=subprocess.run(
        [sys.executable,str(candidate/'scripts'/'replay_proof_case.py'),str(case_path)],
        cwd=candidate,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
    )
    assert process.returncode==0,process.stdout


def test_replay_rejects_a_serialized_field_hash_mismatch(tmp_path):
    _,case=build_case()
    case['exact_input']['field']['label']='changed-after-recording'
    case_path=tmp_path/'changed_field.json'
    case_path.write_text(json.dumps(case),encoding='utf-8')
    exit_code,replay,_=run_replay_worker(case_path)
    assert exit_code==1
    assert replay['accepted'] is False
    assert replay['error']=='field hash mismatch'

def test_real_valid_proof_replays_and_tamper_fails():
    s=base_circle_scenarios()[0]; f,p=make_field(s); e=GeneralReachEngine(max_depth=80,max_boxes=500000); r=e.certify(f,s.r0,p)
    assert r.status is EngineStatus.VALID,r.reason
    log=r.data['proof_log']
    assert log['frozen_phase_c1']=={
        'outer_sha256':OUTER_SHA256,
        'inner_sha256':INNER_SHA256,
    }
    assert log['engine']=={
        'package':'phase-c2a-general-field-reference',
        'version':'0.2.1',
        'algorithm':'phase-c2b-proposal-assisted-v1',
        'work_budgets':{
            'pieces_per_quarter':4,
            'max_depth':80,
            'factorization_max_depth':24,
            'max_boxes':500000,
        },
    }
    assert e.replay(f,s.r0,p,log)
    assert log['oracle_numeric_certificate']=={
        'certified_r0':'2',
        'patch_count':16,
        'all_patch_pairs':136,
        'interval_boxes':120,
        'generated_boxes':120,
        'unresolved_boxes':0,
        'max_depth_seen':1,
        'accounting_ok':True,
        'processing_accounting_ok':True,
        'unresolved_accounting_ok':True,
    }
    tampered=[]
    bad=copy.deepcopy(log); bad['decision']='UNKNOWN'; tampered.append(bad)
    bad=copy.deepcopy(log); bad['r0']='3/2'; tampered.append(bad)
    bad=copy.deepcopy(log); bad['oracle_numeric_certificate']['interval_boxes']+=1; tampered.append(bad)
    bad=copy.deepcopy(log); bad['frozen_phase_c1']['outer_sha256']='0'*64; tampered.append(bad)
    bad=copy.deepcopy(log); bad['zero_set_certificate']['factor_hash']='0'*64; tampered.append(bad)
    for bad in tampered:
        assert not e.replay(f,s.r0,p,seal(bad))
