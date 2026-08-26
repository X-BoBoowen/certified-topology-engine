from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Dict, Tuple, Any
import hashlib, json
from .exact_types import require_fraction, ExactInputError
from .intervals import RationalInterval
from .polynomial import Polynomial2D
from .sturm import zero_free_closed

class FieldStatus(str,Enum):
    VALID="VALID"
    INPUT_INVALID="INPUT_INVALID"
    UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class FieldValidation:
    status: FieldStatus
    reason: str
    data: dict=field(default_factory=dict)

@dataclass(frozen=True)
class PiecewisePolynomialField2D:
    x_breaks: Tuple[Fraction,...]
    y_breaks: Tuple[Fraction,...]
    pieces: Dict[Tuple[int,int],Polynomial2D]
    label: str="field"
    def __post_init__(self):
        if type(self.x_breaks) not in (tuple,list) or type(self.y_breaks) not in (tuple,list):
            raise ExactInputError("breaks must be built-in tuple/list")
        xs=tuple(require_fraction(x,"x_break") for x in self.x_breaks)
        ys=tuple(require_fraction(y,"y_break") for y in self.y_breaks)
        if len(xs)<2 or len(ys)<2 or any(a>=b for a,b in zip(xs,xs[1:])) or any(a>=b for a,b in zip(ys,ys[1:])):
            raise ValueError("breaks must be strictly increasing")
        if type(self.pieces) is not dict: raise ExactInputError("pieces must be dict")
        expected={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1)}
        if set(self.pieces)!=expected: raise ValueError("cell complex has gap or extra/overlap key")
        for k,p in self.pieces.items():
            if not isinstance(p,Polynomial2D): raise ExactInputError(f"piece {k} is not Polynomial2D")
        if type(self.label) is not str: raise ExactInputError("label must be str")
        object.__setattr__(self,"x_breaks",xs); object.__setattr__(self,"y_breaks",ys)
    def cell_box(self,i,j):
        return self.x_breaks[i],self.x_breaks[i+1],self.y_breaks[j],self.y_breaks[j+1]
    def canonical(self):
        return {"x_breaks":[str(x) for x in self.x_breaks],"y_breaks":[str(y) for y in self.y_breaks],
                "pieces":{f"{i},{j}":self.pieces[i,j].canonical() for i,j in sorted(self.pieces)},"label":self.label}
    def field_hash(self): return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def _edge_equal(self,p,q,axis,c):
        derivs=[(0,0),(1,0),(0,1),(2,0),(1,1),(0,2)]
        for dx,dy in derivs:
            a=p.derivative('x',dx).derivative('y',dy)
            b=q.derivative('x',dx).derivative('y',dy)
            diff=a-b
            uni=diff.restrict_x(c) if axis=='x' else diff.restrict_y(c)
            if uni: return False
        return True
    def validate_c2(self):
        nx=len(self.x_breaks)-1; ny=len(self.y_breaks)-1; checks=0
        for i in range(nx-1):
            c=self.x_breaks[i+1]
            for j in range(ny):
                checks+=1
                if not self._edge_equal(self.pieces[i,j],self.pieces[i+1,j],'x',c):
                    return FieldValidation(FieldStatus.INPUT_INVALID,"C2_MISMATCH_VERTICAL",{"i":i,"j":j})
        for j in range(ny-1):
            c=self.y_breaks[j+1]
            for i in range(nx):
                checks+=1
                if not self._edge_equal(self.pieces[i,j],self.pieces[i,j+1],'y',c):
                    return FieldValidation(FieldStatus.INPUT_INVALID,"C2_MISMATCH_HORIZONTAL",{"i":i,"j":j})
        return FieldValidation(FieldStatus.VALID,"C2_OK",{"edge_checks":checks})
    def boundary_zero_free(self):
        """Exact one-dimensional Sturm certificate on every outer-domain edge segment."""
        nx=len(self.x_breaks)-1; ny=len(self.y_breaks)-1; cert=[]
        xmin,xmax=self.x_breaks[0],self.x_breaks[-1]; ymin,ymax=self.y_breaks[0],self.y_breaks[-1]
        # vertical left/right edge restrictions in y
        for side,i,x in (("left",0,xmin),("right",nx-1,xmax)):
            for j in range(ny):
                a,b=self.y_breaks[j],self.y_breaks[j+1]; p=self.pieces[i,j].restrict_x(x)
                ok=zero_free_closed(p,a,b); cert.append([side,i,j,str(a),str(b),ok])
                if not ok: return FieldValidation(FieldStatus.INPUT_INVALID,"ZERO_ON_DOMAIN_BOUNDARY",{"segment":cert[-1]})
        # bottom/top restrictions in x
        for side,j,y in (("bottom",0,ymin),("top",ny-1,ymax)):
            for i in range(nx):
                a,b=self.x_breaks[i],self.x_breaks[i+1]; p=self.pieces[i,j].restrict_y(y)
                ok=zero_free_closed(p,a,b); cert.append([side,i,j,str(a),str(b),ok])
                if not ok: return FieldValidation(FieldStatus.INPUT_INVALID,"ZERO_ON_DOMAIN_BOUNDARY",{"segment":cert[-1]})
        return FieldValidation(FieldStatus.VALID,"BOUNDARY_ZERO_FREE",{"segments":cert})
    def validate(self):
        c2=self.validate_c2()
        if c2.status is not FieldStatus.VALID: return c2
        bd=self.boundary_zero_free()
        if bd.status is not FieldStatus.VALID: return bd
        return FieldValidation(FieldStatus.VALID,"FIELD_VALID",{"c2":c2.data,"boundary":bd.data,"field_hash":self.field_hash()})
