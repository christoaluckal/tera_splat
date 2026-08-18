"""Portable complete-state I/O for the single-bed Genesis MPM scene.

Genesis exposes the MPM constitutive state through :meth:`MPMEntity.get_state`,
but its convenient particle setters intentionally reset ``C``, ``F`` and
``Jp``.  A saved validity-bed state must therefore include all of those fields,
not just a particle point cloud.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch


STATE_KEYS = ("pos", "vel", "C", "F", "Jp", "active")
SCHEMA_VERSION = 1


def _as_numpy(value) -> np.ndarray:
    return value.detach().cpu().numpy()


def save_mpm_state(entity, path: Path) -> dict[str, int]:
    """Save the full MPM state for one entity to an ``npz`` artifact."""
    state = entity.get_state()
    arrays = {key: _as_numpy(getattr(state, key)) for key in STATE_KEYS}
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, schema_version=np.asarray(SCHEMA_VERSION), **arrays)
    return {"particles": int(arrays["pos"].shape[1]), "batch_size": int(arrays["pos"].shape[0])}


def load_mpm_state(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        missing = [key for key in STATE_KEYS if key not in data]
        if missing:
            raise ValueError(f"MPM state is missing fields: {missing}")
        schema = int(data["schema_version"]) if "schema_version" in data else 0
        if schema != SCHEMA_VERSION:
            raise ValueError(f"Unsupported MPM state schema {schema}; expected {SCHEMA_VERSION}")
        arrays = {key: np.array(data[key], copy=True) for key in STATE_KEYS}
    if arrays["pos"].ndim != 3 or arrays["pos"].shape[0] != 1 or arrays["pos"].shape[2] != 3:
        raise ValueError("MPM state position must have shape [1, particles, 3]")
    particle_count = arrays["pos"].shape[1]
    expected = {
        "vel": (1, particle_count, 3),
        "C": (1, particle_count, 3, 3),
        "F": (1, particle_count, 3, 3),
        "Jp": (1, particle_count),
        "active": (1, particle_count),
    }
    for key, shape in expected.items():
        if arrays[key].shape != shape:
            raise ValueError(f"MPM state {key} has shape {arrays[key].shape}; expected {shape}")
    return arrays


def restore_mpm_state(entity, arrays: dict[str, np.ndarray], device) -> None:
    """Restore every MPM constitutive field without using reset-prone setters."""
    n_particles = int(arrays["pos"].shape[1])
    if entity.n_particles != n_particles or entity.solver.n_particles != n_particles:
        raise ValueError(
            "Complete-state restore currently supports one MPM entity with the same particle count "
            f"(state={n_particles}, entity={entity.n_particles}, solver={entity.solver.n_particles})"
        )
    state = SimpleNamespace(
        pos=torch.as_tensor(arrays["pos"], dtype=torch.float32, device=device),
        vel=torch.as_tensor(arrays["vel"], dtype=torch.float32, device=device),
        C=torch.as_tensor(arrays["C"], dtype=torch.float32, device=device),
        F=torch.as_tensor(arrays["F"], dtype=torch.float32, device=device),
        Jp=torch.as_tensor(arrays["Jp"], dtype=torch.float32, device=device),
        active=torch.as_tensor(arrays["active"], dtype=torch.bool, device=device),
    )
    entity.solver.set_state(entity._sim.cur_substep_local, state)


def geostatic_state_from_points(
    entity,
    points: np.ndarray,
    surface_particle_count: int,
    *,
    density_kg_m3: float,
    gravity_mps2: float,
    youngs_modulus_pa: float,
    poisson_ratio: float,
    stress_scale: float = 1.0,
) -> dict[str, np.ndarray]:
    """Return a complete in-situ state with analytic, depth-varying pressure.

    ``F`` is initialized to the isotropic elastic compression corresponding to
    ``p = rho*g*depth``.  The surface coordinates are never changed.  This is
    the conventional geostatic initial-condition approximation for the flat,
    layered metric beds used by the first validity gate.
    """
    if surface_particle_count <= 0 or points.shape[0] % surface_particle_count:
        raise ValueError("Metric bed must have complete equal-sized vertical layers")
    if not (density_kg_m3 > 0 and gravity_mps2 > 0 and youngs_modulus_pa > 0):
        raise ValueError("Density, gravity, and Young's modulus must be positive")
    if not (-1.0 < poisson_ratio < 0.5):
        raise ValueError("Poisson ratio must be between -1 and 0.5")
    state = entity.get_state()
    arrays = {key: _as_numpy(getattr(state, key)) for key in STATE_KEYS}
    surface_z = points[:surface_particle_count, 2]
    top_for_particle = np.tile(surface_z, points.shape[0] // surface_particle_count)
    depth = np.maximum(top_for_particle - points[:, 2], 0.0)
    bulk_modulus = youngs_modulus_pa / (3.0 * (1.0 - 2.0 * poisson_ratio))
    # For an isotropic deformation F=sI, small-strain pressure is
    # p ~= -3K log(s).  This assigns a compressive in-situ stress field while
    # keeping the observed surface exactly at the Chrono H0 geometry.
    scale = np.exp(-float(stress_scale) * density_kg_m3 * gravity_mps2 * depth / (3.0 * bulk_modulus)).astype(np.float32)
    F = np.zeros((points.shape[0], 3, 3), dtype=np.float32)
    F[:, 0, 0] = scale
    F[:, 1, 1] = scale
    F[:, 2, 2] = scale
    arrays["F"][0] = F
    arrays["C"].fill(0.0)
    arrays["vel"].fill(0.0)
    arrays["Jp"].fill(0.0)
    return arrays
