#!/usr/bin/env python3
"""Score every valid archived A0 Newton candidate on deformation characteristics."""
from __future__ import annotations
import argparse,csv,json,glob
from pathlib import Path
from .analyze_forward_model_transfer_v3 import setup,stats
import numpy as np,yaml

def main():
 p=argparse.ArgumentParser(); p.add_argument('--chrono-episode',type=Path,required=True); p.add_argument('--archive-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
 m,v,x,y,fp,sp=setup(a.chrono_episode); h0=np.load(a.chrono_episode/m['states']['initial']).astype(float)
 gt={s:stats(np.load(a.chrono_episode/m['states'][s]).astype(float)-h0,v,x,y,fp,sp) for s in ('loaded','residual')}; rows=[]
 for result_path in sorted(a.archive_root.glob('**/result.json')):
  try:r=json.loads(result_path.read_text())
  except (OSError,json.JSONDecodeError):continue
  if not r.get('valid'):continue
  response=Path(r['paths']['response']);
  if not response.is_dir(): response=result_path.parent/'response'
  try:n0=np.load(response/'initial_heightmap_m.npy').astype(float)
  except OSError:continue
  errors={}
  for s in ('loaded','residual'):
   n=stats(np.load(response/(s+'_heightmap_m.npy')).astype(float)-n0,v,x,y,fp,sp); errors[s]={k:n[k]-gt[s][k] for k in n}
  loaded=float(r['loaded_rmse_m'])*1000; residual=float(r['residual_footprint_rmse_m'])*1000
  volume=abs(errors['loaded']['depression_volume_cm3'])/100; peak=abs(errors['loaded']['max_depression_mm'])/10; cen=(errors['loaded']['depression_centroid_x_mm']**2+errors['loaded']['depression_centroid_y_mm']**2)**0.5/5
  rows.append({'result':str(result_path),'log10_e':r['candidate']['log10_e'],'nu':r['candidate']['nu'],'friction_coefficient':r['candidate']['friction_coefficient'],'objective_mm':r['objective_m']*1000,'loaded_rmse_mm':loaded,'residual_footprint_rmse_mm':residual,'volume_term':volume,'peak_term':peak,'centroid_term':cen,'multi_loss':loaded+0.5*residual+0.25*(volume+peak+cen)})
 if not rows: raise RuntimeError('no valid archived candidates with response maps')
 rows.sort(key=lambda z:z['multi_loss']); a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print('wrote',len(rows),'valid A0 candidates; best multi_loss=',rows[0]['multi_loss'])
if __name__=='__main__':main()
