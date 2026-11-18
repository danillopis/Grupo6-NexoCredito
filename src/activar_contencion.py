"""Hotfix local de politica: no modifica el modelo. Reversible con --restaurar."""
import argparse,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--restaurar',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];f=root/'config/politica.json';policy=json.loads(f.read_text())
policy['review_interaction']=not a.restaurar
policy['policy_version']='1.0.0' if a.restaurar else '1.0.1'
temporary=f.with_suffix('.tmp')
temporary.write_text(json.dumps(policy,indent=2)+'\n')
os.replace(temporary,f)
print('Politica restaurada' if a.restaurar else 'Contencion activa; zona afectada a revision manual')
