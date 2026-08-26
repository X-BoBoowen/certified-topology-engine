from __future__ import annotations
from pathlib import Path
import importlib.util
import sys

def load_frozen_module():
    here=Path(__file__).resolve().parent.parent
    path=here/'frozen_phase_c1'/'reach_engine.py'
    spec=importlib.util.spec_from_file_location('phase_c1_frozen_reach_engine',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load frozen Phase C.1 oracle')
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    return mod
