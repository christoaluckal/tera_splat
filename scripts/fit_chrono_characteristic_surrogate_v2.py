#!/usr/bin/env python3
"""Leave-one-out ridge surrogate for accepted Chrono deformation characteristics."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np,yaml

KEYS=('max_depression_mm','mean_depression_mm','footprint_max_depression_mm','footprint_mean_depression_mm','depression_volume_cm3','depression_centroid_x_mm','depression_centroid_y_mm')
def parse():
 p=argparse.ArgumentParser(); p.add_argument('--episode',action='append',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--ridge-alpha',type=float,default=1e-3); return p.parse_args()
def read(ep):
 m=yaml.safe_load((ep/'manifest.yaml').read_text()); a=json.loads((ep/m['action']).read_text()); assert m['chrono']['loading_convergence']['accepted']
 h0=np.load(ep/m['states']['initial']).astype(float); mask=str(m['heightmap']['valid_mask']).split(';',1)[0].strip(); valid=np.load(ep/mask).astype(bool); rows,cols=h0.shape; sp=float(m['heightmap']['spacing_m']); ox,oy=m['heightmap']['origin_xy_m']; x,y=np.meshgrid(ox+np.arange(cols)*sp,oy+np.arange(rows)*sp); cx,cy=a['center_xy_m']; fp=(x-cx)**2+(y-cy)**2<=float(a['radius_m'])**2
 def one(s):
  d=np.load(ep/m['states'][s]).astype(float)-h0; good=valid&np.isfinite(d); dep=np.maximum(-d,0); f=good&fp; w=dep*f; den=float(w.sum()); return [dep[good].max()*1000,dep[good].mean()*1000,dep[f].max()*1000,dep[f].mean()*1000,w.sum()*sp*sp*1e6,(x*w).sum()/den*1000 if den else 0,(y*w).sum()/den*1000 if den else 0]
 return [a['mass_kg'],a['radius_m'],cx,cy],one('loaded')+one('residual'),a['episode_id']
def mat(x,mu=None,sd=None):
 if mu is None: mu=x.mean(0); sd=np.maximum(x.std(0),1e-9)
 z=(x-mu)/sd; return np.column_stack([np.ones(len(z)),z]),mu,sd
def pred(train_x,train_y,test_x,alpha):
 A,mu,sd=mat(train_x); B,_,_=mat(test_x,mu,sd); scale=np.maximum(train_y.std(0),1e-6); reg=np.eye(A.shape[1]); reg[0,0]=0; w=np.linalg.solve(A.T@A+alpha*reg,A.T@(train_y/scale)); return B@w*scale
def main():
 a=parse(); rec=[read(e) for e in a.episode]; X=np.array([r[0] for r in rec]); Y=np.array([r[1] for r in rec]); rows=[]
 for i,(_,_,name) in enumerate(rec):
  keep=np.arange(len(X))!=i; y=pred(X[keep],Y[keep],X[i:i+1],a.ridge_alpha)[0]; err=y-Y[i]; row={'episode_id':name}
  for j,k in enumerate(KEYS): row['loaded_'+k+'_pred']=y[j]; row['loaded_'+k+'_error']=err[j]; row['residual_'+k+'_pred']=y[7+j]; row['residual_'+k+'_error']=err[7+j]
  rows.append(row)
 full=pred(X,Y,X,a.ridge_alpha); a.output_dir.mkdir(parents=True,exist_ok=True); (a.output_dir/'training_summary.json').write_text(json.dumps({'episodes':[r[2] for r in rec],'features':['mass_kg','radius_m','center_x_m','center_y_m'],'ridge_alpha':a.ridge_alpha,'full_fit':full.tolist()},indent=2)+'\n')
 with (a.output_dir/'leave_one_out.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print('wrote',len(rows),'episodes')
if __name__=='__main__':main()
