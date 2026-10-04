# Newton handoff addendum — A5 spatial transfer (2026-10-02)

This addendum supplements `newton-handoff.md` with the completed A5 spatial
holdout. The Chrono oracle used the frozen 1.625 kg guided cylinder at
`(x=+0.05 m, y=0.0 m)`; all geometry, soil, guide, grid, and numerical
settings were unchanged from the A0–A4 family.

Chrono accepted `converged_speed_hold` at 0.816 s, with 22.188591 mm loaded
sinkage and a 0.25 s residual phase. The support mask and initial terrain are
bitwise identical to A4; all maps are finite on the 14,161-cell support.

At exact timing, Newton used dt=0.25 ms, 8 proxy iterations, and 16 rigid
substeps. Both the frozen incumbent (`log10(E)=4.847943757`, `nu=.237231507`,
`mu=.305497980`) and unchanged control (`log10(E)=5`, `nu=.2`, `mu=.68`)
passed mechanics qualification, zero center-penetration, and the guide gate.

| candidate | objective | loaded RMSE | residual footprint RMSE |
|---|---:|---:|---:|
| frozen incumbent | 3.379302 mm | 1.223777 mm | 4.311049 mm |
| unchanged control | 3.272178 mm | 0.960535 mm | 4.623285 mm |

The control is 0.107124 mm (3.18%) better on the scalar objective, while the
incumbent is 0.312237 mm better on residual-footprint RMSE. A5 therefore
supports admissible spatial transfer, but not a universal incumbent advantage
at every action location.

Artifacts:

- Chrono: `tera_splat_sim/validity_experiment/chrono_episodes/A5_oracle_mass1p625kg_lateral_x50mm_gate6mm_v1`
- Newton incumbent: `outputs/validity_experiment/newton_holdout/mass1p625kg_lateral_x50mm_incumbent_timealigned_20261001`
- Newton control: `outputs/validity_experiment/newton_holdout/mass1p625kg_lateral_x50mm_baseline_timealigned_20261002`
- Diagnostic: `tera_splat/diagnostics/newton_lateral_x50mm_holdout_20261001/`
