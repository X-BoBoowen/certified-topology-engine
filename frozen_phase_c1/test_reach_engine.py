from fractions import Fraction as F

from reach_engine import Circle, ReachEngine, Status


def run(circles, r0, **kwargs):
    engine = ReachEngine(
        pieces_per_quarter=4,
        max_depth=kwargs.get('max_depth', 18),
        max_boxes=kwargs.get('max_boxes', 300_000),
    )
    return engine.certify(circles, F(r0))


def test_s1_single_circle_strict_margin_valid():
    result = run([Circle(F(0), F(0), F(3))], F(2))
    assert result.status is Status.VALID


def test_s2_two_separated_circles_valid():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(10), F(0), F(3))]
    result = run(circles, F(3, 2))
    assert result.status is Status.VALID


def test_s3_concentric_annulus_strict_margin_valid():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(5))]
    result = run(circles, F(7, 5))
    assert result.status is Status.VALID


def test_s4_near_parallel_large_circles_below_bottleneck_valid():
    circles = [Circle(F(0), F(0), F(20)), Circle(F(202, 5), F(0), F(20))]
    result = run(circles, F(19, 100), max_depth=22, max_boxes=500_000)
    assert result.status is Status.VALID


def test_s5_equality_never_false_valid():
    circles = [Circle(F(0), F(0), F(5)), Circle(F(12), F(0), F(5))]
    result = run(circles, F(1), max_depth=14, max_boxes=80_000)
    assert result.status is not Status.VALID


def test_s6_curvature_branch_rejects_too_large_radius():
    result = run([Circle(F(0), F(0), F(3, 4))], F(1))
    assert result.status is Status.CURVATURE_FAIL


def test_s6_curvature_branch_allows_strictly_smaller_radius():
    result = run([Circle(F(0), F(0), F(3, 4))], F(7, 10))
    assert result.status is Status.VALID


def test_s7_low_curvature_global_bottleneck_not_false_valid():
    circles = [Circle(F(0), F(0), F(20)), Circle(F(202, 5), F(0), F(20))]
    result = run(circles, F(1), max_depth=14, max_boxes=80_000)
    assert result.status is not Status.VALID


def test_s8_nested_and_multiple_components_valid():
    circles = [
        Circle(F(0), F(0), F(2)),
        Circle(F(0), F(0), F(5)),
        Circle(F(20), F(0), F(3)),
    ]
    result = run(circles, F(7, 5), max_depth=20, max_boxes=400_000)
    assert result.status is Status.VALID


def test_float_r0_false_valid_regression_is_not_valid():
    """Red-team reproducer: float 0.7 must never enter the certified path."""
    gap = F(139999999999999991, 100000000000000000)
    circles = [
        Circle(F(0), F(0), F(2)),
        Circle(F(4) + gap, F(0), F(2)),
    ]
    result = ReachEngine(
        pieces_per_quarter=4,
        max_depth=130,
        max_boxes=2_000_000,
    ).certify(circles, 0.7)
    assert result.status is not Status.VALID
