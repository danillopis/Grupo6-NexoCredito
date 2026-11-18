"""Grupo 6. Experimento de credito/CRM completamente sintetico.
Python 3.11+ y numpy==2.3.5. Ejecutar: python src/experimento.py
Los resultados son una reproduccion historica, no una cartera ni una API bancaria.
"""
from pathlib import Path
import csv, hashlib, json, math, sqlite3, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SEED=6112026
BIN_EDGES=np.array([-np.inf,.025,.05,.075,.10,.15,.20,.30,.50,np.inf])

def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x,-35,35)))

def design(x, nonlinear=False):
    d,u,late,loginc=x.T
    out=[np.ones(len(x)),d,u,late,loginc]
    if nonlinear:
        out += [np.maximum(d-.28,0)*np.maximum(u-.5,0)*20]
    return np.column_stack(out)

def fit(x,y,nonlinear=False,weights=None):
    z=design(x,nonlinear);w=np.zeros(z.shape[1])
    sw=np.ones(len(y)) if weights is None else weights
    penalty=np.eye(z.shape[1])*.7;penalty[0,0]=0
    for _ in range(45):
        p=sigmoid(z@w)
        h=z.T@((sw*p*(1-p))[:,None]*z)+penalty
        g=z.T@(sw*(p-y))+penalty@w
        step=np.linalg.solve(h,g);w-=step
        if np.max(np.abs(step))<1e-9: break
    return {'coefficients':w.tolist(),'nonlinear':nonlinear,
            'features':['intercept','dti','utilization','prior_late','log_income']+
              (['interaction'] if nonlinear else []),
            'version':'1.1.0' if nonlinear else '1.0.0','seed':SEED}

def predict(model,x):
    return sigmoid(design(x,model['nonlinear'])@np.array(model['coefficients']))

def cohort(rng,name,n,phase='base'):
    d=rng.uniform(.03,.65,n);u=rng.uniform(.05,.95,n)
    if phase=='covariate':
        d=np.minimum(.75,d+.10);u=np.minimum(.99,u+.17)
    late=rng.binomial(1,.18,n);inc=rng.lognormal(np.log(2600),.35,n)
    x=np.column_stack([d,u,late,np.log(inc/2600)])
    interaction=np.maximum(d-.28,0)*np.maximum(u-.5,0)*20
    logits=-4.1+3*d+1.7*u+.9*late-.35*np.log(inc/2600)
    if phase=='concept':logits+=3.6*interaction
    p=sigmoid(logits);y=(rng.random(n)<p).astype(int)
    return {'name':name,'phase':phase,'x':x,'y':y,'p_true':p,
            'ead':rng.integers(2000,16001,n).astype(float),
            'channel':np.where(rng.random(n)<.65,'Digital','Oficina'),
            'segment':np.where(inc<2400,'Esencial','Vinculado')}

def auc(y,p):
    # Rango medio para empates; estable tambien con modelos discretos.
    order=np.argsort(p,kind='stable');values=p[order];ranks=np.empty(len(p))
    start=0
    while start<len(p):
        end=start+1
        while end<len(p) and values[end]==values[start]:end+=1
        ranks[order[start:end]]=(start+1+end)/2;start=end
    n1=int(sum(y));n0=len(y)-n1
    return float((ranks[y==1].sum()-n1*(n1+1)/2)/(n1*n0)) if n1*n0 else None

def psi(ref,current,edges=BIN_EDGES):
    a=np.histogram(ref,edges)[0]+.5;b=np.histogram(current,edges)[0]+.5
    a=a/a.sum();b=b/b.sum()
    return float(np.sum((b-a)*np.log(b/a)))

