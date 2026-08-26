from __future__ import annotations
from fractions import Fraction
from .polynomial import trim_uni, uni_degree, uni_derivative, uni_divmod, uni_neg, uni_eval

def sturm_sequence(p):
    p=trim_uni(p)
    if uni_degree(p)<0: return []
    seq=[p]
    d=uni_derivative(p)
    if uni_degree(d)<0: return seq
    seq.append(d)
    while True:
        _,r=uni_divmod(seq[-2],seq[-1])
        if uni_degree(r)<0: break
        seq.append(uni_neg(r))
    return seq

def sign_variations(values):
    signs=[]
    for v in values:
        if v>0: signs.append(1)
        elif v<0: signs.append(-1)
    return sum(1 for a,b in zip(signs,signs[1:]) if a!=b)

def distinct_roots_open(p,a,b):
    if not a<b: raise ValueError("a<b required")
    if uni_eval(p,a)==0 or uni_eval(p,b)==0:
        raise ValueError("endpoint root must be handled explicitly")
    seq=sturm_sequence(p)
    return sign_variations([uni_eval(q,a) for q in seq])-sign_variations([uni_eval(q,b) for q in seq])

def zero_free_closed(p,a,b):
    p=trim_uni(p)
    if uni_degree(p)<0: return False
    if uni_eval(p,a)==0 or uni_eval(p,b)==0: return False
    return distinct_roots_open(p,a,b)==0
