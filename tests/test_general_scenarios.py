import pytest
from phase_c2a import GeneralReachEngine,EngineStatus
from phase_c2a.scenarios import base_circle_scenarios,knot_scenarios,make_field,expected_ok
@pytest.mark.parametrize('s',base_circle_scenarios(),ids=lambda s:s.name)
def test_22_circle_differential_expectations(s):
    f,p=make_field(s); r=GeneralReachEngine(max_depth=130,max_boxes=2_000_000).certify(f,s.r0,p); assert expected_ok(s.expected,r.status.value),(s.name,s.expected,r.status,r.reason)
@pytest.mark.parametrize('s',knot_scenarios(),ids=lambda s:s.name)
def test_9_knot_expectations(s):
    f,p=make_field(s); r=GeneralReachEngine(max_depth=130,max_boxes=2_000_000).certify(f,s.r0,p); assert expected_ok(s.expected,r.status.value),(s.name,s.expected,r.status,r.reason)
