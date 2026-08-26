from __future__ import annotations
import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
viol=[]
for path in sorted((ROOT/'phase_c2a').glob('*.py')):
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,float): viol.append([str(path.relative_to(ROOT)),n.lineno,repr(n.value)])
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('float','complex'): viol.append([str(path.relative_to(ROOT)),n.lineno,n.func.id])
out={'status':'PASS' if not viol else 'FAIL','certificate_path_float_violations':viol}
(ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/'float_path_audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2)); raise SystemExit(0 if not viol else 1)
