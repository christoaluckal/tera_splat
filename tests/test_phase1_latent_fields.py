from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_latent_fields import (
    contact_column_fields,
    extract_particle_state,
    load_state_archive,
    mechanics_invariants,
    particle_column_fields,
    qualify_nonkinematic_families,
    repeat_field_evidence,
    select_active_collider_contacts,
    triplet_field_evidence,
    validate_particle_state,
    write_state_archive,
)


class FakeArray:
    def __init__(self, value: np.ndarray):
        self.value = np.asarray(value)

    def numpy(self) -> np.ndarray:
        return self.value


class Namespace:
    pass


def fake_state(*, informative: bool) -> Namespace:
    count = 2
    state = Namespace()
    state.particle_q = FakeArray(np.asarray([[0, 0, 0], [1, 0, 0]], dtype=float))
    state.particle_qd = FakeArray(np.asarray([[0, 0, 0], [0, 0, -2]], dtype=float))
    state.mpm = Namespace()
    gradient = np.zeros((count, 3, 3), dtype=float)
    elastic = np.repeat(np.eye(3)[None], count, axis=0)
    plastic = np.ones(count, dtype=float)
    stress = np.zeros((count, 3, 3), dtype=float)
    if informative:
        gradient[1, 2, 2] = -3.0
        elastic[1] = np.diag([1.0, 1.0, 0.9])
        plastic[1] = 0.8
        stress[1] = np.diag([-1.0, -2.0, -3.0])
    state.mpm.particle_qd_grad = FakeArray(gradient)
    state.mpm.particle_elastic_strain = FakeArray(elastic)
    state.mpm.particle_Jp = FakeArray(plastic)
    state.mpm.particle_stress = FakeArray(stress)
    state.mpm.particle_transform = FakeArray(
        np.repeat(np.eye(3)[None], count, axis=0)
    )
    return state


class FakeCoupledSolver:
    def __init__(self, entry_state: Namespace):
        self.state = entry_state
        self.calls: list[tuple[str, str]] = []

    def entry_state(self, name: str, phase: str) -> Namespace:
        self.calls.append((name, phase))
        return self.state


def test_coupled_extraction_uses_parent_kinematics_and_entry_mechanics() -> None:
    parent = fake_state(informative=False)
    entry = fake_state(informative=True)
    entry.particle_q = FakeArray(np.full((2, 3), 99.0))
    solver = FakeCoupledSolver(entry)

    arrays = extract_particle_state(parent, coupled_solver=solver)

    np.testing.assert_array_equal(arrays["position_m"], parent.particle_q.numpy())
    np.testing.assert_array_equal(arrays["stress_pa"], entry.mpm.particle_stress.numpy())
    assert solver.calls == [("mpm", "current")]
    assert arrays["plastic_jacobian"][1] == pytest.approx(0.8)


def test_mechanics_invariants_have_known_rotation_invariant_values() -> None:
    arrays = extract_particle_state(fake_state(informative=True))
    invariants = mechanics_invariants(arrays)

    assert invariants["speed_mps"].tolist() == [0.0, 2.0]
    assert invariants["stress_mean_pa"][1] == pytest.approx(-2.0)
    assert invariants["stress_von_mises_pa"][1] == pytest.approx(np.sqrt(3.0))
    assert invariants["stress_frobenius_pa"][1] == pytest.approx(np.sqrt(14.0))
    assert invariants["elastic_jacobian"][1] == pytest.approx(0.9)
    assert invariants["plastic_jacobian"][1] == pytest.approx(0.8)
    assert invariants["velocity_divergence_per_s"][1] == pytest.approx(-3.0)


def test_state_archive_round_trip_and_shape_validation(tmp_path: Path) -> None:
    arrays = extract_particle_state(fake_state(informative=True))
    path = tmp_path / "state.npz"
    write_state_archive(
        path,
        arrays,
        extra_arrays={"contact_normal_impulse_ns": np.asarray([0.0, 1.0])},
    )

    loaded = load_state_archive(path)
    for name, expected in arrays.items():
        np.testing.assert_array_equal(loaded[name], expected)
    assert int(loaded["schema_version"]) == 2
    np.testing.assert_array_equal(loaded["contact_normal_impulse_ns"], [0.0, 1.0])

    invalid = dict(arrays)
    invalid["stress_pa"] = np.zeros((1, 3, 3))
    with pytest.raises(ValueError, match="stress_pa has shape"):
        validate_particle_state(invalid)


