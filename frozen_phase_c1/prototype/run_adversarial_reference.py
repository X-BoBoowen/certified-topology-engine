from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import random
import sys
from typing import Iterable

from reach_engine import Circle, ReachEngine, Status


SEED = 20260823


def analytic_reach_collinear(circles: Iterable[Circle]) -> F:
    items = list(circles)
    if not items:
        raise ValueError("empty link")
    if any(c.cy != 0 for c in items):
        raise ValueError("reference helper only supports centers on the x-axis")
    reach = min(c.radius for c in items)
    for i, first in enumerate(items):
        for second in items[i + 1 :]:
            center_distance = abs(first.cx - second.cx)
            radius_sum = first.radius + second.radius
            radius_difference = abs(first.radius - second.radius)
            if center_distance > radius_sum:
                boundary_gap = center_distance - radius_sum
            elif center_distance < radius_difference:
                boundary_gap = radius_difference - center_distance
            else:
                raise ValueError("reference helper received intersecting/tangent circles")
            reach = min(reach, boundary_gap / F(2))
    return reach


def generated_links() -> list[tuple[str, list[Circle]]]:
    rng = random.Random(SEED)
    cases: list[tuple[str, list[Circle]]] = []

    for index in range(8):
        r1 = F(rng.randint(3, 10), rng.randint(2, 5))
        r2 = F(rng.randint(3, 10), rng.randint(2, 5))
        gap = F(rng.randint(2, 12), rng.randint(5, 20))
        center = r1 + r2 + gap
        cases.append(
            (
                f"random_external_{index:02d}",
                [Circle(F(0), F(0), r1), Circle(center, F(0), r2)],
            )
        )

    for index in range(4):
        inner_radius = F(rng.randint(3, 8), rng.randint(2, 5))
        offset = F(rng.randint(0, 5), rng.randint(4, 12))
        boundary_gap = F(rng.randint(2, 10), rng.randint(5, 18))
        outer_radius = inner_radius + offset + boundary_gap
        cases.append(
            (
                f"random_nested_{index:02d}",
                [
                    Circle(F(0), F(0), outer_radius),
                    Circle(offset, F(0), inner_radius),
                ],
            )
        )

    return cases


def run() -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    failures: list[str] = []
    for case_id, circles in generated_links():
        reference_reach = analytic_reach_collinear(circles)
        below = reference_reach * F(3, 4)
        above = reference_reach + min(F(1, 1000), reference_reach / F(20))
        engine = ReachEngine(pieces_per_quarter=4, max_depth=36, max_boxes=800_000)

        below_result = engine.certify(circles, below)
        above_result = engine.certify(circles, above)

        passed = (
            below_result.status is Status.VALID
            and above_result.status is not Status.VALID
            and below_result.accounting_ok
            and below_result.processing_accounting_ok
            and below_result.unresolved_accounting_ok
            and above_result.accounting_ok
            and above_result.processing_accounting_ok
            and above_result.unresolved_accounting_ok
        )
        row = {
            "id": case_id,
            "reference_reach": str(reference_reach),
            "below_r0": str(below),
            "below_status": below_result.status.name,
            "below_boxes": below_result.interval_boxes,
            "above_r0": str(above),
            "above_status": above_result.status.name,
            "above_boxes": above_result.interval_boxes,
            "passed": passed,
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
        if not passed:
            failures.append(case_id)
    return rows, failures


def main() -> int:
    rows, failures = run()
    output = Path(__file__).with_name("adversarial_reference_results.json")
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    if failures:
        print("adversarial reference failures:", ", ".join(failures), file=sys.stderr)
        return 1
    print(f"all {len(rows)} deterministic exact-rational reference cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
