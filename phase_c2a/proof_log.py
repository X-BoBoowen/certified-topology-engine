from __future__ import annotations
import json,hashlib

def canonical_json(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(obj): return hashlib.sha256(canonical_json(obj).encode()).hexdigest()
def seal(log):
    x=dict(log); x.pop('root_hash',None); x['root_hash']=digest(x); return x
def verify_seal(log):
    if type(log) is not dict or type(log.get('root_hash')) is not str: return False
    x=dict(log); claimed=x.pop('root_hash'); return claimed==digest(x)
