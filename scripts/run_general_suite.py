from __future__ import annotations
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from phase_c2a import GeneralReachEngine
from phase_c2a.scenarios import base_circle_scenarios,knot_scenarios,make_field,expected_ok
from phase_c2a.frozen_oracle import load_frozen_module

def run_one(s):
    field,prop=make_field(s)
    t=time.perf_counter(); r=GeneralReachEngine(max_depth=130,max_boxes=2_000_000).certify(field,s.r0,prop); dt=time.perf_counter()-t
    oracle=load_frozen_module(); ocs=[oracle.Circle(c.cx,c.cy,c.radius) for c in prop.circles]
    ores=oracle.ReachEngine(pieces_per_quarter=4,max_depth=130,max_boxes=2_000_000).certify(ocs,s.r0)
    oracle_status=getattr(ores.status,'name',str(ores.status).split('.')[-1])
    differential_ok=(r.status.value!='VALID' or oracle_status=='VALID')
    return {'name':s.name,'expected':s.expected,'status':r.status.value,'oracle_status':oracle_status,'reason':r.reason,'ok':expected_ok(s.expected,r.status.value) and differential_ok,'differential_ok':differential_ok,'runtime_seconds':dt,'proof_log':r.data.get('proof_log')}
def main():
    circles=[run_one(s) for s in base_circle_scenarios()]; knots=[run_one(s) for s in knot_scenarios()]
    out={'circle_scenarios':len(circles),'circle_valid':sum(x['status']=='VALID' for x in circles),'circle_false_valid':sum((x['expected']=='NOT_VALID' and x['status']=='VALID') for x in circles),
         'circle_failures':sum(not x['ok'] for x in circles),'knot_scenarios':len(knots),'knot_valid':sum(x['status']=='VALID' for x in knots),'knot_failures':sum(not x['ok'] for x in knots),'circles':circles,'knots':knots}
    (ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/'general_suite.json').write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('circles','knots')},indent=2,sort_keys=True))
    return 0 if out['circle_failures']==0 and out['knot_failures']==0 and out['circle_valid']>0 and out['circle_false_valid']==0 else 1
if __name__=='__main__': raise SystemExit(main())
