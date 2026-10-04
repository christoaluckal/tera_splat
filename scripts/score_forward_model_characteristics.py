#!/usr/bin/env python3
"""Score an existing transfer audit with a multi-characteristic deformation loss."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def parse():
    p=argparse.ArgumentParser()
    p.add_argument('summary',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--surface-weight',type=float,default=1.0)
    p.add_argument('--volume-weight',type=float,default=0.25)
    p.add_argument('--peak-weight',type=float,default=0.25)
    p.add_argument('--centroid-weight',type=float,default=0.25)
    p.add_argument('--volume-scale-cm3',type=float,default=100.0)
    p.add_argument('--peak-scale-mm',type=float,default=10.0)
    p.add_argument('--centroid-scale-mm',type=float,default=5.0)
    return p.parse_args()

def main():
    a=parse(); data=json.loads(a.summary.read_text()); rows=[]
    for r in data:
        for state in ('loaded','residual'):
            e=r[state]['error']; surface=float(r['loaded_rmse_mm'] if state=='loaded' else r['residual_footprint_rmse_mm'])
            volume=abs(float(e['depression_volume_cm3']))/a.volume_scale_cm3
            peak=abs(float(e['max_depression_mm']))/a.peak_scale_mm
            centroid=(float(e['depression_centroid_x_mm'])**2+float(e['depression_centroid_y_mm'])**2)**0.5/a.centroid_scale_mm
            score=a.surface_weight*surface+a.volume_weight*volume+a.peak_weight*peak+a.centroid_weight*centroid
            rows.append({'label':r['label'],'state':state,'surface_term':surface,'volume_term':volume,'peak_term':peak,'centroid_term':centroid,'multicharacteristic_score':score})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} scores to {a.output}')
if __name__=='__main__':main()
