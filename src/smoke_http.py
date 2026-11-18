"""Comprobacion HTTP contra el contenedor de staging."""
import json,sys,urllib.request,urllib.error
url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8080'
assert json.load(urllib.request.urlopen(url+'/health'))['status']=='ok'
data=json.dumps({'dti':.25,'utilization':.35,'prior_late':0,'monthly_income':2600}).encode()
r=json.load(urllib.request.urlopen(urllib.request.Request(url+'/score',data=data,headers={'Content-Type':'application/json'})))
assert 0<r['pd_12m']<1 and r['simulation'] is True
try:urllib.request.urlopen(urllib.request.Request(url+'/score',data=b'{}',headers={'Content-Type':'application/json'}))
except urllib.error.HTTPError as e:assert e.code==422
else:raise AssertionError('Entrada invalida aceptada')
print('HTTP health, scoring y rechazo de invalido: OK')
