from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import sys
from typing import Iterable

from reach_engine import Circle, ReachEngine, Status


LEGACY_CASES = [
    {
        "id": "S1_single_circle",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(3))],
        "reference_reach": "3",
        "r0": F(2),
        "expected": "VALID",
    },
    {
        "id": "S2_two_separated_circles",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(10), F(0), F(3))],
        "reference_reach": "2",
        "r0": F(3, 2),
        "expected": "VALID",
    },
    {
        "id": "S3_concentric_annulus",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(5))],
        "reference_reach": "3/2",
        "r0": F(7, 5),
        "expected": "VALID",
    },
    {
        "id": "S3b_annulus_equality",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(5))],
        "reference_reach": "3/2",
        "r0": F(3, 2),
        "expected": "UNKNOWN_ALLOWED",
        "max_depth": 14,
        "max_boxes": 80_000,
    },
    {
        "id": "S4_near_parallel_large_loops",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(20)), Circle(F(202, 5), F(0), F(20))],
        "reference_reach": "1/5",
        "r0": F(19, 100),
        "expected": "VALID",
        "max_depth": 22,
        "max_boxes": 500_000,
    },
    {
        "id": "S5_exact_equality_pair",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(5)), Circle(F(12), F(0), F(5))],
        "reference_reach": "1",
        "r0": F(1),
        "expected": "UNKNOWN_ALLOWED",
        "max_depth": 14,
        "max_boxes": 80_000,
    },
    {
        "id": "S6_high_curvature_fails",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(3, 4))],
        "reference_reach": "3/4",
        "r0": F(1),
        "expected": "CURVATURE_FAIL",
    },
    {
        "id": "S6b_high_curvature_strict_valid",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(3, 4))],
        "reference_reach": "3/4",
        "r0": F(7, 10),
        "expected": "VALID",
    },
    {
        "id": "S7_low_curvature_global_bottleneck",
        "category": "legacy",
        "circles": [Circle(F(0), F(0), F(20)), Circle(F(202, 5), F(0), F(20))],
        "reference_reach": "1/5",
        "r0": F(1),
        "expected": "NOT_VALID",
        "max_depth": 14,
        "max_boxes": 80_000,
    },
    {
        "id": "S8_nested_and_multiple_components",
        "category": "legacy",
        "circles": [
            Circle(F(0), F(0), F(2)),
            Circle(F(0), F(0), F(5)),
            Circle(F(20), F(0), F(3)),
        ],
        "reference_reach": "3/2",
        "r0": F(7, 5),
        "expected": "VALID",
        "max_depth": 20,
        "max_boxes": 400_000,
    },
]

