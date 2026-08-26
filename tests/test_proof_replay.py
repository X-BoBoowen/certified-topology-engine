import copy
from phase_c2a import GeneralReachEngine,EngineStatus
from phase_c2a.scenarios import base_circle_scenarios,make_field

def test_real_valid_proof_replays_and_tamper_fails():
    s=base_circle_scenarios()[0]; f,p=make_field(s); e=GeneralReachEngine(max_depth=80,max_boxes=500000); r=e.certify(f,s.r0,p)
    assert r.status is EngineStatus.VALID,r.reason
    log=r.data['proof_log']; assert e.replay(f,s.r0,p,log)
    bad=copy.deepcopy(log); bad['decision']='UNKNOWN'; assert not e.replay(f,s.r0,p,bad)
