from fractions import Fraction as F
from phase_c2a import *
from phase_c2a.scenarios import base_circle_scenarios,make_field

def test_exact_factor_certificate_proves_zero_set_coverage():
    f,p=make_field(base_circle_scenarios()[0],extra_knots_x=(F(0),),extra_knots_y=(F(0),)); r=p.validate_field_factorization(f); assert r.status is FieldStatus.VALID,r.reason

def test_wrong_multiplier_cannot_validate():
    f,p=make_field(base_circle_scenarios()[0]); wrong=CircleProposal(p.circles,{k:Polynomial2D.one()+1 for k in p.multipliers}); r=wrong.validate_field_factorization(f); assert r.status is FieldStatus.INPUT_INVALID
