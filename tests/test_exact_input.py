import pytest
from fractions import Fraction as F
from decimal import Decimal
from phase_c2a import *
from phase_c2a.scenarios import circle,base_circle_scenarios,make_field

def test_parse_rational_decimal_text_exact(): assert parse_rational('0.7')==F(7,10)
@pytest.mark.parametrize('bad',[0.7,Decimal('0.7'),True,'0.7'])
def test_r0_rejects_non_exact_types(bad):
    field,p=make_field(base_circle_scenarios()[0]); assert GeneralReachEngine().certify(field,bad,p).status is EngineStatus.INPUT_INVALID
@pytest.mark.parametrize('bad',[0.0,Decimal('1'),True,'1'])
def test_circle_spec_rejects_non_exact_types(bad):
    with pytest.raises((ExactInputError,TypeError)): CircleSpec(bad,F(0),F(1))
