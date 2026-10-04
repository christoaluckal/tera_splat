# A5 Newton results

Both A5 candidates used exact Chrono timing (0.816 s loaded, 0.25 s
residual), the fixed 0.25 ms Newton step, 8 proxy iterations, and 16 rigid
substeps. Both passed mechanics qualification, zero center-penetration, and
the guide gate.

| candidate | objective | loaded RMSE | residual footprint RMSE |
|---|---:|---:|---:|
| frozen incumbent (`log10(E)=4.847943757`, `nu=.237231507`, `mu=.305497980`) | 3.379302 mm | 1.223777 mm | 4.311049 mm |
| unchanged control (`log10(E)=5`, `nu=.2`, `mu=.68`) | 3.272178 mm | 0.960535 mm | 4.623285 mm |

The control is 0.107124 mm (3.18%) better on the scalar objective, while the
incumbent is 0.312237 mm better on residual-footprint RMSE. This supports
admissible spatial transfer but not a universal incumbent advantage at every
action location.
