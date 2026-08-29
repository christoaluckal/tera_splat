#!/usr/bin/env bash
# Run the material-response diagnostic before committing to the fine-resolution target.
#
# This intentionally reuses material configurations saved by the completed 10 mm
# sweep.  The runs differ only in those material values; action, timing, prepared
# geometry, and initialization checks remain the same.
set -euo pipefail

repo_root="/eng/home/christoa/Workspace/splatting/Chrono"
chrono_episode="/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_guided_offset_10mm_gate6mm_v1"
prepared_bed="/data/christoa/Chrono/tera_splat/outputs/validity_experiment/A0_oracle_guided_offset_10mm_gate6mm_prepared_20mm_cpic_frozen/prepared_bed"
sweep_trials="/data/christoa/Chrono/tera_splat/outputs/validity_experiment/bayesopt/A0_oracle_guided_offset_10mm_gate6mm_fixedtime_online/study_5wpq5j75/trials"
diagnostic_root="/data/christoa/Chrono/tera_splat/outputs/validity_experiment/loading_diagnostic/A0_oracle_guided_offset_10mm_gate6mm_v1"
fine_chrono_episode="/data/christoa/Chrono/tera_splat_sim/validity_experiment/chrono_episodes/A0_oracle_guided_offset_5mm_gate6mm_v1"
fine_prepared_root="/data/christoa/Chrono/tera_splat/outputs/validity_experiment/A0_oracle_guided_offset_5mm_gate6mm_prepared_10mm_cpic_frozen"

mkdir -p "$diagnostic_root"
cd "$repo_root"

run_diagnostic() {
    local label="$1"
    local material_config="$2"
    conda run -n chrono_splat python tera_splat/scripts/run_chrono_genesis_bridge.py \
        --chrono-episode "$chrono_episode" \
        --prepared-bed "$prepared_bed" \
        --output-dir "$diagnostic_root/$label" \
        --config "$material_config" \
        --backend cuda \
        --particle-spacing-m 0.02 \
        --loaded-max-time 4.696 \
        --loaded-run-full-duration \
        --post-max-time 0.25 \
        --post-observation-times 0.25
}

# Lowest loaded-RMSE sweep response; selected even though the old post gate timed out.
run_diagnostic soft_iteration037 "$sweep_trials/iteration_037/material_config.json"
# Best trial that met both prior equilibrium requirements.
run_diagnostic best_valid_iteration024 "$sweep_trials/iteration_024/material_config.json"
# Stiffest sampled sweep material.
run_diagnostic stiff_iteration006 "$sweep_trials/iteration_006/material_config.json"

# A 5 mm SCM map has roughly four times as many cells per area as the 10 mm
# target.  It is recreated with the same guided-action and timing contract.
conda run -n chrono_splat python tera_splat_sim/run_cylinder_episode.py \
    --episode-id A0_oracle_guided_offset_5mm_gate6mm_v1 \
    --mass-kg 1.5 \
    --xy 0.0 0.005 \
    --timestep-s 0.001 \
    --scm-grid-spacing-m 0.005 \
    --scm-pit-size-m 0.6 0.6 \
    --max-loading-time-s 5.0 \
    --loading-linear-speed-threshold-mps 0.006 \
    --loading-angular-speed-threshold-radps 0.01 \
    --loading-hold-time-s 0.10 \
    --min-loading-time-s 0.25 \
    --residual-settle-s 0.25 \
    --vertical-guide \
    --output-dir "$fine_chrono_episode"

# A 10 mm Genesis particle spacing and 128-cell MPM grid are the corresponding
# finer Genesis discretization.  The projection will be evaluated on the new
# 5 mm Chrono map, rather than silently retaining the old 10 mm comparison grid.
conda run -n chrono_splat python tera_splat/scripts/build_chrono_settled_bed.py \
    --chrono-episode "$fine_chrono_episode" \
    --output-dir "$fine_prepared_root" \
    --backend cuda \
    --particle-spacing-m 0.01 \
    --particle-size 0.01 \
    --n-grid 128 \
    --dt 0.0005 \
    --enable-cpic

echo "COMPLETE: loading diagnostic and fine-resolution target/prepared bed"
