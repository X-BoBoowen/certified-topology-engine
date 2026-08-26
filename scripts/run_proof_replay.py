from __future__ import annotations
import json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from phase_c2a import GeneralReachEngine,EngineStatus
from phase_c2a.scenarios import base_circle_scenarios,make_field

def main():
    s=base_circle_scenarios()[0]; field,prop=make_field(s); eng=GeneralReachEngine(max_depth=80,max_boxes=500000)
    result=eng.certify(field,s.r0,prop)
    valid=(result.status is EngineStatus.VALID and 'proof_log' in result.data)
    replay=valid and eng.replay(field,s.r0,prop,result.data['proof_log'])
    tampered=copy.deepcopy(result.data.get('proof_log',{}));
    if tampered: tampered['decision']='UNKNOWN'
    tampered_replay=bool(tampered) and eng.replay(field,s.r0,prop,tampered)
    out={'source_status':result.status.value,'original_replay':replay,'tampered_replay':tampered_replay,'proof_root_hash':result.data.get('proof_log',{}).get('root_hash')}
    (ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/'proof_replay.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2)); return 0 if valid and replay and not tampered_replay else 1
if __name__=='__main__': raise SystemExit(main())
