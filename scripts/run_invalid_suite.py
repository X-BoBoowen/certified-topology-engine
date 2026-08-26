from __future__ import annotations
import json,sys
from fractions import Fraction as F
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from phase_c2a import *
from phase_c2a.scenarios import base_circle_scenarios,make_field,circle

def main():
    rows=[]
    def rec(name,ok,status): rows.append({'name':name,'ok':bool(ok),'status':status})
    s=base_circle_scenarios()[0]; field,prop=make_field(s); eng=GeneralReachEngine()
    for name,bad in [('float_r0',0.7),('decimal_r0',Decimal('0.7')),('bool_r0',True),('string_r0','0.7')]:
        r=eng.certify(field,bad,prop); rec(name,r.status is EngineStatus.INPUT_INVALID,r.status.value)
    # Boundary zero: unit circle field on domain [-1,1]^2 touches boundary.
    g=circle(0,0,1).factor(); h=Polynomial2D.one(); f2=PiecewisePolynomialField2D((F(-1),F(1)),(F(-1),F(1)),{(0,0):g},'boundary_touch')
    p2=CircleProposal((circle(0,0,1),),{(0,0):h}); r=eng.certify(f2,F(1,2),p2); rec('boundary_touch',r.status is EngineStatus.INPUT_INVALID,r.status.value)
    # C2 mismatch.
    xs=(F(-3),F(0),F(3)); ys=(F(-3),F(3)); pieces={(0,0):g,(1,0):g+Polynomial2D.constant(1)}
    f3=PiecewisePolynomialField2D(xs,ys,pieces,'c2_bad'); p3=CircleProposal((circle(0,0,1),),{(0,0):h,(1,0):h})
    r=eng.certify(f3,F(1,2),p3); rec('c2_mismatch',r.status is EngineStatus.INPUT_INVALID,r.status.value)
    # No proposal stays UNKNOWN.
    r=eng.certify(field,F(1),None); rec('field_only_gap',r.status is EngineStatus.UNKNOWN,r.status.value)
    out={'failure_count':sum(not x['ok'] for x in rows),'cases':rows}; (ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/'invalid_suite.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2)); return 0 if out['failure_count']==0 else 1
if __name__=='__main__': raise SystemExit(main())
