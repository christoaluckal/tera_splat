# Multi-characteristic score

`score_forward_model_characteristics.py` applies a diagnostic loss of

`surface + 0.25*(|volume error|/100 cm³) + 0.25*(|peak error|/10 mm) +
0.25*(centroid error/5 mm)`.

This is deliberately not fed back into the existing BayesOpt observations.
It demonstrates that candidate ranking depends on the desired deformation
characteristics: A5 control is best on the loaded multi-characteristic score,
while A6 incumbent is next, and A4 incumbent remains better than A4 control.
The score is a selection diagnostic for the next calibration experiment, not a
claim of optimized material parameters.
