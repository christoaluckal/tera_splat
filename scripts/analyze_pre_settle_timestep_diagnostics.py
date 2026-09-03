#!/usr/bin/env python3
"""Compare controlled Genesis pre-settle traces across timesteps.

This is a post-processing tool only. It reads lightweight CSV output from
run_mass_controlled_terrain.py and does not fit or invoke a learned model.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        metavar="LABEL=RUN_DIR",
        help="Completed pre-settle trace; repeat once per timestep.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--speed-threshold-mps", type=float, default=5.0e-4)
    parser.add_argument("--late-window-s", type=float, default=1.0)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def parse_run_spec(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"run must be LABEL=RUN_DIR, got {value!r}")
    label, path = value.split("=", 1)
    if not label or not path:
        raise ValueError(f"run must be LABEL=RUN_DIR, got {value!r}")
    return label, Path(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_metrics(path: Path) -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_csv(path)}


def as_float(row: dict[str, str], name: str) -> float:
    value = row.get(name, "")
    return float(value) if value not in (None, "") else float("nan")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = rows[0].keys() if rows else ()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def maximum_contiguous_duration(times: np.ndarray, condition: np.ndarray) -> float:
    """Return the longest sampled interval for which condition stays true."""
    if times.size < 2 or not np.any(condition):
        return 0.0
    longest = 0.0
    start: float | None = None
    previous = float(times[0])
    for time, accepted in zip(times, condition):
        time = float(time)
        if accepted and start is None:
            start = time
        if not accepted and start is not None:
            longest = max(longest, previous - start)
            start = None
        previous = time
    if start is not None:
        longest = max(longest, previous - start)
    return float(longest)


def summarize_trace(
    label: str,
    run_dir: Path,
    rows: list[dict[str, str]],
    metrics: dict[str, str],
    threshold: float,
    late_window_s: float,
) -> dict[str, Any]:
    times = np.asarray([as_float(row, "time_s") for row in rows])
    p99 = np.asarray([as_float(row, "speed_p99_mps") for row in rows])
    final = rows[-1]
    late = times >= max(0.0, float(times[-1]) - late_window_s)
    below = p99 <= threshold
    first_equilibrium = metrics.get("pre_settle_first_equilibrium_time", "")
    final_p95 = as_float(final, "speed_p95_mps")
    final_wall = as_float(final, "top_near_side_wall_fraction")
    final_surface = as_float(final, "top_near_surface_fraction")
    if final_wall >= 0.9 and final_p95 <= threshold:
        diagnosis = "boundary-localized fast tail; bulk p95 is below the gate"
    elif final_surface >= 0.9:
        diagnosis = "free-surface-localized motion; p95 remains above the gate"
    elif final_wall >= 0.9:
        diagnosis = "boundary-localized motion extends below the fastest percentile"
    else:
        diagnosis = "motion is not predominantly side-wall localized"
    return {
        "label": label,
        "run_dir": str(run_dir.resolve()),
        "termination_reason": metrics.get("pre_settle_termination_reason", "unknown"),
        "duration_s": float(times[-1]),
        "diagnostic_samples": len(rows),
        "first_equilibrium_time_s": float(first_equilibrium) if first_equilibrium else "",
        "final_speed_p50_mps": as_float(final, "speed_p50_mps"),
        "final_speed_p95_mps": final_p95,
        "final_speed_p99_mps": as_float(final, "speed_p99_mps"),
        "final_speed_rms_mps": as_float(final, "speed_rms_mps"),
        "late_speed_p99_median_mps": float(np.median(p99[late])),
        "late_speed_p99_min_mps": float(np.min(p99[late])),
        "late_speed_p99_max_mps": float(np.max(p99[late])),
        "samples_p99_at_or_below_gate_fraction": float(np.mean(below)),
        "longest_sampled_p99_below_gate_s": maximum_contiguous_duration(times, below),
        "final_top_near_side_wall_fraction": final_wall,
        "final_top_near_ground_fraction": as_float(final, "top_near_ground_fraction"),
        "final_top_near_surface_fraction": final_surface,
        "final_top_inside_action_footprint_fraction": as_float(
            final, "top_inside_action_footprint_fraction"
        ),
        "late_top_near_side_wall_mean_fraction": float(
            np.mean([as_float(row, "top_near_side_wall_fraction") for row, use in zip(rows, late) if use])
        ),
        "diagnosis": diagnosis,
    }


def summarize_movers(rows: list[dict[str, str]]) -> dict[str, Any]:
    hit_fraction = np.asarray([as_float(row, "diagnostic_sample_fraction") for row in rows])
    source_x = np.asarray([as_float(row, "source_x_m") for row in rows])
    source_y = np.asarray([as_float(row, "source_y_m") for row in rows])
    source_z = np.asarray([as_float(row, "source_z_m") for row in rows])
    final_x = np.asarray([as_float(row, "final_x_m") for row in rows])
    final_y = np.asarray([as_float(row, "final_y_m") for row in rows])
    final_z = np.asarray([as_float(row, "final_z_m") for row in rows])
    persistent = hit_fraction >= 0.5
    if not np.any(persistent):
        persistent = np.ones(hit_fraction.shape, dtype=bool)
    dz_mm = 1000.0 * (final_z - source_z)
    dxy_mm = 1000.0 * np.hypot(final_x - source_x, final_y - source_y)
    return {
        "reported_mover_count": len(rows),
        "persistent_mover_count_ge_50pct_samples": int(np.count_nonzero(hit_fraction >= 0.5)),
        "persistent_median_vertical_displacement_mm": float(np.median(dz_mm[persistent])),
        "persistent_mean_vertical_displacement_mm": float(np.mean(dz_mm[persistent])),
        "persistent_median_horizontal_displacement_mm": float(np.median(dxy_mm[persistent])),
    }


def render_speed_trajectories(
    path: Path,
    traces: list[tuple[str, list[dict[str, str]]]],
    threshold: float,
    dpi: int,
) -> None:
    figure, axes = plt.subplots(
        1, len(traces), figsize=(5.4 * len(traces), 4.6), sharey=True, layout="constrained"
    )
    axes = np.atleast_1d(axes)
    names = (("speed_p50_mps", "p50"), ("speed_p95_mps", "p95"), ("speed_p99_mps", "p99"))
    for axis, (label, rows) in zip(axes, traces):
        time = [as_float(row, "time_s") for row in rows]
        for name, display in names:
            axis.plot(
                time,
                [1000.0 * as_float(row, name) for row in rows],
                label=display,
                linewidth=1.3,
            )
        axis.axhline(
            1000.0 * threshold, color="black", linestyle="--", linewidth=1, label="p99 gate"
        )
        axis.set_title(label)
        axis.set_xlabel("pre-settle time (s)")
        axis.grid(alpha=0.25)
        axis.legend()
    axes[0].set_ylabel("particle speed (mm/s)")
    figure.suptitle("Whole-bed speed percentiles from the same n128 initial state")
    figure.savefig(path, dpi=dpi, facecolor="white")
    plt.close(figure)


def render_localization(
    path: Path,
    traces: list[tuple[str, list[dict[str, str]]]],
    dpi: int,
) -> None:
    figure, axes = plt.subplots(
        1, len(traces), figsize=(5.4 * len(traces), 4.6), sharey=True, layout="constrained"
    )
    axes = np.atleast_1d(axes)
    names = (
        ("top_near_side_wall_fraction", "side wall"),
        ("top_near_ground_fraction", "ground"),
        ("top_near_surface_fraction", "free surface"),
        ("top_inside_action_footprint_fraction", "future action footprint"),
    )
    for axis, (label, rows) in zip(axes, traces):
        time = [as_float(row, "time_s") for row in rows]
        for name, display in names:
            axis.plot(time, [as_float(row, name) for row in rows], label=display, linewidth=1.2)
        axis.set_title(label)
        axis.set_xlabel("pre-settle time (s)")
        axis.set_ylim(-0.03, 1.03)
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)
    axes[0].set_ylabel("fraction of fastest 1%")
    figure.suptitle("Spatial localization of the speed tail")
    figure.savefig(path, dpi=dpi, facecolor="white")
    plt.close(figure)


def render_top_movers(
    path: Path,
    mover_sets: list[tuple[str, list[dict[str, str]]]],
    dpi: int,
) -> None:
    figure, axes = plt.subplots(
        2, len(mover_sets), figsize=(5.3 * len(mover_sets), 8.4), layout="constrained"
    )
    if len(mover_sets) == 1:
        axes = np.asarray(axes).reshape(2, 1)
    scatter = None
    for column, (label, rows) in enumerate(mover_sets):
        x = np.asarray([as_float(row, "final_x_m") for row in rows])
        y = np.asarray([as_float(row, "final_y_m") for row in rows])
        z = np.asarray([as_float(row, "final_z_m") for row in rows])
        source_z = np.asarray([as_float(row, "source_z_m") for row in rows])
        hit = np.asarray([as_float(row, "diagnostic_sample_fraction") for row in rows])
        radius = np.hypot(x, y - 0.005)
        scatter = axes[0, column].scatter(
            x, y, c=hit, s=4, cmap="viridis", vmin=0.0, vmax=1.0
        )
        axes[0, column].set_title(f"{label}: plan view")
        axes[0, column].set_xlabel("x (m)")
        axes[0, column].set_ylabel("y (m)")
        axes[0, column].set_aspect("equal")
        axes[0, column].grid(alpha=0.2)
        axes[1, column].scatter(
            radius, 1000.0 * (z - source_z), c=hit, s=4, cmap="viridis", vmin=0.0, vmax=1.0
        )
        axes[1, column].axhline(0.0, color="black", linewidth=0.8)
        axes[1, column].set_title(f"{label}: net vertical displacement")
        axes[1, column].set_xlabel("radius from query center (m)")
        axes[1, column].set_ylabel("final minus source z (mm)")
        axes[1, column].grid(alpha=0.2)
    if scatter is not None:
        figure.colorbar(
            scatter,
            ax=list(axes.ravel()),
            label="fraction of samples in fastest 1%",
            shrink=0.75,
        )
    figure.suptitle("Persistent fastest particles (final positions)")
    figure.savefig(path, dpi=dpi, facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    traces: list[tuple[str, list[dict[str, str]]]] = []
    mover_sets: list[tuple[str, list[dict[str, str]]]] = []
    summaries: list[dict[str, Any]] = []
    combined_trace: list[dict[str, Any]] = []
    combined_movers: list[dict[str, Any]] = []
    for spec in args.run:
        label, run_dir = parse_run_spec(spec)
        trace_path = run_dir / "pre_settle_diagnostic.csv"
        movers_path = run_dir / "pre_settle_top_movers.csv"
        metrics_path = run_dir / "run_metrics.csv"
        for path in (trace_path, movers_path, metrics_path):
            if not path.is_file():
                raise FileNotFoundError(path)
        rows = read_csv(trace_path)
        movers = read_csv(movers_path)
        metrics = read_metrics(metrics_path)
        if not rows:
            raise ValueError(f"empty diagnostic trace: {trace_path}")
        traces.append((label, rows))
        mover_sets.append((label, movers))
        summaries.append(
            summarize_trace(
                label,
                run_dir,
                rows,
                metrics,
                args.speed_threshold_mps,
                args.late_window_s,
            )
        )
        summaries[-1].update(summarize_movers(movers))
        combined_trace.extend({"label": label, **row} for row in rows)
        combined_movers.extend({"label": label, **row} for row in movers)

    write_csv(args.output_dir / "pre_settle_summary.csv", summaries)
    write_csv(args.output_dir / "pre_settle_trajectories.csv", combined_trace)
    write_csv(args.output_dir / "persistent_top_movers.csv", combined_movers)
    render_speed_trajectories(
        args.output_dir / "speed_percentile_trajectories.png",
        traces,
        args.speed_threshold_mps,
        args.dpi,
    )
    render_localization(args.output_dir / "speed_tail_localization.png", traces, args.dpi)
    render_top_movers(
        args.output_dir / "persistent_top_mover_positions.png", mover_sets, args.dpi
    )

    median_below = all(
        float(row["final_speed_p50_mps"]) <= args.speed_threshold_mps for row in summaries
    )
    boundary_or_surface_dominated = all(
        max(
            float(row["final_top_near_side_wall_fraction"]),
            float(row["final_top_near_surface_fraction"]),
        )
        >= 0.9
        for row in summaries
    )
    report = {
        "method": {
            "learned_network_used": False,
            "same_initial_state_required": True,
            "speed_threshold_mps": args.speed_threshold_mps,
            "late_window_s": args.late_window_s,
            "fast_tail_fraction": 0.01,
        },
        "runs": summaries,
        "cross_run_diagnosis": {
            "median_below_gate_at_final_time_all_runs": median_below,
            "fastest_one_percent_boundary_or_surface_dominated_at_final_time_all_runs": (
                boundary_or_surface_dominated
            ),
            "classification": (
                "timestep-dependent boundary/free-surface mode, not uniform bulk compaction"
                if median_below and boundary_or_surface_dominated
                else "mixed or unresolved motion"
            ),
            "interpretation": (
                "The dominant fast population changes with timestep: wall/ground at 0.5 ms, wall plus "
                "surface at 0.25 ms, and almost entirely free surface at 0.125 ms. Median speed remains "
                "below the p99 gate value in every run, so this is not uniform whole-bed motion. At the "
                "fine step p95 is also above the gate, however, so the failure cannot be dismissed as a "
                "one-percent wall artifact. This diagnoses timestep-dependent preparation dynamics; it "
                "does not establish response convergence or justify changing a gate after seeing the result."
            ),
        },
        "artifacts": {
            "summary_csv": "pre_settle_summary.csv",
            "trajectories_csv": "pre_settle_trajectories.csv",
            "persistent_top_movers_csv": "persistent_top_movers.csv",
            "speed_plot": "speed_percentile_trajectories.png",
            "localization_plot": "speed_tail_localization.png",
            "positions_plot": "persistent_top_mover_positions.png",
        },
    }
    (args.output_dir / "diagnosis.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["cross_run_diagnosis"], indent=2))


if __name__ == "__main__":
    main()
