import copy
from phase_c2a import GeneralReachEngine,EngineStatus
from phase_c2a.proof_log import seal
from phase_c2a.scenarios import base_circle_scenarios,make_field

OUTER_SHA256='0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256='94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'

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
        'version':'0.2.0',
        'algorithm':'phase-c2b-proposal-assisted-v1',
        'work_budgets':{
            'pieces_per_quarter':4,
            'max_depth':80,
            'factorization_max_depth':24,
            'max_boxes':500000,
        },
    }
    assert e.replay(f,s.r0,p,log)
    tampered=[]
    bad=copy.deepcopy(log); bad['decision']='UNKNOWN'; tampered.append(bad)
    bad=copy.deepcopy(log); bad['r0']='3/2'; tampered.append(bad)
    bad=copy.deepcopy(log); bad['frozen_phase_c1']['outer_sha256']='0'*64; tampered.append(bad)
    bad=copy.deepcopy(log); bad['zero_set_certificate']['factor_hash']='0'*64; tampered.append(bad)
    for bad in tampered:
        assert not e.replay(f,s.r0,p,seal(bad))
