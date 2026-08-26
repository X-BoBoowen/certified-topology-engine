from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from fractions import Fraction
from time import perf_counter
from typing import Iterable, TypeAlias


F = Fraction
ExactRationalInput: TypeAlias = Fraction | int


class ExactInputError(TypeError):
    """Raised when a value is not admitted by the certified numeric API."""


def exact_fraction(value: object, *, name: str) -> Fraction:
    """Return an exact rational accepted by the certified core.

    Only ``fractions.Fraction`` and non-boolean built-in integers are accepted.
    Floats, Decimal values, booleans, strings, and custom numeric types are
    rejected rather than guessed or silently converted.
    """

    if isinstance(value, bool):
        raise ExactInputError(f"{name} must not be bool")
    if type(value) is Fraction:
        return value
    if type(value) is int:
        return Fraction(value)
    raise ExactInputError(
        f"{name} must be fractions.Fraction or a non-boolean built-in int; "
        f"got {type(value).__name__}"
    )


def parse_rational(text: str) -> Fraction:
    """Parse decimal/integer/fraction text exactly, outside ``certify()``.

    Examples:
        ``parse_rational("0.7") == Fraction(7, 10)``
        ``parse_rational("14/20") == Fraction(7, 10)``
    """

    if type(text) is not str:
        raise TypeError("parse_rational expects a string")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("empty rational string")
    try:
        return Fraction(cleaned)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid exact rational text: {text!r}") from exc


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self) -> None:
        lo = exact_fraction(self.lo, name="interval.lo")
        hi = exact_fraction(self.hi, name="interval.hi")
        object.__setattr__(self, "lo", lo)
        object.__setattr__(self, "hi", hi)
        if lo > hi:
            raise ValueError("invalid interval")

    @staticmethod
    def point(x: ExactRationalInput) -> "Interval":
        q = exact_fraction(x, name="interval point")
        return Interval(q, q)

    @property
    def width(self) -> F:
        return self.hi - self.lo

    @property
    def mid(self) -> F:
        return (self.lo + self.hi) / F(2)

    def contains_zero(self) -> bool:
        return self.lo <= 0 <= self.hi

    def __add__(self, other: "Interval | ExactRationalInput") -> "Interval":
        o = as_interval(other)
        return Interval(self.lo + o.lo, self.hi + o.hi)

    __radd__ = __add__

    def __neg__(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other: "Interval | ExactRationalInput") -> "Interval":
        return self + (-as_interval(other))

    def __rsub__(self, other: "Interval | ExactRationalInput") -> "Interval":
        return as_interval(other) - self

    def __mul__(self, other: "Interval | ExactRationalInput") -> "Interval":
        o = as_interval(other)
        values = (
            self.lo * o.lo,
            self.lo * o.hi,
            self.hi * o.lo,
            self.hi * o.hi,
        )
        return Interval(min(values), max(values))

    __rmul__ = __mul__

    def reciprocal(self) -> "Interval":
        if self.contains_zero():
            raise ZeroDivisionError("interval contains zero")
        values = (F(1) / self.lo, F(1) / self.hi)
        return Interval(min(values), max(values))

    def __truediv__(self, other: "Interval | ExactRationalInput") -> "Interval":
        return self * as_interval(other).reciprocal()

    def square(self) -> "Interval":
        if self.contains_zero():
            return Interval(F(0), max(self.lo * self.lo, self.hi * self.hi))
        values = (self.lo * self.lo, self.hi * self.hi)
        return Interval(min(values), max(values))


def as_interval(value: Interval | ExactRationalInput) -> Interval:
    if isinstance(value, Interval):
        return value
    return Interval.point(exact_fraction(value, name="interval operand"))


def bisect_interval_cover(parent: Interval) -> tuple[Interval, Interval]:
    """Closed cover-preserving bisection.

    The two children share the midpoint. Their union covers the complete
    parent interval; they are not claimed to be a pairwise-disjoint partition.
    """

    midpoint = parent.mid
    return Interval(parent.lo, midpoint), Interval(midpoint, parent.hi)


@dataclass(frozen=True)
class Circle:
    """Raw circle input record.

    Runtime exactness and geometry are validated at the beginning of
    ``ReachEngine.certify``. This permits invalid calls to return the explicit
    ``INPUT_INVALID`` status rather than entering certificate arithmetic.
    """

    cx: object
    cy: object
    radius: object


