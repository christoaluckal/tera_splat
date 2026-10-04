#!/usr/bin/env python3
"""Aggregate Chrono deformation characteristics against valid Newton outputs."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np,yaml

def parse():
 p=argparse.ArgumentParser(); p.add_argument('--case',action='append',required=True); p.add_argument('--output-dir',type=Path,required=True); return p.parse_args()
def result(root):
 found=[]
 for p in root.glob('study_*/trials/iteration_*/result.json'):
  try:d=json.loads(p.read_text())
  except (OSError,json.JSONDecodeError):continue
  if d.get('valid'):found.append((p.stat().st_mtime_ns,d,p))
 if not found:raise FileNotFoundError(root)
 _,d,p=max(found); r=Path(d['paths']['response']); return d,r if r.is_dir() else p.parent/'response'
def setup(ep):
 m=yaml.safe_load((ep/'manifest.yaml').read_text()); a=json.loads((ep/m['action']).read_text())
 rows,cols=m['heightmap']['shape']; sp=float(m['heightmap']['spacing_m']); ox,oy=m['heightmap']['origin_xy_m']
 x,y=np.meshgrid(ox+np.arange(cols)*sp,oy+np.arange(rows)*sp); cx,cy=a['center_xy_m']; fp=(x-cx)**2+(y-cy)**2<=float(a['radius_m'])**2
 mask=str(m['heightmap']['valid_mask']).split(';',1)[0].strip(); valid=np.load(ep/mask).astype(bool)
 return m,valid,x,y,fp,sp
def stats(d,v,x,y,fp,sp):
 s=v&np.isfinite(d); z=np.maximum(-d,0.0); f=s&fp; w=z*f; den=float(w.sum())
 return {'max_depression_mm':float(z[s].max()*1000),'mean_depression_mm':float(z[s].mean()*1000),'footprint_max_depression_mm':float(z[f].max()*1000),'footprint_mean_depression_mm':float(z[f].mean()*1000),'depression_volume_cm3':float(w.sum()*sp*sp*1e6),'depression_centroid_x_mm':float((x*w).sum()/den*1000) if den else float('nan'),'depression_centroid_y_mm':float((y*w).sum()/den*1000) if den else float('nan')}
def case(label,ep,root):
 m,v,x,y,fp,sp=setup(ep); r,response=result(root); h0=np.load(ep/m['states']['initial']).astype(float); n0=np.load(response/'initial_heightmap_m.npy').astype(float)
 out={'label':label,'chrono_episode':str(ep),'newton_response':str(response),'candidate':r['candidate'],'objective_mm':r['objective_m']*1000,'loaded_rmse_mm':r['loaded_rmse_m']*1000,'residual_footprint_rmse_mm':r['residual_footprint_rmse_m']*1000}
 for s in ('loaded','residual'):
  c=stats(np.load(ep/m['states'][s]).astype(float)-h0,v,x,y,fp,sp); n=stats(np.load(response/(s+'_heightmap_m.npy')).astype(float)-n0,v,x,y,fp,sp); out[s]={'chrono':c,'newton':n,'error':{k:n[k]-c[k] for k in c}}
 return out
def main():
 a=parse(); a.output_dir.mkdir(parents=True,exist_ok=True); rec=[]
 for spec in a.case:
  label,paths=spec.split('=',1); ep,root=paths.split(':',1); rec.append(case(label,Path(ep),Path(root)))
 (a.output_dir/'summary.json').write_text(json.dumps(rec,indent=2,allow_nan=True)+'\n'); rows=[]
 for r in rec:
  for s in ('loaded','residual'):
   row={'label':r['label'],'state':s,'objective_mm':r['objective_mm'],'loaded_rmse_mm':r['loaded_rmse_mm'],'residual_footprint_rmse_mm':r['residual_footprint_rmse_mm']}
   row.update({'chrono_'+k:v for k,v in r[s]['chrono'].items()}); row.update({'newton_'+k:v for k,v in r[s]['newton'].items()}); row.update({'error_'+k:v for k,v in r[s]['error'].items()}); rows.append(row)
 with (a.output_dir/'characteristics.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print(f'wrote {len(rec)} cases to {a.output_dir}')
if __name__=='__main__':main()
