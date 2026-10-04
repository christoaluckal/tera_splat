#!/usr/bin/env python3
"""Aggregate Chrono deformation characteristics against valid Newton outputs."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import yaml


def args():
    p = argparse.ArgumentParser()
    p.add_argument('--case', action='append', required=True,
                   help='label=chrono_episode:newton_output_root')
    p.add_argument('--output-dir', type=Path, required=True)
    return p.parse_args()


def result(root):
    found=[]
    for p in root.glob('study_*/trials/iteration_*/result.json'):
        try: d=json.loads(p.read_text())
        except (OSError,json.JSONDecodeError): continue
        if d.get('valid'): found.append((p.stat().st_mtime_ns,d,p))
    if not found: raise FileNotFoundError(root)
    _, d, p=max(found)
    response=Path(d['paths']['response'])
    if not response.is_dir(): response=p.parent/'response'
    return d,response


def geometry(ep):
    m=yaml.safe_load((ep/'manifest.yaml').read_text())
    a=json.loads((ep/m['action']).read_text())
    rows,cols=m['heightmap']['shape']; spacing=float(m['heightmap']['spacing_m'])
    ox,oy=m['heightmap']['origin_xy_m']
    x,y=np.meshgrid(ox+np.arange(cols)*spacing,oy+np.arange(rows)*spacing)
    fp=(x-a['center_xy_m'][0])**2+(y-a['center_xy_m'][1])**2<=float(a['radius_m'])**2
    valid=np.load(ep/m['heightmap']['valid_mask']).astype(bool)
    return m,valid,x,y,fp,spacing


def stats(delta,valid,x,y,fp,spacing):
    support=valid & np.isfinite(delta); dep=np.maximum(-delta,0.0); mask=support&fp
    w=dep*mask; denom=float(w.sum())
    return {'max_depression_mm':float(dep[support].max()*1000),
            'mean_depression_mm':float(dep[support].mean()*1000),
            'footprint_max_depression_mm':float(dep[mask].max()*1000),
            'footprint_mean_depression_mm':float(dep[mask].mean()*1000),
            'depression_volume_cm3':float(w.sum()*spacing*spacing*1e6),
            'depression_centroid_x_mm':float((x*w).sum()/denom*1000) if denom else float('nan'),
            'depression_centroid_y_mm':float((y*w).sum()/denom*1000) if denom else float('nan')}


def one(label,ep,root):
    m,valid,x,y,fp,spacing=geometry(ep); d,response=result(root)
    h0=np.load(ep/m['states']['initial']).astype(float)
    n0=np.load(response/'initial_heightmap_m.npy').astype(float)
    out={'label':label,'chrono_episode':str(ep),'newton_response':str(response),
         'candidate':d['candidate'],'objective_mm':d['objective_m']*1000,
         'loaded_rmse_mm':d['loaded_rmse_m']*1000,
         'residual_footprint_rmse_mm':d['residual_footprint_rmse_m']*1000}
    for state in ('loaded','residual'):
        c=np.load(ep/m['states'][state]).astype(float)-h0
        n=np.load(response/(state+'_heightmap_m.npy')).astype(float)-n0
        cs,ns=stats(c,valid,x,y,fp,spacing),stats(n,valid,x,y,fp,spacing)
        out[state]={'chrono':cs,'newton':ns,
                    'error':{k:ns[k]-cs[k] for k in cs}}
    return out


def main():
    a=args(); a.output_dir.mkdir(parents=True,exist_ok=True); records=[]
    for spec in a.case:
        label,paths=spec.split('=',1); ep,root=paths.split(':',1)
        records.append(one(label,Path(ep),Path(root)))
    (a.output_dir/'summary.json').write_text(json.dumps(records,indent=2,allow_nan=True)+'\n')
    rows=[]
    for r in records:
        for s in ('loaded','residual'):
            rows.append({'label':r['label'],'state':s,'objective_mm':r['objective_mm'],
              'loaded_rmse_mm':r['loaded_rmse_mm'],'residual_footprint_rmse_mm':r['residual_footprint_rmse_mm'],
              **{('chrono_'+k):v for k,v in r[s]['chrono'].items()},
              **{('newton_'+k):v for k,v in r[s]['newton'].items()},
              **{('error_'+k):v for k,v in r[s]['error'].items()}})
    with (a.output_dir/'characteristics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'wrote {len(records)} cases to {a.output_dir}')


if __name__=='__main__': main()