@dataclass(frozen=True)
class CirclePatch:
    circle_id: int
    global_index: int
    total_on_loop: int
    quarter: int
    t: Interval
    circle: Circle

    def position(self, parameter: Interval) -> tuple[Interval, Interval]:
        t2 = parameter * parameter
        denominator = 1 + t2
        base_x = (1 - t2) / denominator
        base_y = (2 * parameter) / denominator
        x, y = rotate_quarter(base_x, base_y, self.quarter)
        return (
            self.circle.cx + self.circle.radius * x,
            self.circle.cy + self.circle.radius * y,
        )

    def tangent(self, parameter: Interval) -> tuple[Interval, Interval]:
        t2 = parameter * parameter
        denominator2 = (1 + t2) * (1 + t2)
        dx = (-4 * parameter) / denominator2
        dy = (2 * (1 - t2)) / denominator2
        x, y = rotate_quarter(dx, dy, self.quarter)
        return (self.circle.radius * x, self.circle.radius * y)

    def local_with(self, other: "CirclePatch") -> bool:
        if self.circle_id != other.circle_id:
            return False
        patch_count = self.total_on_loop
        index_distance = abs(self.global_index - other.global_index)
        cyclic_distance = min(index_distance, patch_count - index_distance)
        # Same/adjacent rational quarter-subpatches lie in a common circular
        # guard arc of angular width strictly below pi. For a circle, a
        # nonzero chord is orthogonal to an endpoint tangent only at an
        # antipodal separation, so every such pair is locally excluded.
        return cyclic_distance <= 1


def rotate_quarter(
    x: Interval, y: Interval, quarter: int
) -> tuple[Interval, Interval]:
    quarter %= 4
    if quarter == 0:
        return x, y
    if quarter == 1:
        return -y, x
    if quarter == 2:
        return -x, -y
    return y, -x


class Status(Enum):
    VALID = auto()
    UNKNOWN = auto()
    CURVATURE_FAIL = auto()
    INPUT_INVALID = auto()


@dataclass
class ReachResult:
    status: Status
    r0: F | None
    runtime_seconds: float
    patch_count: int
    all_patch_pairs: int
    initial_pair_boxes: int
    local_pruned: int
    distance_pruned: int
    normal_pruned: int
    interval_boxes: int
    subdivision_children_enqueued: int
    queued_boxes_at_exit: int
    max_depth_seen: int
    max_depth_unresolved_boxes: int
    unresolved_boxes: int
    reason: str

    @property
    def generated_boxes(self) -> int:
        return self.initial_pair_boxes + self.subdivision_children_enqueued

    @property
    def subdivision_parent_boxes(self) -> int:
        if self.subdivision_children_enqueued % 2:
            raise AssertionError("subdivision child count must be even")
        return self.subdivision_children_enqueued // 2

    @property
    def accounting_ok(self) -> bool:
        return self.generated_boxes == self.interval_boxes + self.queued_boxes_at_exit

    @property
    def processing_accounting_ok(self) -> bool:
        return self.interval_boxes == (
            self.distance_pruned
            + self.normal_pruned
            + self.max_depth_unresolved_boxes
            + self.subdivision_parent_boxes
        )

    @property
    def unresolved_accounting_ok(self) -> bool:
        return self.unresolved_boxes == (
            self.max_depth_unresolved_boxes + self.queued_boxes_at_exit
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status.name,
            "r0": None if self.r0 is None else str(self.r0),
            "runtime_seconds": self.runtime_seconds,
            "patch_count": self.patch_count,
            "all_patch_pairs": self.all_patch_pairs,
            "initial_pair_boxes": self.initial_pair_boxes,
            "local_pruned": self.local_pruned,
            "distance_pruned": self.distance_pruned,
            "normal_pruned": self.normal_pruned,
            "interval_boxes": self.interval_boxes,
            "subdivision_children_enqueued": self.subdivision_children_enqueued,
            "subdivision_parent_boxes": self.subdivision_parent_boxes,
            "generated_boxes": self.generated_boxes,
            "queued_boxes_at_exit": self.queued_boxes_at_exit,
            "max_depth_seen": self.max_depth_seen,
            "max_depth_unresolved_boxes": self.max_depth_unresolved_boxes,
            "unresolved_boxes": self.unresolved_boxes,
            "accounting_ok": self.accounting_ok,
            "processing_accounting_ok": self.processing_accounting_ok,
            "unresolved_accounting_ok": self.unresolved_accounting_ok,
            "reason": self.reason,
        }


