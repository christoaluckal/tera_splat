# A6 mirrored spatial holdout

A6 evaluates the frozen 1.625 kg cylinder at `(x=-50 mm, y=0)` under the
same Chrono/Newton contract as A5. Chrono accepted `converged_speed_hold` at
0.902 s, with 23.005060 mm loaded sinkage and a 0.25 s residual phase. The
support mask and initial terrain are bitwise identical to A5.

Newton results:

| candidate | objective | loaded RMSE | residual-footprint RMSE |
|---|---:|---:|---:|
| frozen incumbent | 3.087760 mm | 1.119986 mm | 3.935548 mm |
| unchanged control | 4.072636 mm | 1.201066 mm | 5.743140 mm |

Both candidates passed the strict mechanics, zero-penetration, guide, timing,
and finite/full-support gates. The incumbent wins this mirrored scalar
holdout by 24.2%. Its loaded depression centroid is −50.954 mm versus the
Chrono value −50.200 mm; the control is −50.060 mm. A5 and A6 therefore show
that scalar surface error and spatial-characteristic error should be reported
separately.
