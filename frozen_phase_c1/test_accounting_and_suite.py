from fractions import Fraction as F

import reach_engine
import run_suite
from reach_engine import Circle, ReachEngine, Status


def test_cover_preserving_bisection_covers_parent_and_shares_midpoint():
    parent = reach_engine.Interval(F(1, 3), F(7, 5))
    left, right = reach_engine.bisect_interval_cover(parent)
    assert left.lo == parent.lo
    assert right.hi == parent.hi
    assert left.hi == right.lo == parent.mid
    assert left.lo <= parent.lo <= left.hi
    assert right.lo <= parent.hi <= right.hi


def test_max_depth_unresolved_accounting_is_auditable():
    circles = [Circle(F(0), F(0), F(5)), Circle(F(12), F(0), F(5))]
    result = ReachEngine(4, max_depth=0, max_boxes=200_000).certify(circles, F(1))
    assert result.status is Status.UNKNOWN
    assert result.queued_boxes_at_exit == 0
    assert result.unresolved_boxes == result.max_depth_unresolved_boxes
    assert result.generated_boxes == result.interval_boxes + result.queued_boxes_at_exit


def test_max_box_unresolved_accounting_preserves_prior_depth_failures():
    circles = [Circle(F(0), F(0), F(5)), Circle(F(12), F(0), F(5))]
    result = ReachEngine(4, max_depth=0, max_boxes=20).certify(circles, F(1))
    assert result.status is Status.UNKNOWN
    assert result.max_depth_unresolved_boxes > 0
    assert result.queued_boxes_at_exit > 0
    assert result.unresolved_boxes == (
        result.max_depth_unresolved_boxes + result.queued_boxes_at_exit
    )
    assert result.generated_boxes == result.interval_boxes + result.queued_boxes_at_exit


def test_expected_status_semantics_are_formalized():
    assert run_suite.matches_expected("VALID", Status.VALID)
    assert not run_suite.matches_expected("VALID", Status.UNKNOWN)
    assert run_suite.matches_expected("UNKNOWN_ALLOWED", Status.UNKNOWN)
    assert run_suite.matches_expected("UNKNOWN_ALLOWED", Status.VALID)
    assert not run_suite.matches_expected("UNKNOWN_ALLOWED", Status.CURVATURE_FAIL)
    assert run_suite.matches_expected("NOT_VALID", Status.UNKNOWN)
    assert run_suite.matches_expected("NOT_VALID", Status.CURVATURE_FAIL)
    assert run_suite.matches_expected("NOT_VALID", Status.INPUT_INVALID)
    assert not run_suite.matches_expected("NOT_VALID", Status.VALID)
    assert run_suite.matches_expected("CURVATURE_FAIL", Status.CURVATURE_FAIL)
    assert run_suite.matches_expected("INPUT_INVALID", Status.INPUT_INVALID)


def test_all_accounting_invariants_hold_on_budget_exit():
    circles = [Circle(F(0), F(0), F(5)), Circle(F(12), F(0), F(5))]
    result = ReachEngine(4, max_depth=0, max_boxes=20).certify(circles, F(1))
    assert result.accounting_ok
    assert result.processing_accounting_ok
    assert result.unresolved_accounting_ok
    assert result.interval_boxes == (
        result.distance_pruned
        + result.normal_pruned
        + result.max_depth_unresolved_boxes
        + result.subdivision_parent_boxes
    )


def test_run_suite_main_returns_nonzero_on_expectation_mismatch(tmp_path):
    bad_case = {
        "id": "deliberate_mismatch",
        "circles": [Circle(F(0), F(0), F(3))],
        "reference_reach": "3",
        "r0": F(2),
        "expected": "INPUT_INVALID",
    }
    output = tmp_path / "mismatch.json"
    assert run_suite.main([bad_case], output) == 1
    assert output.exists()
