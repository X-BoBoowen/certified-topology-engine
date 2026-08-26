from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from fractions import Fraction
from time import perf_counter
from typing import Iterable


F = Fraction


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError("invalid interval")

    @staticmethod
    def point(x: F) -> "Interval":
        return Interval(x, x)

    @property
    def width(self) -> F:
        return self.hi - self.lo

    @property
    def mid(self) -> F:
        return (self.lo + self.hi) / 2

    def contains_zero(self) -> bool:
        return self.lo <= 0 <= self.hi

    def __add__(self, other: "Interval | F | int") -> "Interval":
        o = as_interval(other)
        return Interval(self.lo + o.lo, self.hi + o.hi)

    __radd__ = __add__

    def __neg__(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other: "Interval | F | int") -> "Interval":
        return self + (-as_interval(other))

    def __rsub__(self, other: "Interval | F | int") -> "Interval":
        return as_interval(other) - self

    def __mul__(self, other: "Interval | F | int") -> "Interval":
        o = as_interval(other)
        vals = (
            self.lo * o.lo,
            self.lo * o.hi,
            self.hi * o.lo,
            self.hi * o.hi,
        )
        return Interval(min(vals), max(vals))

    __rmul__ = __mul__

    def reciprocal(self) -> "Interval":
        if self.contains_zero():
            raise ZeroDivisionError("interval contains zero")
        vals = (F(1, 1) / self.lo, F(1, 1) / self.hi)
        return Interval(min(vals), max(vals))

    def __truediv__(self, other: "Interval | F | int") -> "Interval":
        return self * as_interval(other).reciprocal()

    def square(self) -> "Interval":
        if self.contains_zero():
            return Interval(F(0), max(self.lo * self.lo, self.hi * self.hi))
        vals = (self.lo * self.lo, self.hi * self.hi)
        return Interval(min(vals), max(vals))


def as_interval(x: Interval | F | int) -> Interval:
    if isinstance(x, Interval):
        return x
    if not isinstance(x, Fraction):
        x = F(x)
    return Interval.point(x)


@dataclass(frozen=True)
class Circle:
    cx: F
    cy: F
    radius: F

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError("circle radius must be positive")


@dataclass(frozen=True)
class CirclePatch:
    circle_id: int
    global_index: int
    total_on_loop: int
    quarter: int
    t: Interval
    circle: Circle

    def position(self, ti: Interval) -> tuple[Interval, Interval]:
        t2 = ti * ti
        den = 1 + t2
        bx = (1 - t2) / den
        by = (2 * ti) / den
        x, y = rotate_quarter(bx, by, self.quarter)
        return (
            self.circle.cx + self.circle.radius * x,
            self.circle.cy + self.circle.radius * y,
        )

    def tangent(self, ti: Interval) -> tuple[Interval, Interval]:
        t2 = ti * ti
        den2 = (1 + t2) * (1 + t2)
        dx = (-4 * ti) / den2
        dy = (2 * (1 - t2)) / den2
        x, y = rotate_quarter(dx, dy, self.quarter)
        return (self.circle.radius * x, self.circle.radius * y)

    def local_with(self, other: "CirclePatch") -> bool:
        if self.circle_id != other.circle_id:
            return False
        n = self.total_on_loop
        d = abs(self.global_index - other.global_index)
        cyclic = min(d, n - d)
        # Same/adjacent rational quarter-subpatches lie in a common
        # circular guard arc of angular width strictly below pi.  For a
        # circle, a nonzero chord is orthogonal to the endpoint tangent
        # only at an antipodal separation, so every such pair is locally
        # excluded.  This is the circle-specific guard-chart certificate
        # used by the reference suite.
        return cyclic <= 1


def rotate_quarter(x: Interval, y: Interval, q: int) -> tuple[Interval, Interval]:
    q %= 4
    if q == 0:
        return x, y
    if q == 1:
        return -y, x
    if q == 2:
        return -x, -y
    return y, -x


class Status(Enum):
    VALID = auto()
    UNKNOWN = auto()
    CURVATURE_FAIL = auto()


