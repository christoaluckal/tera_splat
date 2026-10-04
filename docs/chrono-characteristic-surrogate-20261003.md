# Chrono characteristic surrogate baseline

An explicit action-to-characteristics surrogate was fit from accepted A2–A8
Chrono episodes using features `(mass, radius, center_x, center_y)` and a
standardized low-order ridge model. Leave-one-out validation gives 0.387 mm
RMSE for mean depression, but 7.292 mm peak-depression RMSE, 130.143 cm³
volume RMSE, and 26.598 mm x-centroid RMSE.

Therefore the correct forward-model architecture is currently hybrid:

1. Newton remains the mechanics-respecting forward rollout for map prediction.
2. Chrono supplies synthetic GT episodes and characteristic targets.
3. A characteristic surrogate can be added only after substantially more GT
   action coverage; the current seven-episode fit is a baseline diagnostic,
   not a production predictor.

Artifact: `diagnostics/forward_model_transfer_20261002/chrono_surrogate/`.
