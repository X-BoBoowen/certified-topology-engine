from decimal import Decimal
from fractions import Fraction as F

import reach_engine
from reach_engine import Circle, ReachEngine, Status


def engine(**kwargs):
    return ReachEngine(
        pieces_per_quarter=kwargs.get("pieces_per_quarter", 4),
        max_depth=kwargs.get("max_depth", 18),
        max_boxes=kwargs.get("max_boxes", 300_000),
    )


def valid_circle():
    return Circle(F(0), F(0), F(2))


def test_parse_rational_decimal_and_ratio_are_exact():
    assert reach_engine.parse_rational("0.7") == F(7, 10)
    assert reach_engine.parse_rational(" 14/20 ") == F(7, 10)
    assert isinstance(reach_engine.parse_rational("0.7"), F)


def test_float_r0_is_input_invalid():
    result = engine().certify([valid_circle()], 0.7)
    assert result.status is Status.INPUT_INVALID
    assert result.r0 is None
    assert result.interval_boxes == 0


def test_decimal_bool_and_custom_r0_are_input_invalid():
    class NumericLike:
        pass

    for value in (Decimal("0.7"), True, NumericLike()):
        result = engine().certify([valid_circle()], value)
        assert result.status is Status.INPUT_INVALID
        assert result.interval_boxes == 0


def test_integer_r0_is_explicitly_normalized_to_fraction():
    result = engine().certify([Circle(0, 0, 3)], 2)
    assert result.status is Status.VALID
    assert result.r0 == F(2)
    assert isinstance(result.r0, F)


def test_float_circle_fields_are_input_invalid():
    cases = [
        Circle(0.0, F(0), F(2)),
        Circle(F(0), 0.0, F(2)),
        Circle(F(0), F(0), 2.0),
    ]
    for circle in cases:
        result = engine().certify([circle], F(1))
        assert result.status is Status.INPUT_INVALID
        assert result.interval_boxes == 0


def test_bool_decimal_and_custom_circle_fields_are_input_invalid():
    class NumericLike:
        pass

    cases = [
        Circle(True, F(0), F(2)),
        Circle(F(0), Decimal("0"), F(2)),
        Circle(F(0), F(0), NumericLike()),
    ]
    for circle in cases:
        result = engine().certify([circle], F(1))
        assert result.status is Status.INPUT_INVALID
        assert result.interval_boxes == 0


def test_empty_input_is_input_invalid():
    result = engine().certify([], F(1))
    assert result.status is Status.INPUT_INVALID
    assert result.patch_count == 0


def test_nonpositive_radius_is_input_invalid():
    for radius in (F(0), F(-1)):
        result = engine().certify([Circle(F(0), F(0), radius)], F(1))
        assert result.status is Status.INPUT_INVALID
        assert result.interval_boxes == 0


def test_nonpositive_r0_is_input_invalid():
    for r0 in (F(0), F(-1)):
        result = engine().certify([valid_circle()], r0)
        assert result.status is Status.INPUT_INVALID
        assert result.interval_boxes == 0


def test_external_tangent_link_is_input_invalid():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4), F(0), F(2))]
    assert engine().certify(circles, F(1)).status is Status.INPUT_INVALID


def test_internal_tangent_link_is_input_invalid():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(1), F(0), F(1))]
    assert engine().certify(circles, F(1, 2)).status is Status.INPUT_INVALID


def test_transversely_intersecting_link_is_input_invalid():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(3), F(0), F(2))]
    assert engine().certify(circles, F(1)).status is Status.INPUT_INVALID


def test_duplicate_circle_is_input_invalid():
    circle = Circle(F(0), F(0), F(2))
    assert engine().certify([circle, circle], F(1)).status is Status.INPUT_INVALID


def test_nested_disjoint_circles_remain_valid_input():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(5))]
    result = engine(max_depth=20, max_boxes=400_000).certify(circles, F(7, 5))
    assert result.status is Status.VALID


def test_interval_adapter_rejects_float_defense_in_depth():
    try:
        reach_engine.as_interval(0.5)
    except TypeError:
        pass
    else:
        raise AssertionError("float must not be admitted into exact interval arithmetic")


def test_fraction_subclass_and_int_subclass_are_rejected():
    class FractionSubclass(F):
        pass

    class IntSubclass(int):
        pass

    for value in (FractionSubclass(1, 2), IntSubclass(1)):
        result = engine().certify([valid_circle()], value)
        assert result.status is Status.INPUT_INVALID


def test_rational_text_is_not_silently_accepted_by_certify():
    result = engine().certify([valid_circle()], "0.7")
    assert result.status is Status.INPUT_INVALID
    assert reach_engine.parse_rational("0.7") == F(7, 10)


def test_parse_rational_rejects_nonfinite_and_zero_denominator_text():
    for text in ("nan", "inf", "-inf", "1/0", ""):
        try:
            reach_engine.parse_rational(text)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{text!r} must not parse as an exact rational")


def test_distance_threshold_is_exact_fraction():
    threshold2 = ReachEngine._squared_distance_threshold(F(7, 10))
    assert type(threshold2) is F
    assert threshold2 == F(49, 25)


def test_build_atlas_rejects_invalid_circle_link():
    circles = [Circle(F(0), F(0), F(2)), Circle(F(4), F(0), F(2))]
    try:
        engine().build_atlas(circles)
    except ValueError:
        pass
    else:
        raise AssertionError("public atlas builder must enforce the link contract")


def test_nan_and_infinity_are_input_invalid():
    for value in (float("nan"), float("inf"), float("-inf")):
        result = engine().certify([valid_circle()], value)
        assert result.status is Status.INPUT_INVALID


def test_position_tangent_distance_and_orthogonality_intervals_stay_fractional():
    atlas = engine().build_atlas([Circle(F(0), F(0), F(3))])
    first = atlas[0]
    second = atlas[2]
    position_a = first.position(first.t)
    position_b = second.position(second.t)
    tangent_a = first.tangent(first.t)
    tangent_b = second.tangent(second.t)
    chord = (position_a[0] - position_b[0], position_a[1] - position_b[1])
    distance2 = chord[0].square() + chord[1].square()
    g1 = chord[0] * tangent_a[0] + chord[1] * tangent_a[1]
    g2 = chord[0] * tangent_b[0] + chord[1] * tangent_b[1]

    intervals = [*position_a, *position_b, *tangent_a, *tangent_b, distance2, g1, g2]
    for interval in intervals:
        assert type(interval.lo) is F
        assert type(interval.hi) is F


def test_circle_subclass_is_rejected_at_public_boundary():
    class CircleSubclass(Circle):
        pass

    result = engine().certify([CircleSubclass(F(0), F(0), F(2))], F(1))
    assert result.status is Status.INPUT_INVALID