def metrics(y,p):
    s=np.argsort(-p,kind='stable');ys=y[s]
    ks=np.max(np.abs(np.cumsum(ys)/sum(ys)-np.cumsum(1-ys)/sum(1-ys)))
    bins=np.digitize(p,BIN_EDGES[1:-1]);ece=0
    for k in range(len(BIN_EDGES)-1):
        m=bins==k
        if sum(m):ece+=sum(m)/len(y)*abs(float(y[m].mean()-p[m].mean()))
    return {'n':len(y),'default_rate':float(y.mean()),'mean_pd':float(p.mean()),
      'auc':auc(y,p),'ks':float(ks),'brier':float(np.mean((p-y)**2)),
      'oe':float(y.mean()/p.mean()),'ece':float(ece)}

def policy(c,p,name='Vigente',tight=False,lgd=.45,spread=.08):
    d,u,_,_=c['x'].T
    approved=(p<=.12)&(d<=.40)
    if tight:approved &= ~((d>.28)&(u>.50))
    ead=c['ead'];y=c['y'];el=ead*p*lgd
    # Margen neto de financiacion 8%, coste unitario 90 EUR por prestamo.
    # Horizonte simplificado de un ano, EAD constante: no es ECL NIIF9.
    revenue=ead*spread-90
    realized=revenue-y*ead*lgd
    aead=float(ead[approved].sum())
    return {'policy':name,'cohort':c['name'],'applications':len(p),
     'approved':int(sum(approved)),'approval_rate':float(approved.mean()),
     'approved_ead':aead,'expected_loss':float(el[approved].sum()),
     'realized_loss':float((y*ead*lgd)[approved].sum()),
     'bad_rate':float(y[approved].mean()) if sum(approved) else None,
     'expected_margin':float((revenue-el)[approved].sum()),
     'realized_margin':float(realized[approved].sum())},approved

