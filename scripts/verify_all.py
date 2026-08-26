from __future__ import annotations
import json,subprocess,sys,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT); sys.path.insert(0,str(ROOT))
LOGS=ROOT/'logs'; RESULTS=ROOT/'results'; LOGS.mkdir(exist_ok=True); RESULTS.mkdir(exist_ok=True)
commands=[
 ('py_compile',[sys.executable,'-m','compileall','-q','phase_c2a','tests','scripts']),
 ('pytest',[sys.executable,'-m','pytest','-q']),
 ('property_suite',[sys.executable,'scripts/run_property_suite.py']),
 ('general_suite',[sys.executable,'scripts/run_general_suite.py']),
 ('invalid_suite',[sys.executable,'scripts/run_invalid_suite.py']),
 ('proof_replay',[sys.executable,'scripts/run_proof_replay.py']),
 ('float_path_audit',[sys.executable,'scripts/run_float_path_audit.py']),
]
summary={'commands':{},'all_passed':True,'field_only_loop_discovery':'NOT_IMPLEMENTED; candidate-free calls return UNKNOWN'}
for name,cmd in commands:
    t=time.perf_counter(); p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); dt=time.perf_counter()-t
    (LOGS/f'VERIFY_{name.upper()}.txt').write_text(p.stdout+f'\nEXIT_CODE={p.returncode}\n',encoding='utf-8')
    summary['commands'][name]={'exit_code':p.returncode,'runtime_seconds':dt,'command':cmd}; summary['all_passed'] &= p.returncode==0
# Enforce semantic gates from generated results.
try:
    gs=json.loads((RESULTS/'general_suite.json').read_text())
    semantic=(gs['circle_scenarios']==22 and gs['circle_failures']==0 and gs['circle_false_valid']==0 and gs['circle_valid']>0 and gs['knot_scenarios']==9 and gs['knot_failures']==0)
except Exception as e:
    semantic=False; gs={'error':repr(e)}
summary['general_semantic_gate']=semantic; summary['general_counts']={k:gs.get(k) for k in ('circle_scenarios','circle_valid','circle_false_valid','circle_failures','knot_scenarios','knot_valid','knot_failures')}
summary['all_passed'] &= semantic
(RESULTS/'verification_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
code=0 if summary['all_passed'] else 1
(RESULTS/'VERIFY_ALL_EXIT_CODE.txt').write_text(str(code)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2,sort_keys=True)); raise SystemExit(code)
