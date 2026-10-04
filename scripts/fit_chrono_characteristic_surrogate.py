#!/usr/bin/env python3
"""Fit a transparent action→Chrono-deformation characteristic surrogate.

This is intentionally a small synthetic-data baseline, not a replacement for
the Newton rollout or a real-sand calibration.  Each ``--episode`` is an
accepted Chrono episode directory.  A standardized ridge model maps mass,
radius, and action center to loaded/residual deformation characteristics, and
leave-one-out predictions are written for an honest coverage check.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np,yaml

CHAR_KEYS=('max_depression_mm','mean_depression_mm','footprint_max_depression_mm','footprint_mean_depression_mm','depression_volume_cm3','depression_centroid_x_mm','depression_centroid_y_mm')

def parse():
 p=argparse.ArgumentParser(); p.add_argument('--episode',action='append',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--ridge-alpha',type=float,default=1e-3); return p.parse_args()

def episode_features(ep):
 m=yaml.safe_load((ep/'manifest.yaml').read_text()); a=json.loads((ep/m['action']).read_text())
 if not m['chrono']['loading_convergence']['accepted']: raise ValueError(f'episode not accepted: {ep}')
 initial=np.load(ep/m['states']['initial']).astype(float); valid_path=str(m['heightmap']['valid_mask']).split(';',1)[0].strip(); valid=np.load(ep/valid_path).astype(bool)
 rows,cols=initial.shape; sp=float(m['heightmap']['spacing_m']); ox,oy=m['heightmap']['origin_xy_m']; x,y=np.meshgrid(ox+np.arange(cols)*sp,oy+np.arange(rows)*sp); cx,cy=a['center_xy_m']; fp=((x-cx)**2+(y-cy)**2<=float(a['radius_m'])**2)
 def stats(surface):
  d=surface-initial; s=valid&np.isfinite(d); z=np.maximum(-d,0.0); f=s&fp; w=z*f; den=float(w.sum()); return np.array([z[s].max()*1000,z[s].mean()*1000,z[f].max()*1000,z[f].mean()*1000,w.sum()*sp*sp*1e6,(x*w).sum()/den*1000 if den else 0,(y*w).sum()/den*1000 if den else 0],float)
 out=[]
 for state in ('loaded','residual'): out.extend(stats(np.load(ep/m['states'][state]).astype(float)))
 return np.array([a['mass_kg'],a['radius_m'],cx,cy],float),out,a['episode_id']

def design(x):
 # Transparent low-order terms; the sample set is too small for a high-order model.
 z=(x-x.mean(axis=0))/np.maximum(x.std(axis=0),1e-9); return np.column_stack([np.ones(len(z)),z])

def fit_predict(X,Y,alpha,holdout=None):
 train=np.ones(len(X),bool)
 if holdout is not None: train[holdout]=False
 A=design(X[train]); B=design(X if holdout is None else X[[holdout]])
 scale=np.maximum(np.std(Y[train],axis=0),1e-6); target=Y[train]/scale
 reg=np.eye(A.shape[1]); reg[0,0]=0; w=np.linalg.solve(A.T@A+alpha*reg,A.T@target); pred=(B@w)*scale
 return pred[0] if holdout is not None else pred

def main():
 a=parse(); records=[episode_features(p) for p in a.episode]; X=np.array([r[0] for r in records]); Y=np.array([r[1] for r in records]); names=[r[2] for r in records]; loo=[]
 for i,name in enumerate(names):
  pred=fit_predict(X,Y,a.ridge_alpha,holdout=i); err=pred-Y[i]; row={'episode_id':name}
  for j,k in enumerate(('loaded_'+q for q in CHAR_KEYS)): row[k+'_pred']=pred[j]; row[k+'_error']=err[j]
  for j,k in enumerate(('residual_'+q for q in CHAR_KEYS)): row[k+'_pred']=pred[7+j]; row[k+'_error']=err[7+j]
  loo.append(row)
 full=fit_predict(X,Y,a.ridge_alpha); a.output_dir.mkdir(parents=True,exist_ok=True); (a.output_dir/'training_summary.json').write_text(json.dumps({'episodes':names,'features':['mass_kg','radius_m','center_x_m','center_y_m'],'targets':list(('loaded_'+q for q in CHAR_KEYS))+list(('residual_'+q for q in CHAR_KEYS)),'ridge_alpha':a.ridge_alpha,'full_fit_characteristics':full.tolist()},indent=2)+'\n')
 with (a.output_dir/'leave_one_out.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(loo[0])); w.writeheader(); w.writerows(loo)
 print('wrote',len(records),'accepted Chrono episodes to',a.output_dir)
if __name__=='__main__': main()
