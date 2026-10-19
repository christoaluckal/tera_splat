# A7 geometry-transfer boundary

A7 is a Chrono GT episode for the 1.625 kg guided cylinder at `(0,+5 mm)`
with radius 55 mm instead of the canonical 73.025 mm. Chrono accepted the
loaded state at 0.456 s with 24.386021 mm sinkage; support/initial terrain
remain identical to A4.

The frozen incumbent fails the unchanged Newton mechanics gate: four sampled
analytic particle centers entered the cylinder, with maximum penetration
1.406 µm. The unchanged 100 kPa control passes and scores 2.643076 mm
objective, 0.574235 mm loaded RMSE, and 4.137683 mm residual-footprint RMSE.

This expands the forward-model boundary from mass/location transfer to
geometry transfer: the incumbent is not mechanically admissible for every
contact footprint, even when the Chrono oracle is accepted and the control is
valid. The smaller-radius case must therefore remain a reported boundary,
not an optimizer observation for the incumbent.
