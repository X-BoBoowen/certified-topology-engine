from fractions import Fraction as F
from phase_c2a.scenarios import base_circle_scenarios,make_field,circle
from phase_c2a import PiecewisePolynomialField2D,Polynomial2D

def test_strict_zero_free_boundary_passes_exact_sturm():
    field,_=make_field(base_circle_scenarios()[0]); r=field.boundary_zero_free(); assert r.status.value=='VALID',r.reason

def test_true_boundary_zero_is_rejected():
    g=circle(0,0,1).factor(); field=PiecewisePolynomialField2D((F(-1),F(1)),(F(-1),F(1)),{(0,0):g})
    r=field.boundary_zero_free(); assert r.status.value=='INPUT_INVALID'

def test_sturm_closes_dependency_case_that_natural_interval_cannot():
    # p(x)=(x-1)^2+1 has no real root, but its expanded natural interval
    # on [-10,10] contains zero because x occurs dependently.
    X=Polynomial2D.x(); p=(X-1)*(X-1)+1
    field=PiecewisePolynomialField2D((F(-10),F(10)),(F(-1),F(1)),{(0,0):p},'dependency_boundary')
    natural=p.restrict_y(F(-1))
    r=field.boundary_zero_free()
    assert r.status.value=='VALID',r.reason