_RED_GAP = F(139999999999999991, 100000000000000000)
ADVERSARIAL_CASES = [
    {
        "id": "A1_red_team_float_r0_rejected",
        "category": "adversarial",
        "circles": [
            Circle(F(0), F(0), F(2)),
            Circle(F(4) + _RED_GAP, F(0), F(2)),
        ],
        "reference_reach": str(_RED_GAP / 2),
        "r0": 0.7,
        "expected": "INPUT_INVALID",
        "max_depth": 130,
        "max_boxes": 2_000_000,
    },
    {
        "id": "A2_red_team_exact_binary_float_not_valid",
        "category": "adversarial",
        "circles": [
            Circle(F(0), F(0), F(2)),
            Circle(F(4) + _RED_GAP, F(0), F(2)),
        ],
        "reference_reach": str(_RED_GAP / 2),
        "r0": F.from_float(0.7),
        "expected": "NOT_VALID",
        "max_depth": 130,
        "max_boxes": 2_000_000,
    },
    {
        "id": "A3_red_team_exact_decimal_not_valid",
        "category": "adversarial",
        "circles": [
            Circle(F(0), F(0), F(2)),
            Circle(F(4) + _RED_GAP, F(0), F(2)),
        ],
        "reference_reach": str(_RED_GAP / 2),
        "r0": F(7, 10),
        "expected": "NOT_VALID",
        "max_depth": 130,
        "max_boxes": 2_000_000,
    },
    {
        "id": "A4_near_tangent_strict_margin_valid",
        "category": "adversarial",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(81, 20), F(0), F(2))],
        "reference_reach": "1/40",
        "r0": F(1, 50),
        "expected": "VALID",
        "max_depth": 40,
        "max_boxes": 600_000,
    },
    {
        "id": "A5_near_tangent_above_reach_not_valid",
        "category": "adversarial",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(81, 20), F(0), F(2))],
        "reference_reach": "1/40",
        "r0": F(3, 100),
        "expected": "NOT_VALID",
        "max_depth": 40,
        "max_boxes": 600_000,
    },
    {
        "id": "A6_periodic_seam_bottleneck",
        "category": "adversarial",
        "circles": [Circle(F(0), F(0), F(3)), Circle(F(8), F(0), F(3))],
        "reference_reach": "1",
        "r0": F(11, 10),
        "expected": "NOT_VALID",
        "max_depth": 24,
        "max_boxes": 500_000,
    },
    {
        "id": "A7_three_components_hidden_short_gap",
        "category": "adversarial",
        "circles": [
            Circle(F(0), F(0), F(2)),
            Circle(F(20), F(0), F(3)),
            Circle(F(241, 10), F(0), F(1)),
        ],
        "reference_reach": "1/20",
        "r0": F(3, 50),
        "expected": "NOT_VALID",
        "max_depth": 32,
        "max_boxes": 600_000,
    },
    {
        "id": "A8_external_tangent_invalid",
        "category": "invalid-input",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(4), F(0), F(2))],
        "reference_reach": None,
        "r0": F(1),
        "expected": "INPUT_INVALID",
    },
    {
        "id": "A9_internal_tangent_invalid",
        "category": "invalid-input",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(1), F(0), F(1))],
        "reference_reach": None,
        "r0": F(1, 2),
        "expected": "INPUT_INVALID",
    },
    {
        "id": "A10_intersection_invalid",
        "category": "invalid-input",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(3), F(0), F(2))],
        "reference_reach": None,
        "r0": F(1),
        "expected": "INPUT_INVALID",
    },
    {
        "id": "A11_duplicate_invalid",
        "category": "invalid-input",
        "circles": [Circle(F(0), F(0), F(2)), Circle(F(0), F(0), F(2))],
        "reference_reach": None,
        "r0": F(1),
        "expected": "INPUT_INVALID",
    },
    {
        "id": "A12_empty_invalid",
        "category": "invalid-input",
        "circles": [],
        "reference_reach": None,
        "r0": F(1),
        "expected": "INPUT_INVALID",
    },
]

CASES = LEGACY_CASES + ADVERSARIAL_CASES


def matches_expected(expected: str, actual: Status) -> bool:
    """Formal expected-status semantics used by the executable suite oracle."""

    if expected == "VALID":
        return actual is Status.VALID
    if expected == "CURVATURE_FAIL":
        return actual is Status.CURVATURE_FAIL
    if expected == "INPUT_INVALID":
        return actual is Status.INPUT_INVALID
    if expected == "UNKNOWN_ALLOWED":
        # Equality is mathematically certifiable, but this semi-decision
        # implementation is permitted to return UNKNOWN.
        return actual in {Status.VALID, Status.UNKNOWN}
    if expected == "NOT_VALID":
        return actual is not Status.VALID
    raise ValueError(f"unknown expected-status rule: {expected}")


def run_cases(cases: Iterable[dict[str, object]] = CASES) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    mismatches: list[str] = []
    for case in cases:
        engine = ReachEngine(
            pieces_per_quarter=4,
            max_depth=int(case.get("max_depth", 18)),
            max_boxes=int(case.get("max_boxes", 300_000)),
        )
        result = engine.certify(case["circles"], case["r0"])
        passed = matches_expected(str(case["expected"]), result.status)
        row = {
            "id": case["id"],
            "category": case.get("category", "unspecified"),
            "reference_reach": case.get("reference_reach"),
            "expected": case["expected"],
            "expectation_passed": passed,
            **result.as_dict(),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
        if not passed:
            mismatches.append(
                f"{case['id']}: expected {case['expected']}, got {result.status.name}"
            )
    return rows, mismatches


def main(
    cases: Iterable[dict[str, object]] = CASES,
    output: Path | None = None,
) -> int:
    rows, mismatches = run_cases(cases)
    if output is None:
        output = Path(__file__).with_name("synthetic_results.json")
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    if mismatches:
        print("scenario expectation failures:", file=sys.stderr)
        for message in mismatches:
            print(f"- {message}", file=sys.stderr)
        return 1
    print(f"all {len(rows)} scenario expectations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
