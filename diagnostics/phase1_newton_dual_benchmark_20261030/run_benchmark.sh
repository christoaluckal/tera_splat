#!/usr/bin/env bash
set -euo pipefail

repo_root=/eng/home/christoa/Workspace/splatting/Chrono/tera_splat
newton_python=/data/christoa/conda/envs/newton_splat/bin/python3.11
benchmark_root=$(mktemp -d /tmp/phase1_newton_dual_benchmark_20261030.XXXXXX)
monitor_pid=

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

cleanup() {
    if [[ -n "${monitor_pid}" ]] && kill -0 "${monitor_pid}" 2>/dev/null; then
        kill "${monitor_pid}" 2>/dev/null || true
        wait "${monitor_pid}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

monitor_gpu() {
    while true; do
        timestamp=$(date +%s.%N)
        nvidia-smi \
            --query-gpu=index,utilization.gpu,memory.used,power.draw,temperature.gpu \
            --format=csv,noheader,nounits \
            | awk -v timestamp="${timestamp}" '{print timestamp "," $0}'
        sleep 2
    done
}

start_monitor() {
    local destination=$1
    monitor_gpu > "${destination}" &
    monitor_pid=$!
}

stop_monitor() {
    if [[ -n "${monitor_pid}" ]]; then
        kill "${monitor_pid}" 2>/dev/null || true
        wait "${monitor_pid}" 2>/dev/null || true
        monitor_pid=
    fi
}

common_args=(
    "${repo_root}/scripts/run_newton_cylinder_diagnostic.py"
    --config "${repo_root}/configs/newton_sand_smoke_voxel7p8125mm.json"
    --candidate-preparation
    --device cuda:0
    --dt-s 0.00025
    --pre-settle-duration-s 0.35
    --pre-settle-required-duration-s 0.02
    --particle-speed-threshold-mps 0.0005
    --observation-time-mode independent_fixed
    --loaded-duration-s 0.05
    --residual-duration-s 0.05
    --proxy-iterations 8
    --rigid-substeps 16
    --cylinder-friction-coefficient 0.2
    --cylinder-collider-mode circumscribed_mesh
    --cylinder-collider-segments 128
    --cylinder-collision-guard-m 0.00001
    --cylinder-collision-bottom-inset-m 0
    --cylinder-projection-threshold-m 0.0
)

prepared_a=${repo_root}/outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_bulk_v1/newton_priors/surface_1101/preparation
prepared_b=${repo_root}/outputs/validity_experiment/newton/phase1_bed_state_v1/dataset_bulk_v1/newton_priors/surface_1102/preparation
chrono_a=${repo_root}/../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/dataset_bulk_v1/p1_train_joint-design_000
chrono_b=${repo_root}/../tera_splat_sim/validity_experiment/chrono_episodes/phase1_bed_state_v1/dataset_bulk_v1/p1_train_joint-design_001

run_case() {
    local label=$1
    local prepared=$2
    local chrono=$3
    local output=$4
    /usr/bin/time \
        -f $'wall_s=%e\nuser_s=%U\nsystem_s=%S\nmax_rss_kb=%M\nexit_status=%x' \
        -o "${benchmark_root}/${label}.time" \
        "${newton_python}" "${common_args[@]}" \
        --prepared-dir "${prepared}" \
        --chrono-episode "${chrono}" \
        --output-dir "${output}" \
        > "${benchmark_root}/${label}.stdout" \
        2> "${benchmark_root}/${label}.stderr"
}

mkdir -p \
    "${benchmark_root}/serial/a" \
    "${benchmark_root}/serial/b" \
    "${benchmark_root}/dual/a" \
    "${benchmark_root}/dual/b"

serial_start=$(date +%s.%N)
start_monitor "${benchmark_root}/serial_gpu.csv"
run_case serial_a "${prepared_a}" "${chrono_a}" "${benchmark_root}/serial/a"
run_case serial_b "${prepared_b}" "${chrono_b}" "${benchmark_root}/serial/b"
stop_monitor
serial_end=$(date +%s.%N)
awk -v start="${serial_start}" -v end="${serial_end}" \
    'BEGIN {printf "%.6f\n", end - start}' \
    > "${benchmark_root}/serial_batch_wall_s.txt"

dual_start=$(date +%s.%N)
start_monitor "${benchmark_root}/dual_gpu.csv"
set +e
run_case dual_a "${prepared_a}" "${chrono_a}" "${benchmark_root}/dual/a" &
pid_a=$!
run_case dual_b "${prepared_b}" "${chrono_b}" "${benchmark_root}/dual/b" &
pid_b=$!
wait "${pid_a}"
status_a=$?
wait "${pid_b}"
status_b=$?
set -e
stop_monitor
dual_end=$(date +%s.%N)
awk -v start="${dual_start}" -v end="${dual_end}" \
    'BEGIN {printf "%.6f\n", end - start}' \
    > "${benchmark_root}/dual_batch_wall_s.txt"
printf '%s\n' "${status_a}" > "${benchmark_root}/dual_a.exit_status"
printf '%s\n' "${status_b}" > "${benchmark_root}/dual_b.exit_status"

if [[ "${status_a}" -ne 0 || "${status_b}" -ne 0 ]]; then
    printf 'BENCH_ROOT=%s\n' "${benchmark_root}"
    exit 1
fi

printf 'BENCH_ROOT=%s\n' "${benchmark_root}"
