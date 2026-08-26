from fractions import Fraction as F
import random

from reach_engine import Circle, ReachEngine, Status


def deep_engine():
    return ReachEngine(pieces_per_quarter=4, max_depth=130, max_boxes=2_000_000)


def test_red_team_float_counterexample_is_rejected():
    gap = F(139999999999999991, 100000000000000000)
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4) + gap, F(0), F(2))]
    result = deep_engine().certify(circles, 0.7)
    assert result.status is Status.INPUT_INVALID


def test_red_team_exact_binary_float_value_is_not_valid():
    gap = F(139999999999999991, 100000000000000000)
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4) + gap, F(0), F(2))]
    result = deep_engine().certify(circles, F.from_float(0.7))
    assert result.status is not Status.VALID


def test_red_team_exact_decimal_value_is_not_valid():
    gap = F(139999999999999991, 100000000000000000)
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4) + gap, F(0), F(2))]
    result = deep_engine().certify(circles, F(7, 10))
    assert result.status is not Status.VALID


def test_near_external_tangency_strictly_disjoint_below_gap_is_valid():
    gap = F(1, 20)
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4) + gap, F(0), F(2))]
    result = ReachEngine(4, max_depth=40, max_boxes=600_000).certify(circles, F(1, 50))
    assert result.status is Status.VALID


def test_near_external_tangency_above_true_reach_is_not_valid():
    gap = F(1, 20)
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4) + gap, F(0), F(2))]
    result = ReachEngine(4, max_depth=40, max_boxes=600_000).certify(circles, F(3, 100))
    assert result.status is not Status.VALID


def test_annulus_equality_has_independent_regression():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(5))]
    result = ReachEngine(4, max_depth=14, max_boxes=80_000).certify(circles, F(3, 2))
    assert result.status is not Status.VALID


def test_periodic_seam_bottleneck_is_not_missed():
    # Closest points lie on x-axis quarter/seam representations.
    circles = [Circle(F(0), F(0), F(3)), Circle(F(8), F(0), F(3))]
    equality = ReachEngine(4, max_depth=18, max_boxes=200_000).certify(circles, F(1))
    above = ReachEngine(4, max_depth=22, max_boxes=400_000).certify(circles, F(11, 10))
    assert equality.status is not Status.INPUT_INVALID
    assert above.status is not Status.VALID


def test_three_components_hidden_short_gap_is_not_valid():
    circles = [
        Circle(F(0), F(0), F(2)),
        Circle(F(20), F(0), F(3)),
        Circle(F(24) + F(1, 10), F(0), F(1)),
    ]
    # Hidden gap between the last two boundaries is 1/10, so reach <= 1/20.
    result = ReachEngine(4, max_depth=32, max_boxes=600_000).certify(circles, F(3, 50))
    assert result.status is not Status.VALID


def analytic_reach_for_separated_axis_circles(circles):
    reach = min(c.radius for c in circles)
    for i, a in enumerate(circles):
        for b in circles[i + 1 :]:
            center_distance = abs(a.cx - b.cx)
            boundary_gap = center_distance - a.radius - b.radius
            reach = min(reach, boundary_gap / 2)
    return reach


def test_random_exact_rational_separated_links_against_analytic_reference():
    rng = random.Random(20260823)
    for _ in range(8):
        r1 = F(rng.randint(2, 5), rng.randint(1, 3))
        r2 = F(rng.randint(2, 5), rng.randint(1, 3))
        gap = F(rng.randint(1, 6), rng.randint(4, 10))
        circles = [
            Circle(F(0), F(0), r1),
            Circle(r1 + r2 + gap, F(0), r2),
        ]
        reach = analytic_reach_for_separated_axis_circles(circles)
        below = reach * F(9, 10)
        above = reach + F(1, 1000)
        below_result = ReachEngine(4, max_depth=36, max_boxes=800_000).certify(circles, below)
        above_result = ReachEngine(4, max_depth=36, max_boxes=800_000).certify(circles, above)
        assert below_result.status is Status.VALID
        assert above_result.status is not Status.VALID
