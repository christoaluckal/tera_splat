# Tera Splat Docs

This folder contains only current, actionable docs for the prototype.

## Read First

1. [Current State](current_state.md)
2. [Single-Trial Calibration](single_trial_calibration.md)
3. [RealSense Instrumentation And Real6 Trial](realsense_instrumentation_real6.md)
4. [Mass-Controlled Bridge Findings](mass_controlled_bridge_findings.md)
5. [PhysGaussian Notes](00_physgaussian_notes.md)

Current generated calibration-readiness report:

```text
../reports/single_trial_real3_report.md
```

Older phase-roadmap docs were removed because they described an intended plan
that no longer matched the implemented Genesis, PhysGaussian, subsurface, and
indenter scripts.

## Current Milestone

Use a settled, splat-derived terrain bed and a mass-controlled gravitational
cylinder release to reproduce the real before/action/after sand trial. Then
calibrate two effective Genesis MPM parameters:

- `log10_E`
- `phi_deg`

Do not claim geotechnical uniqueness from one trial. The output is an effective
Genesis parameter estimate and plausible region for the measured experiment.
