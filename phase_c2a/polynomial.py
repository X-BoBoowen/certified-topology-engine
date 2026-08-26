from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Iterable, Tuple
from .exact_types import require_fraction
from .intervals import RationalInterval, as_interval

Monomial=Tuple[int,int]

@dataclass(frozen=True)
class Polynomial2D:
    coeffs: Dict[Monomial,Fraction]
    def __post_init__(self):
        out={}
        if type(self.coeffs) is not dict: raise TypeError("coeffs must be built-in dict")
        for k,v in self.coeffs.items():
            if type(k) is not tuple or len(k)!=2 or type(k[0]) is not int or type(k[1]) is not int:
                raise TypeError("monomial keys must be (built-in int,built-in int)")
            i,j=k
            if i<0 or j<0: raise ValueError("negative exponent")
            q=require_fraction(v,f"coefficient[{k}]")
            if q: out[(i,j)]=q
        object.__setattr__(self,"coeffs",out)
    @staticmethod
    def zero(): return Polynomial2D({})
    @staticmethod
    def one(): return Polynomial2D({(0,0):Fraction(1)})
    @staticmethod
    def x(): return Polynomial2D({(1,0):Fraction(1)})
    @staticmethod
    def y(): return Polynomial2D({(0,1):Fraction(1)})
    @staticmethod
    def constant(c): return Polynomial2D({(0,0):require_fraction(c)})
    def __add__(self,o):
        if not isinstance(o,Polynomial2D): o=Polynomial2D.constant(o)
        d=dict(self.coeffs)
        for k,v in o.coeffs.items(): d[k]=d.get(k,Fraction(0))+v
        return Polynomial2D(d)
    __radd__=__add__
    def __neg__(self): return Polynomial2D({k:-v for k,v in self.coeffs.items()})
    def __sub__(self,o): return self+(-o if isinstance(o,Polynomial2D) else -require_fraction(o))
    def __rsub__(self,o): return Polynomial2D.constant(o)-self
    def __mul__(self,o):
        if not isinstance(o,Polynomial2D): o=Polynomial2D.constant(o)
        d={}
        for (i,j),a in self.coeffs.items():
            for (k,l),b in o.coeffs.items(): d[(i+k,j+l)]=d.get((i+k,j+l),Fraction(0))+a*b
        return Polynomial2D(d)
    __rmul__=__mul__
    def derivative(self,axis:str,order:int=1):
        p=self
        for _ in range(order):
            d={}
            if axis=='x':
                for (i,j),a in p.coeffs.items():
                    if i: d[(i-1,j)]=a*i
            elif axis=='y':
                for (i,j),a in p.coeffs.items():
                    if j: d[(i,j-1)]=a*j
            else: raise ValueError("axis must be x or y")
            p=Polynomial2D(d)
        return p
    def evaluate(self,x,y):
        x=require_fraction(x,'x'); y=require_fraction(y,'y')
        s=Fraction(0)
        for (i,j),a in self.coeffs.items(): s+=a*(x**i)*(y**j)
        return s
    def interval_evaluate(self,x:RationalInterval,y:RationalInterval):
        x=as_interval(x); y=as_interval(y); s=RationalInterval.point(0)
        xp={0:RationalInterval.point(1)}; yp={0:RationalInterval.point(1)}
        for i,_ in self.coeffs:
            if i not in xp:
                q=RationalInterval.point(1)
                for _ in range(i): q=q*x
                xp[i]=q
        for _,j in self.coeffs:
            if j not in yp:
                q=RationalInterval.point(1)
                for _ in range(j): q=q*y
                yp[j]=q
        for (i,j),a in self.coeffs.items(): s=s+a*xp[i]*yp[j]
        return s
    def restrict_x(self,x0):
        x0=require_fraction(x0); d={}
        for (i,j),a in self.coeffs.items(): d[j]=d.get(j,Fraction(0))+a*(x0**i)
        return trim_uni(d)
    def restrict_y(self,y0):
        y0=require_fraction(y0); d={}
        for (i,j),a in self.coeffs.items(): d[i]=d.get(i,Fraction(0))+a*(y0**j)
        return trim_uni(d)
    def substitute_affine(self, ox, oy, ex, ey, nx, ny):
        """Return polynomial in (s,v) after x=ox+ex*s+nx*v, y=oy+ey*s+ny*v."""
        vals=[require_fraction(z) for z in (ox,oy,ex,ey,nx,ny)]
        ox,oy,ex,ey,nx,ny=vals
        X=Polynomial2D.constant(ox)+ex*Polynomial2D.x()+nx*Polynomial2D.y()
        Y=Polynomial2D.constant(oy)+ey*Polynomial2D.x()+ny*Polynomial2D.y()
        out=Polynomial2D.zero()
        for (i,j),a in self.coeffs.items():
            term=Polynomial2D.constant(a)
            for _ in range(i): term=term*X
            for _ in range(j): term=term*Y
            out=out+term
        return out
    def canonical(self):
        return [[i,j,str(a)] for (i,j),a in sorted(self.coeffs.items())]
    def degree(self): return max((i+j for i,j in self.coeffs),default=-1)

def trim_uni(d):
    out={int(k):require_fraction(v) for k,v in d.items() if require_fraction(v)}
    return out

def uni_eval(p,x):
    x=require_fraction(x); return sum((a*(x**i) for i,a in p.items()),Fraction(0))

def uni_derivative(p): return {i-1:a*i for i,a in p.items() if i>0 and a*i}

def uni_degree(p): return max(p.keys(),default=-1)

def uni_neg(p): return {i:-a for i,a in p.items() if a}

def uni_divmod(a,b):
    a=dict(trim_uni(a)); b=trim_uni(b)
    db=uni_degree(b)
    if db<0: raise ZeroDivisionError
    q={}
    lb=b[db]
    while uni_degree(a)>=db:
        da=uni_degree(a); c=a[da]/lb; k=da-db
        q[k]=q.get(k,Fraction(0))+c
        for j,v in b.items():
            idx=j+k; a[idx]=a.get(idx,Fraction(0))-c*v
            if not a[idx]: a.pop(idx,None)
    return trim_uni(q),trim_uni(a)
