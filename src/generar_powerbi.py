"""Genera PBIP/PBIR publico, modelo TMSL y datos M integrados.
Los CSV se incorporan al modelo; no hace falta cambiar rutas en Power BI.
Despues de abrir NexoCredito.pbip en Desktop Windows, pulsar Actualizar.
"""
from pathlib import Path
import csv,json,uuid
ROOT=Path(__file__).resolve().parents[1]
BI=ROOT/'powerbi'
SC='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def native_table(name,path):
    with path.open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    cols=list(rows[0]);numeric={}
    for k in cols:
        try:
            [float(r[k]) for r in rows];numeric[k]=True
        except ValueError:numeric[k]=False
    tablecols=[{'name':k,'dataType':'double' if numeric[k] else 'string',
                'sourceColumn':k,'summarizeBy':'none'} for k in cols]
    definitions=', '.join('#"'+k+'" = '+('number' if numeric[k] else 'text') for k in cols)
    def lit(k,v):return str(float(v)) if numeric[k] else '"'+v.replace('"','""')+'"'
    literals=',\n'.join('{'+', '.join(lit(k,r[k]) for k in cols)+'}' for r in rows)
    expr='let\n Source = #table(type table ['+definitions+'], {\n'+literals+'\n})\nin Source'
    return {'name':name,'columns':tablecols,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}

def measure(table,name,expr,fmt='0.00%'):
    table.setdefault('measures',[]).append({'name':name,'expression':expr,'formatString':fmt,
       'displayFolder':'Grupo 6'})

def field(table,column,is_measure=False):
    kind='Measure' if is_measure else 'Column'
    return {'field':{kind:{'Expression':{'SourceRef':{'Entity':table}},'Property':column}},
            'queryRef':table+'.'+column,'nativeQueryRef':column}

def visual(page,name,typ,x,y,w,h,roles,title):
    v={'$schema':SC+'visualContainer/2.1.0/schema.json','name':name,
       'position':{'x':x,'y':y,'z':1,'width':w,'height':h,'tabOrder':1},
       'visual':{'visualType':typ,'query':{'queryState':{
           r:{'projections':ps} for r,ps in roles.items()}},
         'visualContainerObjects':{'title':[{'properties':{
             'show':{'expr':{'Literal':{'Value':'true'}}},
             'text':{'expr':{'Literal':{'Value':"'"+title.replace("'","''")+"'"}}},
             'fontSize':{'expr':{'Literal':{'Value':'12D'}}}}}]}}}
    write(BI/'NexoCredito.Report/definition/pages'/page/'visuals'/name/'visual.json',v)

