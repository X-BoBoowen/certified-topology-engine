from fractions import Fraction as F
from phase_c2a import *
from phase_c2a.scenarios import base_circle_scenarios,make_field

def test_piecewise_knot_field_is_c2_and_boundary_zero_free():
    f,_=make_field(base_circle_scenarios()[0],extra_knots_x=(F(-1),F(0),F(1)),extra_knots_y=(F(0),)); r=f.validate(); assert r.status is FieldStatus.VALID,r.reason

def test_candidate_free_field_is_honest_unknown():
    f,_=make_field(base_circle_scenarios()[0]); r=GeneralReachEngine().certify(f,F(1),None); assert r.status is EngineStatus.UNKNOWN
