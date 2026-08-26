import subprocess,sys
from pathlib import Path

def test_runner_imports_from_clean_working_directory(tmp_path):
    root=Path(__file__).resolve().parents[1]
    p=subprocess.run([sys.executable,str(root/'scripts'/'run_invalid_suite.py')],cwd=tmp_path,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert p.returncode==0,p.stdout