def run():
    modeldir=BI/'NexoCredito.SemanticModel';report=BI/'NexoCredito.Report'
    for filename,col,values in [('canales.csv','channel',['Digital','Oficina']),('segmentos.csv','segment',['Esencial','Vinculado'])]:
        with (ROOT/'datos'/filename).open('w',newline='') as f:
            w=csv.writer(f);w.writerow([col]);w.writerows([[v] for v in values])
    mappings={'Canales':'datos/canales.csv','Segmentos':'datos/segmentos.csv','Cohortes':'datos/cohortes.csv','Scoring':'datos/scoring.csv',
      'Cartera':'datos/cartera.csv','CRM':'datos/crm.csv','API':'datos/api.csv',
      'Monitor':'resultados/monitorizacion.csv','Politicas':'resultados/politicas.csv'}
    tables=[native_table(k,ROOT/v) for k,v in mappings.items()]
    by={t['name']:t for t in tables}
    measures=[('Cartera','NPL cartera','DIVIDE(SUM(Cartera[npl_balance]),SUM(Cartera[balance]))','0.00%'),
      ('Cartera','Saldo vivo','SUM(Cartera[balance])','#,0 €'),
      ('Scoring','Solicitudes','COUNTROWS(Scoring)','#,0'),
      ('Scoring','Tasa aprobacion','AVERAGE(Scoring[approved])','0.00%'),
      ('CRM','Churn mensual medio','DIVIDE(SUM(CRM[churned]),SUM(CRM[active_start]))','0.00%'),
      ('CRM','Conversion','DIVIDE(SUM(CRM[conversions]),SUM(CRM[contacted]))','0.00%'),
      ('CRM','Resolucion SLA','DIVIDE(SUM(CRM[resolved_sla]),SUM(CRM[tickets]))','0.00%'),
      ('CRM','Cobertura formacion','DIVIDE(SUM(CRM[trained]),SUM(CRM[staff]))','0.00%'),
      ('CRM','Coste adquisicion','DIVIDE(SUM(CRM[campaign_cost]),SUM(CRM[conversions]))','0.00 €'),
      ('API','Exito API','DIVIDE(SUM(API[success]),SUM(API[requests]))','0.00%'),
      ('API','P95 escenario','MAX(API[p95_ms])','0 ms'),
      ('Monitor','PSI score','AVERAGE(Monitor[psi_score])','0.000'),
      ('Monitor','O E','AVERAGE(Monitor[oe])','0.00'),
      ('Monitor','AUC','AVERAGE(Monitor[auc])','0.000'),
      ('Monitor','Brier','AVERAGE(Monitor[brier])','0.000'),
      ('Monitor','ECE','AVERAGE(Monitor[ece])','0.000'),
      ('Politicas','Margen realizado','SUM(Politicas[realized_margin])','#,0 €'),
      ('Politicas','Perdida realizada','SUM(Politicas[realized_loss])','#,0 €'),
      ('Politicas','Aprobacion politica','DIVIDE(SUM(Politicas[approved]),SUM(Politicas[applications]))','0.00%')]
    for t,n,e,f in measures:measure(by[t],n,e,f)
    relationships=[{'name':str(uuid.uuid5(uuid.NAMESPACE_URL,'Grupo6-'+t)),
        'fromTable':t,'fromColumn':'cohort','toTable':'Cohortes','toColumn':'cohort',
        'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'}
        for t in mappings if t not in ['Cohortes','Canales','Segmentos']]
    for dim,col in [('Canales','channel'),('Segmentos','segment')]:
        for fact in ['Scoring','Cartera','CRM']:
            relationships.append({'name':str(uuid.uuid5(uuid.NAMESPACE_URL,'Grupo6-'+dim+fact)),
              'fromTable':fact,'fromColumn':col,'toTable':dim,'toColumn':col,
              'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
    write(modeldir/'definition.pbism',{'version':'4.0','settings':{'qnaEnabled':False}})
    write(modeldir/'model.bim',{'name':'NexoCredito','compatibilityLevel':1600,
      'model':{'culture':'es-ES','defaultPowerBIDataSourceVersion':'powerBI_V3',
      'dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':False},
      'tables':tables,'relationships':relationships}})
    write(BI/'NexoCredito.pbip',{'version':'1.0','artifacts':[{'report':{'path':'NexoCredito.Report'}}],
      'settings':{'enableAutoRecovery':True}})
    write(report/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json',
      'version':'4.0','datasetReference':{'byPath':{'path':'../NexoCredito.SemanticModel'}}})
    write(report/'definition/version.json',{'$schema':SC+'versionMetadata/1.0.0/schema.json','version':'4.0.0'})
    write(report/'definition/report.json',{'$schema':SC+'report/2.0.0/schema.json','themeCollection':{}})
    pages=[('01_resumen','01 | Dirección'),('02_mlops','02 | MLOps y riesgo'),
           ('03_crm','03 | CRM y BSC'),('04_crisis','04 | Comparar políticas')]
    write(report/'definition/pages/pages.json',{'$schema':SC+'pagesMetadata/1.0.0/schema.json',
       'pageOrder':[p[0] for p in pages],'activePageName':pages[0][0]})
    for pn,label in pages:
        write(report/'definition/pages'/pn/'page.json',{'$schema':SC+'page/2.0.0/schema.json',
           'name':pn,'displayName':label,'displayOption':'FitToPage','width':1280,'height':720})
        visual(pn,'filtro_cohorte','slicer',1020,10,250,90,{'Values':[field('Cohortes','cohort')]},'Cohorte / mes')
    def card(p,n,t,m,x):visual(p,n,'card',x,110,300,115,{'Values':[field(t,m,True)]},m)
    def chart(p,n,typ,t,cat,ms,x,y,w=610,h=390):
        visual(p,n,typ,x,y,w,h,{'Category':[field(t,cat)],'Y':[field(a,b,True) for a,b in ms]},n.replace('_',' '))
    for i,(t,m) in enumerate([('Scoring','Solicitudes'),('Cartera','Saldo vivo'),('Cartera','NPL cartera'),('CRM','Churn mensual medio')]):card('01_resumen','card'+str(i),t,m,10+i*315)
    chart('01_resumen','NPL_por_cohorte_corte_junio_2025','lineChart','Cohortes','cohort',[('Cartera','NPL cartera')],10,250)
    chart('01_resumen','Churn_por_mes','lineChart','Cohortes','cohort',[('CRM','Churn mensual medio')],650,250)
    for i,(t,m) in enumerate([('Monitor','AUC'),('Monitor','Brier'),('Monitor','O E'),('Monitor','PSI score')]):card('02_mlops','card'+str(i),t,m,10+i*315)
    chart('02_mlops','PSI_no_detecta_toda_deriva','clusteredColumnChart','Cohortes','cohort',[('Monitor','PSI score')],10,250)
    chart('02_mlops','AUC_y_Brier_por_cohorte','lineChart','Cohortes','cohort',[('Monitor','AUC'),('Monitor','Brier')],650,250)
    for i,(t,m) in enumerate([('CRM','Conversion'),('CRM','Resolucion SLA'),('CRM','Coste adquisicion'),('CRM','Cobertura formacion')]):card('03_crm','card'+str(i),t,m,10+i*315)
    chart('03_crm','Conversion_por_segmento','clusteredColumnChart','CRM','segment',[('CRM','Conversion')],10,250)
    chart('03_crm','Churn_por_canal_principal','clusteredColumnChart','CRM','channel',[('CRM','Churn mensual medio')],650,250)
    chart('04_crisis','Margen_observado_por_politica','clusteredColumnChart','Politicas','policy',[('Politicas','Margen realizado')],10,140,610,440)
    chart('04_crisis','Perdida_observada_por_politica','clusteredColumnChart','Politicas','policy',[('Politicas','Perdida realizada')],650,140,610,440)
    # Tabla de coeficientes DAX portable, util para inspeccion y reconstruccion.
    (BI/'medidas.dax').write_text('\n\n'.join(f'{n} = {e}' for _,n,e,_ in measures)+'\n')
    print('Power BI: 4 paginas,',len(list(report.rglob('visual.json'))),'visuales, 9 tablas,',len(measures),'medidas DAX')

if __name__=='__main__':run()
