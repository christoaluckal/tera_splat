#!/usr/bin/env python3
"""Predict deformation characteristics from accepted Chrono episode GT data."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from .fit_chrono_characteristic_surrogate_v2 import KEYS,read,pred

def main():
 p=argparse.ArgumentParser(); p.add_argument('--episode',action='append',type=Path,required=True); p.add_argument('--mass-kg',type=float,required=True); p.add_argument('--radius-m',type=float,required=True); p.add_argument('--center-x-m',type=float,required=True); p.add_argument('--center-y-m',type=float,required=True); p.add_argument('--ridge-alpha',type=float,default=1e-3); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
 rec=[read(e) for e in a.episode]; X=np.array([r[0] for r in rec]); Y=np.array([r[1] for r in rec]); query=np.array([[a.mass_kg,a.radius_m,a.center_x_m,a.center_y_m]],float); y=pred(X,Y,query,a.ridge_alpha)[0]
 bounds=np.column_stack([X.min(0),X.max(0)]); inside=bool(np.all((query[0]>=bounds[:,0])&(query[0]<=bounds[:,1]))); out={'query':{'mass_kg':a.mass_kg,'radius_m':a.radius_m,'center_x_m':a.center_x_m,'center_y_m':a.center_y_m},'training_episode_count':len(rec),'in_training_bounds':inside,'training_bounds':{'mass_kg':bounds[0].tolist(),'radius_m':bounds[1].tolist(),'center_x_m':bounds[2].tolist(),'center_y_m':bounds[3].tolist()},'warning':None if inside else 'query extrapolates beyond at least one accepted Chrono feature bound','loaded':dict(zip(KEYS,map(float,y[:7]))),'residual':dict(zip(KEYS,map(float,y[7:])))}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2)+'\n'); print(a.output)
if __name__=='__main__':main()
