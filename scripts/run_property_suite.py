from __future__ import annotations
import json,sys,random
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from phase_c2a.intervals import RationalInterval
from phase_c2a.polynomial import Polynomial2D
from phase_c2a.scenarios import base_circle_scenarios,make_field

def main():
    rng=random.Random(20260824); checks=0
    s=base_circle_scenarios()[0]; field,_=make_field(s,extra_knots_x=(F(0),),extra_knots_y=(F(0),))
    val=field.validate()
    if val.status.value!='VALID':
        print(json.dumps({'status':'FAIL','reason':val.reason})); return 1
    polys=[]
    for p in field.pieces.values(): polys += [p,p.derivative('x'),p.derivative('y'),p.derivative('x',2),p.derivative('x').derivative('y'),p.derivative('y',2)]
    for _ in range(100_000):
        p=polys[rng.randrange(len(polys))]
        i=rng.randrange(len(field.x_breaks)-1); j=rng.randrange(len(field.y_breaks)-1)
        x0,x1,y0,y1=field.cell_box(i,j)
        den=1<<rng.randrange(2,10)
        xa=x0+(x1-x0)*F(rng.randrange(den+1),den); xb=x0+(x1-x0)*F(rng.randrange(den+1),den)
        ya=y0+(y1-y0)*F(rng.randrange(den+1),den); yb=y0+(y1-y0)*F(rng.randrange(den+1),den)
        xi=RationalInterval(min(xa,xb),max(xa,xb)); yi=RationalInterval(min(ya,yb),max(ya,yb))
        iv=p.interval_evaluate(xi,yi)
        x=xi.lo+(xi.hi-xi.lo)*F(rng.randrange(17),16); y=yi.lo+(yi.hi-yi.lo)*F(rng.randrange(17),16)
        if not iv.contains(p.evaluate(x,y)):
            print(json.dumps({'status':'FAIL','check':checks})); return 1
        checks+=1
    out={'status':'PASS','exact_reference_checks':checks,'field_validation':val.reason}
    (ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/'property_suite.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