def test_particle_columns_conserve_count_mass_and_reduce_fields() -> None:
    arrays = extract_particle_state(fake_state(informative=True))
    xs = np.asarray([0.0, 1.0])
    ys = np.asarray([0.0, 1.0])

    columns = particle_column_fields(
        arrays,
        x_coordinates_m=xs,
        y_coordinates_m=ys,
        particle_mass_kg=0.25,
    )

    assert int(np.sum(columns["column_particle_count"])) == 2
    assert float(np.sum(columns["column_mass_kg"])) == pytest.approx(0.5)
    np.testing.assert_array_equal(
        columns["column_mean_velocity_xyz_mps"][0, 1], [0.0, 0.0, -2.0]
    )
    assert columns["column_max_stress_von_mises_pa"][0, 1] == pytest.approx(
        np.sqrt(3.0)
    )


def test_contact_columns_keep_only_active_nodes_and_conserve_impulse() -> None:
    positions = np.asarray(
        [[0.0, 0.0, 0.0], [0.02, 0.0, 0.0], [1.0, 1.0, 0.0]]
    )
    impulses = np.asarray(
        [[0.0, 0.0, 2.0], [0.0, 0.0, 0.0], [1.0, 0.0, 3.0]]
    )

    columns = contact_column_fields(
        positions,
        impulses,
        x_coordinates_m=np.asarray([0.0, 1.0]),
        y_coordinates_m=np.asarray([0.0, 1.0]),
    )

    assert int(np.sum(columns["contact_node_count"])) == 2
    assert float(np.sum(columns["contact_normal_impulse_ns"])) == pytest.approx(5.0)
    np.testing.assert_array_equal(columns["contact_impulse_xyz_ns"][0, 0], [0, 0, 2])


def test_active_contact_selection_filters_body_assignment_and_zero_rows() -> None:
    selected = select_active_collider_contacts(
        impulses_ns=np.asarray(
            [[0.0, 0.0, 2.0], [0.0, 0.0, 0.0], [0.0, 0.0, 4.0]]
        ),
        positions_m=np.asarray(
            [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [0.2, 0.0, 0.0]]
        ),
        collider_ids=np.asarray([0, 0, 1]),
        collider_body_indices=np.asarray([7, 8]),
        body_index=7,
    )

    np.testing.assert_array_equal(selected["contact_position_m"], [[0.0, 0.0, 0.0]])
    np.testing.assert_array_equal(selected["contact_impulse_ns"], [[0.0, 0.0, 2.0]])
    np.testing.assert_array_equal(selected["contact_collider_id"], [0])


def synthetic_triplet(scale: float = 1.0) -> dict[str, dict[str, np.ndarray]]:
    initial = extract_particle_state(fake_state(informative=False))
    loaded = extract_particle_state(fake_state(informative=True))
    post = {name: value.copy() for name, value in loaded.items()}
    post["stress_pa"] *= 0.5 * scale
    post["elastic_strain"] = np.repeat(np.eye(3)[None], 2, axis=0)
    post["elastic_strain"][1] = np.diag([1.0, 1.0, 0.95])
    post["plastic_jacobian"][1] = 0.9
    return {"initial": initial, "loaded": loaded, "post_unload": post}


def test_triplet_and_repeat_metrics_qualify_known_stable_signal() -> None:
    runs = [synthetic_triplet() for _ in range(3)]
    triplet = triplet_field_evidence(
        runs[0],
        center_xy_m=[0.5, 0.0],
        radius_m=1.0,
        radius_multiplier=2.0,
        minimum_local_particles=2,
    )
    action_signal = {
        field: evidence["maximum_pairwise_checkpoint_rms_change"]
        for field, evidence in triplet["fields"].items()
    }
    repeat = repeat_field_evidence(
        runs,
        local_mask=triplet["local_particle_mask"],
        action_signal=action_signal,
    )
    contract = {
        "repeatability": {
            "maximum_repeat_rms_over_action_signal": 0.25,
            "minimum_repeat_pearson_correlation": 0.95,
        },
        "candidate_nonkinematic_families": {
            "stress": {
                "minimum_loaded_local_robust_span": 0.01,
                "minimum_pairwise_checkpoint_rms_change": 0.01,
                "maximum_relative_antisymmetric_norm": 1e-8,
            },
            "elastic": {
                "minimum_loaded_local_robust_span": 1e-4,
                "minimum_pairwise_checkpoint_rms_change": 1e-4,
                "require_positive_jacobian": True,
            },
            "plastic": {
                "minimum_loaded_local_robust_span": 1e-4,
                "minimum_pairwise_checkpoint_rms_change": 1e-4,
                "require_positive_jacobian": True,
            },
        },
    }
    qualified = qualify_nonkinematic_families(triplet, repeat, contract)

    assert qualified["stress"]["qualified"] is True
    assert qualified["elastic"]["qualified"] is True
    assert qualified["plastic"]["qualified"] is True
    assert repeat["stress_von_mises_pa"]["repeat_rms_over_action_signal"] == 0.0
