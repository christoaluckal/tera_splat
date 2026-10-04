# Forward-model transfer audit (2026-10-02)

The Chrono→Newton evaluator in
`scripts/analyze_forward_model_transfer_v3.py` compares deformation
characteristics on every mechanics-valid completed holdout. Its output is in
`diagnostics/forward_model_transfer_20261002/`.

The audit includes A2 control (2.0 kg), A3 control (1.75 kg), A4 incumbent and
control (1.625 kg at y=+5 mm), and A5 incumbent and control (1.625 kg at
x=+50 mm). The invalid A2 incumbent is excluded by contract.

The scalar objective is not sufficient as a forward-model criterion. Across
the guided mass controls, Newton underpredicts Chrono depression volume by
about 260–308 cm³ and maximum depression by 18–21 mm. The frozen incumbent
has lower A4 scalar error than the control but overpredicts A4/A5 local
maximum depression; at A5 it also shifts the depression centroid by about
1.15 mm in x. Thus the current result is an admissible, useful deformation
surrogate, not yet a characteristic-faithful Chrono predictor.

Next evidence should use a multi-characteristic loss (surface RMSE plus
volume, peak, footprint, and centroid terms) on a fresh action, while
retaining the strict mechanics and timing gates. Do not treat the aggregate
diagnostic as additional BayesOpt observations.