@dataclass
class ReachResult:
    status: Status
    r0: F
    runtime_seconds: float
    patch_count: int
    all_patch_pairs: int
    local_pruned: int
    distance_pruned: int
    normal_pruned: int
    interval_boxes: int
    max_depth_seen: int
    unresolved_boxes: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status.name,
            "r0": str(self.r0),
            "runtime_seconds": self.runtime_seconds,
            "patch_count": self.patch_count,
            "all_patch_pairs": self.all_patch_pairs,
            "local_pruned": self.local_pruned,
            "distance_pruned": self.distance_pruned,
            "normal_pruned": self.normal_pruned,
            "interval_boxes": self.interval_boxes,
            "max_depth_seen": self.max_depth_seen,
            "unresolved_boxes": self.unresolved_boxes,
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

    This is a deliberately small reference implementation. It proves
    soundness of the exhaustive pair-cover/pair-pruning architecture on
    rational circles; it is not the spline-atlas implementation.
    """

    def __init__(
        self,
        pieces_per_quarter: int = 4,
        max_depth: int = 18,
        max_boxes: int = 300_000,
    ) -> None:
        if pieces_per_quarter < 2:
            raise ValueError("pieces_per_quarter must be at least 2")
        self.pieces_per_quarter = pieces_per_quarter
        self.max_depth = max_depth
        self.max_boxes = max_boxes

    def build_atlas(self, circles: Iterable[Circle]) -> list[CirclePatch]:
        patches: list[CirclePatch] = []
        per_loop = 4 * self.pieces_per_quarter
        for circle_id, circle in enumerate(circles):
            for q in range(4):
                for j in range(self.pieces_per_quarter):
                    lo = F(j, self.pieces_per_quarter)
                    hi = F(j + 1, self.pieces_per_quarter)
                    idx = q * self.pieces_per_quarter + j
                    patches.append(
                        CirclePatch(
                            circle_id=circle_id,
                            global_index=idx,
                            total_on_loop=per_loop,
                            quarter=q,
                            t=Interval(lo, hi),
                            circle=circle,
                        )
                    )
        return patches

    def certify(self, circles: list[Circle], r0: F) -> ReachResult:
        start = perf_counter()
        if r0 <= 0:
            raise ValueError("r0 must be positive")

        atlas = self.build_atlas(circles)
        n = len(atlas)
        all_pairs = n * (n + 1) // 2

        # Curvature radius of a circle equals its radius. Equality is allowed.
        if any(c.radius < r0 for c in circles):
            return ReachResult(
                status=Status.CURVATURE_FAIL,
                r0=r0,
                runtime_seconds=perf_counter() - start,
                patch_count=n,
                all_patch_pairs=all_pairs,
                local_pruned=0,
                distance_pruned=0,
                normal_pruned=0,
                interval_boxes=0,
                max_depth_seen=0,
                unresolved_boxes=0,
                reason="curvature bound 1/R <= 1/r0 fails",
            )

        queue: deque[PairBox] = deque()
        local_pruned = 0
        for i, a in enumerate(atlas):
            for b in atlas[i:]:
                if a.local_with(b):
                    local_pruned += 1
                    continue
                queue.append(PairBox(a, b, a.t, b.t, 0))

        distance_pruned = 0
        normal_pruned = 0
        interval_boxes = 0
        max_depth_seen = 0
        unresolved = 0
        threshold2 = (2 * r0) * (2 * r0)

        while queue:
            if interval_boxes >= self.max_boxes:
                unresolved = len(queue)
                return ReachResult(
                    status=Status.UNKNOWN,
                    r0=r0,
                    runtime_seconds=perf_counter() - start,
                    patch_count=n,
                    all_patch_pairs=all_pairs,
                    local_pruned=local_pruned,
                    distance_pruned=distance_pruned,
                    normal_pruned=normal_pruned,
                    interval_boxes=interval_boxes,
                    max_depth_seen=max_depth_seen,
                    unresolved_boxes=unresolved,
                    reason="interval box budget exhausted",
                )

            box = queue.popleft()
            interval_boxes += 1
            max_depth_seen = max(max_depth_seen, box.depth)

            xa = box.a.position(box.s)
            xb = box.b.position(box.t)
            chord = (xa[0] - xb[0], xa[1] - xb[1])
            d2 = chord[0].square() + chord[1].square()

            if d2.lo >= threshold2:
                distance_pruned += 1
                continue

            ta = box.a.tangent(box.s)
            tb = box.b.tangent(box.t)
            g1 = chord[0] * ta[0] + chord[1] * ta[1]
            g2 = chord[0] * tb[0] + chord[1] * tb[1]

            if not g1.contains_zero() or not g2.contains_zero():
                normal_pruned += 1
                continue

            if box.depth >= self.max_depth:
                unresolved += 1
                continue

            # Deterministic subdivision of the wider parameter interval.
            if box.s.width >= box.t.width:
                m = box.s.mid
                queue.append(PairBox(box.a, box.b, Interval(box.s.lo, m), box.t, box.depth + 1))
                queue.append(PairBox(box.a, box.b, Interval(m, box.s.hi), box.t, box.depth + 1))
            else:
                m = box.t.mid
                queue.append(PairBox(box.a, box.b, box.s, Interval(box.t.lo, m), box.depth + 1))
                queue.append(PairBox(box.a, box.b, box.s, Interval(m, box.t.hi), box.depth + 1))

        if unresolved:
            return ReachResult(
                status=Status.UNKNOWN,
                r0=r0,
                runtime_seconds=perf_counter() - start,
                patch_count=n,
                all_patch_pairs=all_pairs,
                local_pruned=local_pruned,
                distance_pruned=distance_pruned,
                normal_pruned=normal_pruned,
                interval_boxes=interval_boxes,
                max_depth_seen=max_depth_seen,
                unresolved_boxes=unresolved,
                reason="unresolved boxes at maximum subdivision depth",
            )

        return ReachResult(
            status=Status.VALID,
            r0=r0,
            runtime_seconds=perf_counter() - start,
            patch_count=n,
            all_patch_pairs=all_pairs,
            local_pruned=local_pruned,
            distance_pruned=distance_pruned,
            normal_pruned=normal_pruned,
            interval_boxes=interval_boxes,
            max_depth_seen=max_depth_seen,
            unresolved_boxes=0,
            reason="all nonlocal patch-pair boxes excluded",
        )
