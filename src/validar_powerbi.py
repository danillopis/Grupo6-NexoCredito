"""Valida PBIR con JSON Schema oficial almacenado, sin acceso de red.
Requiere jsonschema==4.25.1. No sustituye abrir/renderizar en Desktop Windows.
"""
import json
from pathlib import Path
from jsonschema import Draft7Validator
from referencing import Registry,Resource
ROOT=Path(__file__).resolve().parents[1]

def run():
    cache=ROOT/'validacion/esquemas';idx=json.loads((cache/'index.json').read_text())
    store={u:json.loads((cache/f).read_text()) for u,f in idx.items()}
    registry=Registry().with_resources((u,Resource.from_contents(d)) for u,d in store.items())
    count=0
    for p in sorted((ROOT/'powerbi').rglob('*')):
        if not p.is_file() or p.suffix not in ['.json','.pbir']:continue
        d=json.loads(p.read_text());u=d.get('$schema')
        if not u:continue
        schema=store[u]
        errors=list(Draft7Validator(schema,registry=registry).iter_errors(d))
        if errors:raise ValueError(str(p)+': '+str(errors[0]))
        count+=1
    model=json.loads((ROOT/'powerbi/NexoCredito.SemanticModel/model.bim').read_text())['model']
    tables={t['name']:t for t in model['tables']}
    for rel in model['relationships']:
        for end in ['from','to']:
            t=rel[end+'Table'];col=rel[end+'Column']
            assert t in tables and col in {x['name'] for x in tables[t]['columns']}
    for p in (ROOT/'powerbi').rglob('visual.json'):
        v=json.loads(p.read_text())
        for state in v['visual']['query']['queryState'].values():
            for proj in state['projections']:
                kind=next(iter(proj['field']));spec=proj['field'][kind]
                table=spec['Expression']['SourceRef']['Entity'];column=spec['Property']
                pool=tables[table]['measures' if kind=='Measure' else 'columns']
                assert column in {x['name'] for x in pool},(p,table,column)
    result={'archivos_esquema_validos':count,'tablas':len(tables),
       'relaciones':len(model['relationships']),
       'visuales':len(list((ROOT/'powerbi').rglob('visual.json'))),
       'renderizado_desktop_windows':'pendiente'}
    (ROOT/'resultados/validacion_powerbi.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':run()
