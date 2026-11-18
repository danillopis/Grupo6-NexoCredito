"""API de demostracion local. No autoriza operaciones financieras.
python src/api.py --port 8080
"""
import argparse,json,math
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import numpy as np
from experimento import predict
ROOT=Path(__file__).resolve().parents[1]

def score(payload,policy=None):
    if policy is None:policy=json.loads((ROOT/'config/politica.json').read_text())
    required={'dti','utilization','prior_late','monthly_income'}
    if set(payload)!=required:raise ValueError('Esquema: dti, utilization, prior_late, monthly_income')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in payload.values()):
        raise ValueError('Solo numeros finitos; sin booleanos ni nulos')
    d,u,l,inc=[float(payload[k]) for k in ['dti','utilization','prior_late','monthly_income']]
    if not (0<=d<=1 and 0<=u<=1 and l in (0,1) and 300<=inc<=100000):raise ValueError('Variable fuera de dominio')
    model=json.loads((ROOT/'modelos'/f"scoring-{policy['model_version']}.json").read_text())
    p=float(predict(model,np.array([[d,u,l,math.log(inc/2600)]]))[0])
    guard=policy.get('review_interaction',False) and d>.28 and u>.50
    decision='REVISION_MANUAL' if guard or p>policy['max_pd'] or d>policy['max_dti'] else 'PROPUESTA_FAVORABLE'
    return {'pd_12m':p,'decision':decision,'model_version':model['version'],
      'policy_version':policy['policy_version'],'simulation':True,
      'reasons':(['INTERACCION_EN_REVISION'] if guard else [])+
       (['PD_SOBRE_LIMITE'] if p>policy['max_pd'] else [])+
       (['ENDEUDAMIENTO_SOBRE_LIMITE'] if d>policy['max_dti'] else [])}

class Handler(BaseHTTPRequestHandler):
    def respond(self,status,payload):
        out=json.dumps(payload,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out)
    def do_GET(self):
        if self.path=='/health':self.respond(200,{'status':'ok','simulation':True})
        else:self.respond(404,{'error':'not_found'})
    def do_POST(self):
        if self.path!='/score':return self.respond(404,{'error':'not_found'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>4096:raise ValueError('Tamano de solicitud invalido')
            payload=json.loads(self.rfile.read(size));self.respond(200,score(payload))
        except (ValueError,TypeError,AttributeError) as e:self.respond(422,{'error':str(e)})
    def log_message(self,*args):pass

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8080)
    p.add_argument('--host',default='127.0.0.1');a=p.parse_args()
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
