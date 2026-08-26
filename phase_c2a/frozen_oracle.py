from __future__ import annotations
from pathlib import Path
import hashlib
import sys
import types
import zipfile

OUTER_FILENAME='Phase_C1_Exact_Input_Soundness_Repair_Bundle_20260823.zip'
INNER_FILENAME='phase_c_reach_engine_prototype.zip'
OUTER_SHA256='0edae927f9cd75b5140ced9e925b70da0cbaa785f6cfe077789e046b0e368ee0'
INNER_SHA256='94903d2a45f08e14cd153782e949c1301dbc8e67c863c25cce958ee1581aa6fe'

class FrozenArtifactError(RuntimeError):
    pass

def resolve_frozen_artifacts(root:Path|None=None):
    root=Path(__file__).resolve().parent.parent if root is None else Path(root).resolve()
    frozen_dir=root/'frozen_phase_c1'
    resolved={}
    for label,filename,expected in (
        ('outer',OUTER_FILENAME,OUTER_SHA256),
        ('inner',INNER_FILENAME,INNER_SHA256),
    ):
        path=frozen_dir/filename
        if not path.is_file():
            raise FrozenArtifactError(f'missing frozen Phase C.1 artifact: {filename}')
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected:
            raise FrozenArtifactError(
                f'frozen Phase C.1 artifact hash mismatch: {filename}'
            )
        resolved[f'{label}_sha256']=actual
    return resolved

def load_frozen_module(root:Path|None=None):
    here=Path(__file__).resolve().parent.parent if root is None else Path(root).resolve()
    resolve_frozen_artifacts(here)
    archive_path=here/'frozen_phase_c1'/INNER_FILENAME
    try:
        with zipfile.ZipFile(archive_path) as archive:
            source=archive.read('reach_engine.py')
    except (OSError,KeyError,zipfile.BadZipFile) as e:
        raise FrozenArtifactError('cannot load verified Phase C.1 oracle') from e
    name='phase_c1_frozen_reach_engine'
    filename=f'{archive_path}!/reach_engine.py'
    mod=types.ModuleType(name); mod.__file__=filename; sys.modules[name]=mod
    exec(compile(source,filename,'exec'),mod.__dict__)
    return mod
