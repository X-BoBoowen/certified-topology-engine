from __future__ import annotations

from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_case(module: ModuleType, r0: object) -> dict[str, object]:
    gap = F(139999999999999991, 100000000000000000)
    circles = [
        module.Circle(F(0), F(0), F(2)),
        module.Circle(F(4) + gap, F(0), F(2)),
    ]
    result = module.ReachEngine(
        pieces_per_quarter=4,
        max_depth=130,
        max_boxes=2_000_000,
    ).certify(circles, r0)
    return {
        "status": result.status.name,
        "interval_boxes": result.interval_boxes,
        "max_depth_seen": result.max_depth_seen,
        "unresolved_boxes": result.unresolved_boxes,
        "reason": result.reason,
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    legacy_path = root / "audit" / "legacy_unsound_reach_engine.py"
    if not legacy_path.exists():
        legacy_path = root / "original" / "reach_engine.py"
    patched_path = root / "reach_engine.py"

    legacy = load_module(legacy_path, "phase_c_legacy_unsound")
    patched = load_module(patched_path, "phase_c1_patched")

    rows = {
        "geometry": {
            "gap": "139999999999999991/100000000000000000",
            "true_reach": "139999999999999991/200000000000000000",
        },
        "before": {
            "float_0_7": run_case(legacy, 0.7),
            "fraction_from_float_0_7": run_case(legacy, F.from_float(0.7)),
        },
        "after": {
            "float_0_7": run_case(patched, 0.7),
            "fraction_from_float_0_7": run_case(patched, F.from_float(0.7)),
            "fraction_7_10": run_case(patched, F(7, 10)),
        },
    }
    print(json.dumps(rows, indent=2))

    passed = (
        rows["before"]["float_0_7"]["status"] == "VALID"
        and rows["after"]["float_0_7"]["status"] == "INPUT_INVALID"
        and rows["after"]["fraction_from_float_0_7"]["status"] != "VALID"
        and rows["after"]["fraction_7_10"]["status"] != "VALID"
    )
    print("REGRESSION_REPAIR_VERIFIED" if passed else "REGRESSION_REPAIR_FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
