# Changelog

This file records material changes relative to named Git commits. Generated
simulation outputs and external environments are listed for reproducibility but
are not part of the Git diff unless explicitly stated.

## Unreleased — changes since `0f30de26bdd151f822a2e691924b15e98e20b09d`

Baseline commit: `0f30de2` — `fixing bayesopt` — 2026-08-20 15:01:39 -04:00.

### Runtime and documentation

- Standardized commands and contributor documentation on the `chrono_splat`
  Conda environment instead of `tsplat`.
- Relocated `chrono_splat` to `/data/christoa/conda/envs/chrono_splat` and
  installed the runtime used for validation: Python 3.10, PyTorch 2.13.0+cu130,
  Genesis 1.3.3, W&B, NumPy, SciPy, Viser, and PLY support. The environment is
  external to Git.
- Expanded `docs/current-state.md` with the frozen-state contract, online/offline
  sweep evidence, corrected stress initialization, and the post-removal
  diagnostic plan.

### BayesOpt initialization boundary

- Changed `run_chrono_genesis_bayesopt.py` from rebuilding a candidate-dependent
  bed to requiring one accepted `--prepared-bed`.
- Froze particle spacing and size per study; the active optimization dimensions
  are `log10_E` and `phi_deg`.
- Added prepared-bed episode, acceptance, and particle-geometry validation.
- Persisted `result.json` for non-equilibrium trials instead of returning before
  the diagnostic record was written.
- Added candidate-initialization H0 metrics to W&B and persisted trial results.

### Candidate-consistent constitutive state

- Added `--reinitialize-geostatic-stress-from-state` to
  `run_mass_controlled_terrain.py`.
- Preserved frozen particle positions and active flags while rebuilding velocity,
  `C`, `F`, and `Jp` for each candidate material.
- Recomputed depth-dependent geostatic `F` from the candidate `E`, density, and
  Poisson ratio before contact.
- Added a cylinder-free candidate relaxation stage to
  `run_chrono_genesis_bridge.py`.
- Required candidate preparation to re-pass the original particle-speed and
  Chrono-oracle H0 RMSE/maximum-error gates before cylinder release.
- Persisted each accepted candidate state under
  `bridge/candidate_prepare_raw/mpm_state.npz` and recorded its metrics in the
  bridge manifest.

### Validation evidence

- Generated a fresh accepted 20 mm CPIC reference bed: equilibrium at 0.274 s,
  p99 speed 0.424 mm/s, H0 RMSE 0.615 mm, maximum H0 error 0.654 mm, with all
  14,161 target-valid cells supported.
- Verified the corrected reference candidate (`100 kPa`, `45 deg`) and formerly
  failing high-E candidate (`log10_E=5.636`, `phi=44.415 deg`) both pass H0,
  loaded equilibrium, and post-removal equilibrium.
- Confirmed the high-E negative-depth rebound disappeared after constitutive
  stress reconstruction.
- Completed online W&B run `61sldco9` using the pre-fix constitutive restore; its
  response feasibility interpretation is superseded by the stress fix.
- Completed corrected online W&B run `h2il8dg0`: 12/12 candidate preparations
  and loaded phases passed, while 3/12 post-removal phases reached equilibrium
  within 1 s. Best valid objective was 0.372 mm at `log10_E=4.5`,
  `phi_deg=35`.

### Remaining work

- Run the documented 1.0/1.5/2.0/3.0 s post-removal diagnostic before another
  calibration sweep.
- Freeze whether the Chrono residual target is defined by observation time or by
  equilibrium.
- Freeze the production post-removal window from the diagnostic evidence.

### Tracked files changed

- `docs/README.md`
- `docs/contributor-guidance.md`
- `docs/current-state.md`
- `scripts/run_chrono_genesis_bayesopt.py`
- `scripts/run_chrono_genesis_bridge.py`
- `scripts/run_mass_controlled_terrain.py`
- `CHANGELOG.md` (new)

### Generated evidence not tracked by Git

- `outputs/validity_experiment/A0_cal_full10mm_prepared_20mm_cpic_frozen/`
- `outputs/validity_experiment/bayesopt/A0_cal_full10mm_frozen_online/`
- `outputs/validity_experiment/bayesopt/A0_cal_candidate_stress_quick_online/`
- Local W&B run directories under `wandb/`; online runs are linked from
  `docs/current-state.md`.
