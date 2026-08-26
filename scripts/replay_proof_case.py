from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from phase_c2a import GeneralReachEngine
from phase_c2a.scenarios import base_circle_scenarios, knot_scenarios, make_field


def main():
    if len(sys.argv) != 2:
        print(json.dumps({'accepted': False, 'error': 'expected one proof-case path'}))
        return 2
    case = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    scenarios = {
        scenario.name: scenario
        for scenario in [*base_circle_scenarios(), *knot_scenarios()]
    }
    scenario = scenarios.get(case.get('scenario_name'))
    accepted = False
    error = None
    if scenario is None:
        error = 'unknown scenario identity'
    elif case.get('schema') != 'phase-c2b-replay-case-v1':
        error = 'unsupported replay-case schema'
    elif case.get('r0') != str(scenario.r0):
        error = 'exact r0 identity mismatch'
    else:
        budgets = case.get('engine_budgets', {})
        field, proposal = make_field(scenario)
        engine = GeneralReachEngine(
            pieces_per_quarter=budgets.get('pieces_per_quarter'),
            max_depth=budgets.get('max_depth'),
            max_boxes=budgets.get('max_boxes'),
        )
        accepted = engine.replay(field, scenario.r0, proposal, case.get('proof_log'))
    output = {'accepted': accepted, 'error': error, 'replay_pid': os.getpid()}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
