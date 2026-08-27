from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from phase_c2a import (
    ExactSerializationError,
    GeneralReachEngine,
    deserialize_exact_input,
)


def main():
    if len(sys.argv) != 2:
        print(json.dumps({'accepted': False, 'error': 'expected one proof-case path'}))
        return 2
    accepted = False
    error = None
    try:
        case = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        if type(case) is not dict or case.get('schema') != 'phase-c2b-replay-case-v2':
            raise ExactSerializationError('unsupported replay-case schema')
        if set(case) != {'schema', 'exact_input', 'engine_budgets', 'proof_log'}:
            raise ExactSerializationError('replay case has unexpected or missing fields')
        field, proposal, r0 = deserialize_exact_input(case.get('exact_input'))
        budgets = case.get('engine_budgets', {})
        if type(budgets) is not dict or set(budgets) != {
            'pieces_per_quarter', 'max_depth', 'max_boxes'
        }:
            raise ExactSerializationError('invalid replay engine budgets')
        engine = GeneralReachEngine(
            pieces_per_quarter=budgets['pieces_per_quarter'],
            max_depth=budgets['max_depth'],
            max_boxes=budgets['max_boxes'],
        )
        accepted = engine.replay(field, r0, proposal, case.get('proof_log'))
        if not accepted:
            error = 'proof log does not match reconstructed exact input'
    except (OSError, json.JSONDecodeError, ExactSerializationError, TypeError, ValueError) as exc:
        error = str(exc)
    output = {'accepted': accepted, 'error': error, 'replay_pid': os.getpid()}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
