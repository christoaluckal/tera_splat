from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from scripts.pre_settle_diagnostics import pre_settle_diagnostic_row


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_chrono_genesis_model_form.py"
SPEC = importlib.util.spec_from_file_location("model_form_diagnostics", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

PRE_SETTLE_ANALYSIS_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "analyze_pre_settle_timestep_diagnostics.py"
)
PRE_SETTLE_SPEC = importlib.util.spec_from_file_location(
    "pre_settle_timestep_diagnostics", PRE_SETTLE_ANALYSIS_SCRIPT
)
assert PRE_SETTLE_SPEC is not None and PRE_SETTLE_SPEC.loader is not None
PRE_SETTLE_MODULE = importlib.util.module_from_spec(PRE_SETTLE_SPEC)
PRE_SETTLE_SPEC.loader.exec_module(PRE_SETTLE_MODULE)


def test_pareto_indices_for_minimization() -> None:
    points = np.array([[1.0, 4.0], [2.0, 3.0], [3.0, 2.0], [2.5, 4.5], [4.0, 1.0]])
    assert MODULE.pareto_indices(points).tolist() == [0, 1, 2, 4]


def test_radial_statistics_assigns_values_to_annuli() -> None:
    radius = np.array([0.0, 0.4, 0.6, 1.1])
    values = {"error": np.array([1.0, 3.0, 2.0, 4.0])}
    rows = MODULE.radial_statistics(radius, values, np.ones(4, dtype=bool), 0.5)
    assert [row["count"] for row in rows] == [2, 1, 1]
    assert rows[0]["error_mean"] == 2.0
    assert rows[1]["error_rmse"] == 2.0


def test_sensitivity_effects_hold_one_axis_fixed() -> None:
    rows = []
    for n_grid, dt_s, loaded, residual in (
        (64, 0.0005, 2.0, 10.0),
        (64, 0.00025, 3.0, 12.0),
        (128, 0.0005, 1.5, 11.0),
        (128, 0.00025, 2.5, 13.5),
    ):
        rows.append(
            {
                "label": f"n{n_grid}_dt{dt_s}",
                "n_grid": n_grid,
                "dt_s": dt_s,
                "loaded_rmse_mm": loaded,
                "residual_footprint_rmse_mm": residual,
                "objective_mm": loaded + 0.5 * residual,
                "candidate_h0_rmse_mm": 0.5,
            }
        )
    effects = MODULE.sensitivity_effects(rows)
    assert len(effects) == 4
    assert effects[0]["comparison"] == "timestep"
    assert effects[0]["loaded_rmse_delta_mm"] == 1.0
    assert effects[2]["comparison"] == "resolution"


def test_three_level_convergence_estimate() -> None:
    rows = [
        {
            "label": label,
            "n_grid": 128,
            "dt_s": dt_s,
            "prepared_state_dt_s": dt_s,
            "loaded_rmse_mm": value,
            "residual_footprint_rmse_mm": 10.0 + value,
            "objective_mm": 5.0 + value,
        }
        for label, dt_s, value in (
            ("coarse", 0.0005, 1.0),
            ("middle", 0.00025, 1.5),
            ("fine", 0.000125, 1.75),
        )
    ]
    estimates = MODULE.convergence_estimates(rows)
    loaded = next(row for row in estimates if row["metric"] == "loaded_rmse_mm")
    assert loaded["same_direction"]
    assert loaded["decreasing_change"]
    assert loaded["observed_order"] == 1.0
    assert loaded["extrapolated_zero_dt_value"] == 2.0


def test_pre_settle_diagnostic_localizes_fast_tail() -> None:
    source = np.array(
        [
            [-1.0, 0.0, 0.0],
            [0.0, 0.0, 0.5],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.5],
        ]
    )
    row, indices = pre_settle_diagnostic_row(
        step=2,
        dt=0.1,
        speeds=np.array([4.0, 1.0, 2.0, 3.0]),
        positions=source,
        source_points=source,
        query_xy=np.array([0.0, 0.0]),
        footprint_radius=0.25,
        particle_size=0.1,
        top_fraction=0.5,
        stable_steps=1,
        equilibrium_seen=False,
    )
    assert set(indices.tolist()) == {0, 3}
    assert row["time_s"] == 0.2
    assert row["top_near_side_wall_fraction"] == 1.0
    assert row["top_inside_action_footprint_fraction"] == 0.0


def test_maximum_contiguous_duration() -> None:
    times = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    accepted = np.array([False, True, True, False, True, True])
    assert PRE_SETTLE_MODULE.maximum_contiguous_duration(times, accepted) == 0.1


def test_summarize_trace_identifies_boundary_tail(tmp_path: Path) -> None:
    rows = []
    for time, p99 in ((0.0, 8.0e-4), (0.1, 4.0e-4), (0.2, 4.0e-4)):
        rows.append(
            {
                "time_s": str(time),
                "speed_p50_mps": "0.0001",
                "speed_p95_mps": "0.0003",
                "speed_p99_mps": str(p99),
                "speed_rms_mps": "0.0002",
                "top_near_side_wall_fraction": "0.95",
                "top_near_ground_fraction": "0.2",
                "top_near_surface_fraction": "0.1",
                "top_inside_action_footprint_fraction": "0.0",
            }
        )
    summary = PRE_SETTLE_MODULE.summarize_trace(
        "test",
        tmp_path,
        rows,
        {"pre_settle_termination_reason": "equilibrium"},
        5.0e-4,
        1.0,
    )
    assert summary["diagnosis"] == "boundary-localized fast tail; bulk p95 is below the gate"
    assert summary["samples_p99_at_or_below_gate_fraction"] == 2.0 / 3.0


def test_summarize_trace_identifies_free_surface_mode(tmp_path: Path) -> None:
    rows = [
        {
            "time_s": "1.0",
            "speed_p50_mps": "0.0003",
            "speed_p95_mps": "0.0007",
            "speed_p99_mps": "0.001",
            "speed_rms_mps": "0.0004",
            "top_near_side_wall_fraction": "0.5",
            "top_near_ground_fraction": "0.0",
            "top_near_surface_fraction": "0.999",
            "top_inside_action_footprint_fraction": "0.16",
        }
    ]
    summary = PRE_SETTLE_MODULE.summarize_trace("fine", tmp_path, rows, {}, 5.0e-4, 1.0)
    assert summary["diagnosis"] == "free-surface-localized motion; p95 remains above the gate"


def test_summarize_movers_uses_persistent_subset() -> None:
    rows = [
        {
            "diagnostic_sample_fraction": hit,
            "source_x_m": "0",
            "source_y_m": "0",
            "source_z_m": "0",
            "final_x_m": dx,
            "final_y_m": "0",
            "final_z_m": dz,
        }
        for hit, dx, dz in (
            ("0.75", "0.001", "0.002"),
            ("0.50", "0.003", "0.004"),
            ("0.25", "1.0", "1.0"),
        )
    ]
    summary = PRE_SETTLE_MODULE.summarize_movers(rows)
    assert summary["persistent_mover_count_ge_50pct_samples"] == 2
    assert summary["persistent_median_vertical_displacement_mm"] == 3.0
    assert summary["persistent_median_horizontal_displacement_mm"] == 2.0
