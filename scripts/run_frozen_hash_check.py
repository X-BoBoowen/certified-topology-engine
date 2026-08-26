from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from phase_c2a.frozen_oracle import FrozenArtifactError, resolve_frozen_artifacts


def main():
    results_dir = ROOT / 'results'
    results_dir.mkdir(exist_ok=True)
    try:
        output = {'status': 'PASS', **resolve_frozen_artifacts(ROOT)}
        exit_code = 0
    except FrozenArtifactError as exc:
        output = {'status': 'FAIL', 'error': str(exc)}
        exit_code = 1
    (results_dir / 'frozen_artifacts.json').write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding='utf-8'
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
