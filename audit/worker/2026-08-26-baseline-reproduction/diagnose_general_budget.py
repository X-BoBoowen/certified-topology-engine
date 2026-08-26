from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from phase_c2a import GeneralReachEngine
from phase_c2a.frozen_oracle import load_frozen_module
from phase_c2a.scenarios import base_circle_scenarios, knot_scenarios, make_field


oracle = load_frozen_module()
for scenario in [*base_circle_scenarios(), *knot_scenarios()]:
    field, proposal = make_field(scenario)
    started = time.perf_counter()
    result = GeneralReachEngine(max_depth=40, max_boxes=800_000).certify(
        field, scenario.r0, proposal
    )
    circles = [oracle.Circle(c.cx, c.cy, c.radius) for c in proposal.circles]
    oracle_max_depth = 40 if result.status.value == 'VALID' else 0
    oracle_max_boxes = 800_000 if result.status.value == 'VALID' else 1_000
    oracle_result = oracle.ReachEngine(
        pieces_per_quarter=4,
        max_depth=oracle_max_depth,
        max_boxes=oracle_max_boxes,
    ).certify(circles, scenario.r0)
    print(
        json.dumps(
            {
                'name': scenario.name,
                'engine_status': result.status.value,
                'oracle_status': getattr(
                    oracle_result.status,
                    'name',
                    str(oracle_result.status).split('.')[-1],
                ),
                'oracle_max_depth': oracle_max_depth,
                'oracle_max_boxes': oracle_max_boxes,
                'runtime_seconds': time.perf_counter() - started,
            },
            sort_keys=True,
        ),
        flush=True,
    )