@dataclass
class PairBox:
    a: CirclePatch
    b: CirclePatch
    s: Interval
    t: Interval
    depth: int


class ReachEngine:
    """Exact-rational interval DCSD exclusion for an analytic circle atlas.

    This is an analytic-circle restricted reference engine. It is not a
    general spline reach engine.
    """

    def __init__(
        self,
        pieces_per_quarter: int = 4,
        max_depth: int = 18,
        max_boxes: int = 300_000,
    ) -> None:
        for name, value in (
            ("pieces_per_quarter", pieces_per_quarter),
            ("max_depth", max_depth),
            ("max_boxes", max_boxes),
        ):
            if type(value) is not int:
                raise TypeError(f"{name} must be a built-in int")
        if pieces_per_quarter < 2:
            raise ValueError("pieces_per_quarter must be at least 2")
        if max_depth < 0:
            raise ValueError("max_depth must be nonnegative")
        if max_boxes < 1:
            raise ValueError("max_boxes must be positive")
        self.pieces_per_quarter = pieces_per_quarter
        self.max_depth = max_depth
        self.max_boxes = max_boxes

    @staticmethod
    def _normalize_circle(circle: object, index: int) -> Circle:
        if type(circle) is not Circle:
            raise ExactInputError(f"circles[{index}] must be a Circle")
        cx = exact_fraction(circle.cx, name=f"circles[{index}].cx")
        cy = exact_fraction(circle.cy, name=f"circles[{index}].cy")
        radius = exact_fraction(circle.radius, name=f"circles[{index}].radius")
        if radius <= 0:
            raise ValueError(f"circles[{index}].radius must be positive")
        return Circle(cx, cy, radius)

    @classmethod
    def _normalize_circles(cls, circles: object) -> list[Circle]:
        if isinstance(circles, (str, bytes)):
            raise ExactInputError("circles must be an iterable of Circle objects")
        try:
            raw = list(circles)  # type: ignore[arg-type]
        except TypeError as exc:
            raise ExactInputError("circles must be an iterable of Circle objects") from exc
        if not raw:
            raise ValueError("empty circle link is not supported")
        return [cls._normalize_circle(circle, index) for index, circle in enumerate(raw)]

    @staticmethod
    def _validate_disjoint_embedded_link(circles: list[Circle]) -> None:
        for i, first in enumerate(circles):
            for j in range(i + 1, len(circles)):
                second = circles[j]
                dx = first.cx - second.cx
                dy = first.cy - second.cy
                center_distance2 = dx * dx + dy * dy
                sum_radius = first.radius + second.radius
                radius_difference = abs(first.radius - second.radius)
                externally_separated = center_distance2 > sum_radius * sum_radius
                strictly_nested = center_distance2 < radius_difference * radius_difference
                if externally_separated or strictly_nested:
                    continue

                if (
                    first.cx == second.cx
                    and first.cy == second.cy
                    and first.radius == second.radius
                ):
                    relation = "duplicate circle"
                elif center_distance2 == sum_radius * sum_radius:
                    relation = "external tangency"
                elif center_distance2 == radius_difference * radius_difference:
                    relation = "internal tangency"
                else:
                    relation = "transverse circle-boundary intersection"
                raise ValueError(
                    f"circle link is not pairwise-disjoint: pair ({i}, {j}) has {relation}"
                )

    def _build_atlas_exact(self, circles: list[Circle]) -> list[CirclePatch]:
        patches: list[CirclePatch] = []
        per_loop = 4 * self.pieces_per_quarter
        for circle_id, circle in enumerate(circles):
            for quarter in range(4):
                for piece in range(self.pieces_per_quarter):
                    lo = F(piece, self.pieces_per_quarter)
                    hi = F(piece + 1, self.pieces_per_quarter)
                    index = quarter * self.pieces_per_quarter + piece
                    patches.append(
                        CirclePatch(
                            circle_id=circle_id,
                            global_index=index,
                            total_on_loop=per_loop,
                            quarter=quarter,
                            t=Interval(lo, hi),
                            circle=circle,
                        )
                    )
        return patches

    def build_atlas(self, circles: Iterable[Circle]) -> list[CirclePatch]:
        normalized = self._normalize_circles(circles)
        self._validate_disjoint_embedded_link(normalized)
        return self._build_atlas_exact(normalized)

    @staticmethod
    def _squared_distance_threshold(r0: ExactRationalInput) -> Fraction:
        exact_r0 = exact_fraction(r0, name="r0")
        two_r0 = F(2) * exact_r0
        threshold2 = two_r0 * two_r0
        if type(threshold2) is not Fraction:
            raise AssertionError("distance threshold left exact rational arithmetic")
        return threshold2

    @staticmethod
    def _result(
        *,
        status: Status,
        r0: F | None,
        start: float,
        patch_count: int = 0,
        all_patch_pairs: int = 0,
        initial_pair_boxes: int = 0,
        local_pruned: int = 0,
        distance_pruned: int = 0,
        normal_pruned: int = 0,
        interval_boxes: int = 0,
        subdivision_children_enqueued: int = 0,
        queued_boxes_at_exit: int = 0,
        max_depth_seen: int = 0,
        max_depth_unresolved_boxes: int = 0,
        unresolved_boxes: int = 0,
        reason: str,
    ) -> ReachResult:
        result = ReachResult(
            status=status,
            r0=r0,
            runtime_seconds=perf_counter() - start,
            patch_count=patch_count,
            all_patch_pairs=all_patch_pairs,
            initial_pair_boxes=initial_pair_boxes,
            local_pruned=local_pruned,
            distance_pruned=distance_pruned,
            normal_pruned=normal_pruned,
            interval_boxes=interval_boxes,
            subdivision_children_enqueued=subdivision_children_enqueued,
            queued_boxes_at_exit=queued_boxes_at_exit,
            max_depth_seen=max_depth_seen,
            max_depth_unresolved_boxes=max_depth_unresolved_boxes,
            unresolved_boxes=unresolved_boxes,
            reason=reason,
        )
        if not result.accounting_ok:
            raise AssertionError("generated/processed/queued accounting invariant failed")
        if not result.processing_accounting_ok:
            raise AssertionError("processed-box outcome accounting invariant failed")
        if not result.unresolved_accounting_ok:
            raise AssertionError("unresolved-box accounting invariant failed")
        return result

    def certify(self, circles: object, r0: object) -> ReachResult:
        start = perf_counter()

        try:
            exact_r0 = exact_fraction(r0, name="r0")
        except ExactInputError as exc:
            return self._result(
                status=Status.INPUT_INVALID,
                r0=None,
                start=start,
                reason=str(exc),
            )
        if exact_r0 <= 0:
            return self._result(
                status=Status.INPUT_INVALID,
                r0=exact_r0,
                start=start,
                reason="r0 must be positive",
            )

        try:
            exact_circles = self._normalize_circles(circles)
            self._validate_disjoint_embedded_link(exact_circles)
        except (ExactInputError, ValueError) as exc:
            return self._result(
                status=Status.INPUT_INVALID,
                r0=exact_r0,
                start=start,
                reason=str(exc),
            )

        atlas = self._build_atlas_exact(exact_circles)
        patch_count = len(atlas)
        all_patch_pairs = patch_count * (patch_count + 1) // 2

        # A circle's curvature radius equals its exact radius. Equality is allowed.
        if any(circle.radius < exact_r0 for circle in exact_circles):
            return self._result(
                status=Status.CURVATURE_FAIL,
                r0=exact_r0,
                start=start,
                patch_count=patch_count,
                all_patch_pairs=all_patch_pairs,
                reason="curvature bound 1/R <= 1/r0 fails",
            )

        queue: deque[PairBox] = deque()
        local_pruned = 0
        for i, first in enumerate(atlas):
            for second in atlas[i:]:
                if first.local_with(second):
                    local_pruned += 1
                    continue
                queue.append(PairBox(first, second, first.t, second.t, 0))

        initial_pair_boxes = len(queue)
        distance_pruned = 0
        normal_pruned = 0
        interval_boxes = 0
        subdivision_children_enqueued = 0
        max_depth_seen = 0
        max_depth_unresolved_boxes = 0

        threshold2 = self._squared_distance_threshold(exact_r0)

        while queue:
            if interval_boxes >= self.max_boxes:
                queued_boxes_at_exit = len(queue)
                unresolved_total = max_depth_unresolved_boxes + queued_boxes_at_exit
                return self._result(
                    status=Status.UNKNOWN,
                    r0=exact_r0,
                    start=start,
                    patch_count=patch_count,
                    all_patch_pairs=all_patch_pairs,
                    initial_pair_boxes=initial_pair_boxes,
                    local_pruned=local_pruned,
                    distance_pruned=distance_pruned,
                    normal_pruned=normal_pruned,
                    interval_boxes=interval_boxes,
                    subdivision_children_enqueued=subdivision_children_enqueued,
                    queued_boxes_at_exit=queued_boxes_at_exit,
                    max_depth_seen=max_depth_seen,
                    max_depth_unresolved_boxes=max_depth_unresolved_boxes,
                    unresolved_boxes=unresolved_total,
                    reason="interval box budget exhausted",
                )

            box = queue.popleft()
            interval_boxes += 1
            max_depth_seen = max(max_depth_seen, box.depth)

            first_position = box.a.position(box.s)
            second_position = box.b.position(box.t)
            chord = (
                first_position[0] - second_position[0],
                first_position[1] - second_position[1],
            )
            distance2 = chord[0].square() + chord[1].square()

            if distance2.lo >= threshold2:
                distance_pruned += 1
                continue

            first_tangent = box.a.tangent(box.s)
            second_tangent = box.b.tangent(box.t)
            g1 = chord[0] * first_tangent[0] + chord[1] * first_tangent[1]
            g2 = chord[0] * second_tangent[0] + chord[1] * second_tangent[1]

            if not g1.contains_zero() or not g2.contains_zero():
                normal_pruned += 1
                continue

            if box.depth >= self.max_depth:
                max_depth_unresolved_boxes += 1
                continue

            # Closed, cover-preserving bisection. The children share the
            # midpoint; no pairwise-disjoint partition claim is made.
            if box.s.width >= box.t.width:
                left, right = bisect_interval_cover(box.s)
                queue.append(PairBox(box.a, box.b, left, box.t, box.depth + 1))
                queue.append(PairBox(box.a, box.b, right, box.t, box.depth + 1))
            else:
                left, right = bisect_interval_cover(box.t)
                queue.append(PairBox(box.a, box.b, box.s, left, box.depth + 1))
                queue.append(PairBox(box.a, box.b, box.s, right, box.depth + 1))
            subdivision_children_enqueued += 2

        if max_depth_unresolved_boxes:
            return self._result(
                status=Status.UNKNOWN,
                r0=exact_r0,
                start=start,
                patch_count=patch_count,
                all_patch_pairs=all_patch_pairs,
                initial_pair_boxes=initial_pair_boxes,
                local_pruned=local_pruned,
                distance_pruned=distance_pruned,
                normal_pruned=normal_pruned,
                interval_boxes=interval_boxes,
                subdivision_children_enqueued=subdivision_children_enqueued,
                queued_boxes_at_exit=0,
                max_depth_seen=max_depth_seen,
                max_depth_unresolved_boxes=max_depth_unresolved_boxes,
                unresolved_boxes=max_depth_unresolved_boxes,
                reason="unresolved boxes at maximum subdivision depth",
            )

        return self._result(
            status=Status.VALID,
            r0=exact_r0,
            start=start,
            patch_count=patch_count,
            all_patch_pairs=all_patch_pairs,
            initial_pair_boxes=initial_pair_boxes,
            local_pruned=local_pruned,
            distance_pruned=distance_pruned,
            normal_pruned=normal_pruned,
            interval_boxes=interval_boxes,
            subdivision_children_enqueued=subdivision_children_enqueued,
            queued_boxes_at_exit=0,
            max_depth_seen=max_depth_seen,
            max_depth_unresolved_boxes=0,
            unresolved_boxes=0,
            reason="all nonlocal patch-pair boxes excluded",
        )