def save_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run():
    for d in ['datos','resultados','modelos']: (ROOT/d).mkdir(exist_ok=True)
    rng=np.random.default_rng(SEED)
    train=cohort(rng,'2022',8000);val=cohort(rng,'2023H1',2500)
    test=cohort(rng,'2023H2',2500)
    history=[]
    for partition,c in [('train',train),('reference',val),('test_temporal',test)]:
        for j in range(len(c['y'])):
            history.append({'record_id':f"{c['name']}-{j}",'partition':partition,
              'cohort':c['name'],'dti':float(c['x'][j,0]),'utilization':float(c['x'][j,1]),
              'prior_late':int(c['x'][j,2]),'log_income':float(c['x'][j,3]),
              'default_12m':int(c['y'][j]),'ead':float(c['ead'][j])})
    save_csv(ROOT/'datos/historico.csv',history)
    live=[cohort(rng,f'2024-{m:02}',3000,
          'base' if m<=2 else 'covariate' if m==3 else 'concept') for m in range(1,7)]
    champion=fit(train['x'],train['y'])
    # Challenger usa abril etiquetado y una muestra historica. Mayo valida;
    # junio no participa en entrenamiento ni seleccion.
    recent=live[3]
    xx=np.vstack([train['x'],recent['x']]);yy=np.r_[train['y'],recent['y']]
    candidate=fit(xx,yy,True,np.r_[np.full(8000,.10),np.ones(3000)])
    for model in [champion,candidate]:
        (ROOT/'modelos'/f"scoring-{model['version']}.json").write_text(json.dumps(model,indent=2)+'\n')
    reference=predict(champion,val['x'])
    base=metrics(test['y'],predict(champion,test['x']))
    monitoring=[];policies=[];scoring=[];calibration=[];segments=[]
    for c in live:
        p=predict(champion,c['x']);pc=predict(candidate,c['x'])
        mt=metrics(c['y'],p);mt.update(cohort=c['name'],phase=c['phase'],
          psi_score=psi(reference,p),
          psi_dti=psi(val['x'][:,0],c['x'][:,0],np.r_[-np.inf,np.arange(.1,.7,.1),np.inf]),
          delta_brier=metrics(c['y'],p)['brier']-base['brier'])
        mt['alert']='ROJO' if mt['oe']>1.25 or mt['oe']<.8 or mt['ece']>.05 else 'AMBAR' if mt['psi_score']>=.10 or mt['delta_brier']>.02 else 'VERDE'
        monitoring.append(mt)
        for label,pred,tight in [('Vigente',p,False),('Contencion',p,True),('Candidato',pc,False)]:
            result,approved=policy(c,pred,label,tight);policies.append(result)
        for j in range(len(p)):
            scoring.append({'application_id':f"{c['name']}-{j:04}",
              'cohort':c['name'],'channel':c['channel'][j],'segment':c['segment'][j],
              'dti':round(float(c['x'][j,0]),6),'utilization':round(float(c['x'][j,1]),6),
              'prior_late':int(c['x'][j,2]),'log_income':round(float(c['x'][j,3]),6),
              'ead':float(c['ead'][j]),'default_12m':int(c['y'][j]),
              'pd_champion':float(p[j]),'pd_candidate':float(pc[j]),
              'approved':int(p[j]<=.12 and c['x'][j,0]<=.40)})
        for model,pred in [('Vigente',p),('Candidato',pc)]:
            groups=[('segment',v,c['segment']==v) for v in ['Esencial','Vinculado']]
            groups += [('channel',v,c['channel']==v) for v in ['Digital','Oficina']]
            for kind,value,mask in groups:
                item=metrics(c['y'][mask],pred[mask])
                item.update(cohort=c['name'],model=model,group_kind=kind,group_value=value)
                segments.append(item)
            bins=np.digitize(pred,BIN_EDGES[1:-1])
            for k in range(len(BIN_EDGES)-1):
                mask=bins==k
                if sum(mask):calibration.append({'cohort':c['name'],'model':model,'bin':k,
                   'n':int(sum(mask)),'mean_pd':float(pred[mask].mean()),'observed':float(c['y'][mask].mean())})
    held=live[-1]
    comp={m:metrics(held['y'],predict(mod,held['x'])) for m,mod in [('Vigente',champion),('Candidato',candidate)]}
    # Bootstrap pareado de la mejora probabilistica, manteniendo la misma cohorte.
    pp=predict(champion,held['x']);cc=predict(candidate,held['x'])
    differences=(cc-held['y'])**2-(pp-held['y'])**2
    brng=np.random.default_rng(SEED+1)
    boot=[float(differences[brng.integers(0,len(differences),len(differences))].mean()) for _ in range(500)]
    ci=np.quantile(boot,[.025,.975]).tolist()
    valid={m:metrics(live[4]['y'],predict(mod,live[4]['x'])) for m,mod in [('Vigente',champion),('Candidato',candidate)]}
    portfolio=[];crm=[];api=[]
    # Cartera stock separada del target de impago acumulado a 12 meses.
    for c in live:
        p=predict(champion,c['x']);_,approved=policy(c,p)
        for j in np.flatnonzero(approved):
            bad=bool(c['y'][j]);dpd=int(rng.choice([0,30,100,120],p=[.10,.20,.35,.35])) if bad else int(rng.choice([0,15,35],p=[.95,.04,.01]))
            utp=int(bad and dpd<=90 and rng.random()<.5)
            bal=float(c['ead'][j]*rng.uniform(.4,1))
            portfolio.append({'loan_id':f"P-{c['name']}-{j}",'cohort':c['name'],'stock_as_of':'2025-06-30',
              'channel':c['channel'][j],'segment':c['segment'][j],'balance':bal,
              'dpd':dpd,'utp':utp,'npl_balance':bal if dpd>90 or utp else 0.0})
        for seg in ['Esencial','Vinculado']:
            for ch in ['Digital','Oficina']:
                active=1000 if seg=='Esencial' else 700
                contacted=320 if ch=='Digital' else 180
                churn=int(active*(.045 if seg=='Esencial' else .025)+(8 if c['phase']=='concept' else 0))
                crm.append({'cohort':c['name'],'segment':seg,'channel':ch,
                 'active_start':active,'churned':churn,'contacted':contacted,
                 'conversions':int(contacted*(.18 if seg=='Esencial' else .27)),
                 'campaign_cost':contacted*(2.0 if ch=='Digital' else 4.5),
                 'tickets':100,'resolved_sla':92 if c['phase']=='concept' else 97,
                 'trained':18,'staff':20})
        api.append({'cohort':c['name'],'requests':100000,'success':99930,
                    'p95_ms':130 if c['phase']!='concept' else 180,
                    'p99_ms':260,'availability':.9993,'freshness_minutes':10})
    save_csv(ROOT/'datos/scoring.csv',scoring)
    save_csv(ROOT/'datos/cartera.csv',portfolio)
    save_csv(ROOT/'datos/crm.csv',crm);save_csv(ROOT/'datos/api.csv',api)
    save_csv(ROOT/'datos/cohortes.csv',[{'cohort':c['name'],'order':i+1,'phase':c['phase']} for i,c in enumerate(live)])
    save_csv(ROOT/'resultados/monitorizacion.csv',monitoring)
    save_csv(ROOT/'resultados/politicas.csv',policies)
    save_csv(ROOT/'resultados/calibracion.csv',calibration)
    save_csv(ROOT/'resultados/segmentos.csv',segments)
    sensitivity=[]
    for lgd in [.25,.45,.65]:
        for spread in [.04,.08,.12]:
            for name,model,tight in [('Vigente',champion,False),('Contencion',champion,True),('Candidato',candidate,False)]:
                row,_=policy(held,predict(model,held['x']),name,tight,lgd,spread)
                row.update(lgd=lgd,spread=spread);sensitivity.append(row)
    save_csv(ROOT/'resultados/sensibilidad.csv',sensitivity)
    ead=sum(x['balance'] for x in portfolio);npl=sum(x['npl_balance'] for x in portfolio)
    validation_policy=[p for p in policies if p['cohort']=='2024-05']
    vp={p['policy']:p for p in validation_policy}
    candidate_pass=(valid['Candidato']['brier']<valid['Vigente']['brier']-.01
      and .8<=valid['Candidato']['oe']<=1.25 and valid['Candidato']['ece']<=.05
      and vp['Candidato']['bad_rate']<=.06
      and vp['Candidato']['realized_margin']>=.90*vp['Vigente']['realized_margin'])
    result={'seed':SEED,'as_of':'2026-11-18','sintetico':True,'base':base,
       'validation_may':valid,'holdout_june':comp,'candidate_validation_pass':candidate_pass,
       'bootstrap_delta_brier':{'replicates':500,'mean_difference':float(differences.mean()),'ci95':ci},
       'monitoring':monitoring,'policies':policies,
       'stock_npl':npl/ead,'stock_balance':ead,'stock_npl_balance':npl,
       'churn':sum(r['churned'] for r in crm)/sum(r['active_start'] for r in crm),
       'total_scoring':len(scoring),'total_training':len(train['y']),
       'numpy_version':np.__version__}
    (ROOT/'resultados/resumen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    # DW local inspeccionable, con granos separados para evitar fan-out.
    dbpath=ROOT/'datos/warehouse.sqlite'
    if dbpath.exists():dbpath.unlink()
    db=sqlite3.connect(dbpath)
    for name,rows in [('Scoring',scoring),('Cartera',portfolio),('CRM',crm),('API',api),('Monitor',monitoring),('Politicas',policies)]:
        keys=list(rows[0]);defs=','.join('"'+k+'" '+('REAL' if isinstance(rows[0][k],(int,float)) else 'TEXT') for k in keys)
        db.execute(f'CREATE TABLE {name} ({defs})')
        db.executemany(f'INSERT INTO {name} VALUES ({",".join("?" for _ in keys)})',[tuple(r[k] for k in keys) for r in rows])
    db.commit();db.close()
    print(json.dumps({'base':base,'monitoring':monitoring,'holdout':comp,
                      'candidate_validation_pass':candidate_pass,'NPL_stock':npl/ead},indent=2))
    return result

if __name__=='__main__':run()
