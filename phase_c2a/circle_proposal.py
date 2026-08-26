from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple, Dict
import hashlib,json
from .exact_types import require_fraction, ExactInputError
from .polynomial import Polynomial2D
from .field import PiecewisePolynomialField2D, FieldStatus, FieldValidation
from .intervals import RationalInterval

@dataclass(frozen=True)
class CircleSpec:
    cx: Fraction
    cy: Fraction
    radius: Fraction
    def __post_init__(self):
        cx=require_fraction(self.cx,'CircleSpec.cx'); cy=require_fraction(self.cy,'CircleSpec.cy'); r=require_fraction(self.radius,'CircleSpec.radius')
        if r<=0: raise ValueError('radius must be positive')
        object.__setattr__(self,'cx',cx); object.__setattr__(self,'cy',cy); object.__setattr__(self,'radius',r)
    def factor(self):
        X=Polynomial2D.x()-self.cx; Y=Polynomial2D.y()-self.cy
        return X*X+Y*Y-self.radius*self.radius
    def canonical(self): return [str(self.cx),str(self.cy),str(self.radius)]

@dataclass(frozen=True)
class CircleProposal:
    circles: Tuple[CircleSpec,...]
    multipliers: Dict[Tuple[int,int],Polynomial2D]
    def __post_init__(self):
        if type(self.circles) not in (tuple,list): raise ExactInputError('circles must be built-in tuple/list')
        cs=tuple(self.circles)
        if not cs: raise ValueError('empty circle proposal')
        if any(not isinstance(c,CircleSpec) for c in cs): raise ExactInputError('invalid circle proposal member')
        if type(self.multipliers) is not dict or any(not isinstance(p,Polynomial2D) for p in self.multipliers.values()):
            raise ExactInputError('multipliers must map cells to Polynomial2D')
        object.__setattr__(self,'circles',cs)
    def canonical(self):
        return {"circles":[c.canonical() for c in self.circles],"multipliers":{f"{i},{j}":p.canonical() for (i,j),p in sorted(self.multipliers.items())}}
    def proposal_hash(self): return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def validate_link(self):
        cs=self.circles
        for i in range(len(cs)):
            for j in range(i+1,len(cs)):
                a,b=cs[i],cs[j]; dx=a.cx-b.cx; dy=a.cy-b.cy; d2=dx*dx+dy*dy
                sp=a.radius+b.radius; df=abs(a.radius-b.radius)
                if not (d2>sp*sp or d2<df*df):
                    return FieldValidation(FieldStatus.INPUT_INVALID,'PROPOSAL_NOT_DISJOINT',{'i':i,'j':j})
                if d2==0 and a.radius==b.radius:
                    return FieldValidation(FieldStatus.INPUT_INVALID,'DUPLICATE_CIRCLE',{'i':i,'j':j})
        return FieldValidation(FieldStatus.VALID,'PROPOSAL_LINK_VALID',{'circle_count':len(cs)})
    def base_factor(self):
        g=Polynomial2D.one()
        for c in self.circles: g=g*c.factor()
        return g
    def validate_field_factorization(self,field:PiecewisePolynomialField2D,max_depth:int=20,max_boxes:int=200000):
        if set(self.multipliers)!=set(field.pieces):
            return FieldValidation(FieldStatus.INPUT_INVALID,'MULTIPLIER_CELL_KEYS_MISMATCH',{})
        g=self.base_factor(); positivity=[]
        for key,p in field.pieces.items():
            h=self.multipliers[key]
            if p!=h*g:
                return FieldValidation(FieldStatus.INPUT_INVALID,'FIELD_FACTOR_MISMATCH',{'cell':list(key)})
            i,j=key; x0,x1,y0,y1=field.cell_box(i,j)
            stack=[(RationalInterval(x0,x1),RationalInterval(y0,y1),0)]; seen=0; leaves=0
            while stack:
                xi,yi,d=stack.pop(); seen+=1
                if seen>max_boxes:
                    return FieldValidation(FieldStatus.UNKNOWN,'MULTIPLIER_POSITIVITY_BUDGET',{'cell':list(key),'boxes':seen})
                iv=h.interval_evaluate(xi,yi)
                if iv.lo>0:
                    leaves+=1; continue
                if iv.hi<=0:
                    return FieldValidation(FieldStatus.INPUT_INVALID,'MULTIPLIER_NOT_POSITIVE',{'cell':list(key),'interval':iv.to_json()})
                if d>=max_depth:
                    return FieldValidation(FieldStatus.UNKNOWN,'MULTIPLIER_POSITIVITY_UNRESOLVED',{'cell':list(key),'interval':iv.to_json()})
                if xi.width()>=yi.width():
                    m=xi.midpoint(); stack.append((RationalInterval(xi.lo,m),yi,d+1)); stack.append((RationalInterval(m,xi.hi),yi,d+1))
                else:
                    m=yi.midpoint(); stack.append((xi,RationalInterval(yi.lo,m),d+1)); stack.append((xi,RationalInterval(m,yi.hi),d+1))
            positivity.append({'cell':list(key),'boxes':seen,'leaves':leaves})
        return FieldValidation(FieldStatus.VALID,'ZERO_SET_EQUALS_PROPOSED_LINK',{'factor_hash':hashlib.sha256(json.dumps(g.canonical()).encode()).hexdigest(),'positivity':positivity})
