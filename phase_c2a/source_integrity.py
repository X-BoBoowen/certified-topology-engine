from __future__ import annotations

import hashlib
import json
from pathlib import Path


CONTROLLED_ROOT_FILES = (
    'AGENTS.md',
    'BOUNDARY_ZERO_FREE_CERTIFICATE.md',
    'FROZEN_PHASE_C1_HASHES.txt',
    'GENERAL_FIELD_INPUT_CONTRACT.md',
    'KNOWN_LIMITATIONS.md',
    'PHASE_C2A_RESEARCH_STATUS.md',
    'PROOF_REPLAY.md',
    'PROPOSAL_ASSISTED_SCOPE.md',
    'README.md',
    'SCENARIO_TEST_MAPPING.md',
    'pyproject.toml',
    'requirements.txt',
)
CONTROLLED_FROZEN_FILES = (
    'frozen_phase_c1/Phase_C1_Exact_Input_Soundness_Repair_Bundle_20260823.zip',
    'frozen_phase_c1/phase_c_reach_engine_prototype.zip',
)
CONTROLLED_PATTERNS = (
    ('docs', '*.md'),
    ('phase_c2a', '*.py'),
    ('scripts', '*.py'),
    ('tests', '*.py'),
)


def controlled_source_paths(root):
    root = Path(root).resolve()
    paths = [root / relative for relative in CONTROLLED_ROOT_FILES]
    paths.extend(root / relative for relative in CONTROLLED_FROZEN_FILES)
    for directory, pattern in CONTROLLED_PATTERNS:
        paths.extend((root / directory).rglob(pattern))
    paths = sorted(
        set(paths), key=lambda path: path.relative_to(root).as_posix()
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError(
            f'missing controlled source file: {missing[0].relative_to(root).as_posix()}'
        )
    return paths


def controlled_source_records(root):
    root = Path(root).resolve()
    records = []
    for path in controlled_source_paths(root):
        content = path.read_bytes()
        records.append(
            {
                'path': path.relative_to(root).as_posix(),
                'sha256': hashlib.sha256(content).hexdigest(),
                'size': len(content),
            }
        )
    return records


def digest_source_records(records):
    encoded = json.dumps(
        records, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def controlled_source_snapshot(root):
    records = controlled_source_records(root)
    return {
        'schema': 'phase-c2b-controlled-source-v1',
        'sha256': digest_source_records(records),
        'file_count': len(records),
        'files': records,
    }
