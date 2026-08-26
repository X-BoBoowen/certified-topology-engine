from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from .exact_types import require_fraction

@dataclass(frozen=True)
class RationalInterval:
    lo: Fraction
    hi: Fraction
    def __post_init__(self):
        lo=require_fraction(self.lo,"interval.lo"); hi=require_fraction(self.hi,"interval.hi")
        if lo>hi: raise ValueError("interval lo > hi")
        object.__setattr__(self,"lo",lo); object.__setattr__(self,"hi",hi)
    @classmethod
    def point(cls,x):
        q=require_fraction(x); return cls(q,q)
    def __add__(self,o):
        o=as_interval(o); return RationalInterval(self.lo+o.lo,self.hi+o.hi)
    __radd__=__add__
    def __neg__(self): return RationalInterval(-self.hi,-self.lo)
    def __sub__(self,o): return self+(-as_interval(o))
    def __rsub__(self,o): return as_interval(o)-self
    def __mul__(self,o):
        o=as_interval(o); vals=(self.lo*o.lo,self.lo*o.hi,self.hi*o.lo,self.hi*o.hi)
        return RationalInterval(min(vals),max(vals))
    __rmul__=__mul__
    def reciprocal(self):
        if self.lo<=0<=self.hi: raise ZeroDivisionError("interval contains zero")
        return RationalInterval(min(1/self.lo,1/self.hi),max(1/self.lo,1/self.hi))
    def __truediv__(self,o): return self*as_interval(o).reciprocal()
    def square(self):
        if self.lo<=0<=self.hi: return RationalInterval(Fraction(0),max(self.lo*self.lo,self.hi*self.hi))
        vals=(self.lo*self.lo,self.hi*self.hi); return RationalInterval(min(vals),max(vals))
    def contains(self,x):
        q=require_fraction(x); return self.lo<=q<=self.hi
    def contains_zero(self): return self.lo<=0<=self.hi
    def width(self): return self.hi-self.lo
    def midpoint(self): return (self.lo+self.hi)/2
    def hull(self,o):
        o=as_interval(o); return RationalInterval(min(self.lo,o.lo),max(self.hi,o.hi))
    def to_json(self): return [str(self.lo),str(self.hi)]

def as_interval(x):
    if isinstance(x,RationalInterval): return x
    return RationalInterval.point(x)
