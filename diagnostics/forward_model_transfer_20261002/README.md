# Chrono→Newton forward-model transfer audit — 2026-10-02

This audit aggregates mechanics-valid held-out responses using
`scripts/analyze_forward_model_transfer_v3.py`. Chrono supplies the target
initial/loaded/residual heightfields; Newton supplies the prediction. The
evaluator reports map RMSE already produced by the runner plus deformation
characteristics: maximum/mean depression, footprint depression, depression
volume, and depression centroid.

Included cases are A2 control (2.0 kg), A3 control (1.75 kg), A4 incumbent
and control (1.625 kg, +5 mm y), and A5 incumbent and control (1.625 kg,
+50 mm x). The rejected A2 incumbent is intentionally excluded because its
strict center-penetration gate failed.

See `characteristics.csv` for state-level metrics and `summary.json` for full
case metadata. These are prediction-transfer diagnostics, not new optimizer
observations or evidence of real-sand calibration.
