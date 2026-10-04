# A6 mirrored spatial holdout

Chrono A6 is the same 1.625 kg action at `x=-50 mm`, accepted at 0.902 s
with 23.005060 mm loaded sinkage. The support mask and initial terrain match
A5 exactly. A5 versus mirrored A6 Chrono loaded maps differ by 2.181 mm RMSE,
so the oracle itself is not perfectly reflection-symmetric at the accepted
settling times.

Both Newton candidates are mechanics-valid with exact 0.902 s / 0.25 s
timing:

| candidate | objective | loaded RMSE | residual footprint RMSE |
|---|---:|---:|---:|
| frozen incumbent | 3.087760 mm | 1.119986 mm | 3.935548 mm |
| unchanged control | 4.072636 mm | 1.201066 mm | 5.743140 mm |

The incumbent wins the A6 scalar objective by 0.985 mm (24.2%) and also has
the lower residual-footprint error. Its predicted loaded depression centroid
is x=-50.954 mm versus Chrono x=-50.200 mm (−0.755 mm error); the control is
within −0.140 mm. This confirms that scalar and centroid fidelity can disagree
and that mirrored actions are necessary for spatial-transfer evaluation.
