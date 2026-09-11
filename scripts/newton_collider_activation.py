"""Per-collider activation-distance override for Newton implicit-MPM diagnostics.

Newton 1.5.1 exposes collider thickness and projection thresholds, but its
rasterized contact activation distance is a module-wide constant.  This
version-locked adapter changes only the selected collider's grid-node
activation threshold while retaining the original signed-distance geometry
and particle-level ``project_outside`` behavior.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import warp as wp
import warp.fem as fem

from newton._src.solvers.implicit_mpm import rasterized_collisions as _collisions
from newton._src.solvers.implicit_mpm import solver_implicit_mpm as _solver_module


@wp.kernel
def _rasterize_collider_with_per_collider_activation(
    collider: _collisions.Collider,
    body_q: wp.array[wp.transform],
    body_qd: wp.array[wp.spatial_vector],
    body_q_prev: wp.array[wp.transform],
    voxel_size: float,
    activation_distance_voxels: wp.array[float],
    dt: float,
    node_positions: wp.array[wp.vec3],
    node_environment_offsets: wp.array[int],
    node_volumes: wp.array[float],
    collider_sdf: wp.array[float],
    collider_velocity: wp.array[wp.vec3],
    collider_normals: wp.array[wp.vec3],
    collider_friction: wp.array[float],
    collider_adhesion: wp.array[float],
    collider_ids: wp.array[int],
):
    i = wp.tid()
    x = node_positions[i]

    collider_id = int(-1)
    material_id = int(0)
    sdf = float(1.0e12)
    sdf_gradient = wp.vec3(0.0)
    sdf_vel = wp.vec3(0.0)
    active = False
    if x[0] != fem.OUTSIDE:
        environment_index = int(-2)
        if node_environment_offsets:
            environment_index = _collisions.environment_from_offsets(
                i, node_environment_offsets
            )
        sdf, sdf_gradient, sdf_vel, collider_id, material_id = (
            _collisions.collision_sdf(
                x,
                environment_index,
                collider,
                body_q,
                body_qd,
                body_q_prev,
                dt,
            )
        )
        if collider_id >= 0:
            active = sdf < activation_distance_voxels[collider_id] * voxel_size

    collider_sdf[i] = sdf
    if not active:
        collider_velocity[i] = wp.vec3(0.0)
        collider_normals[i] = wp.vec3(0.0)
        collider_friction[i] = -1.0
        collider_adhesion[i] = 0.0
        collider_ids[i] = -1
        return

    collider_ids[i] = collider_id
    collider_normals[i] = sdf_gradient
    collider_friction[i] = collider.material_friction[material_id]
    collider_adhesion[i] = (
        collider.material_adhesion[material_id]
        * dt
        * node_volumes[i]
        / voxel_size
    )
    collider_velocity[i] = sdf_vel


def install_per_collider_activation_override(
    solver: Any,
    *,
    body_index: int,
    activation_distance_voxels: float,
) -> dict[str, Any]:
    """Install a process-local rasterizer override for one solver collider."""
    if not np.isfinite(activation_distance_voxels):
        raise ValueError("activation distance must be finite")

    body_indices = np.asarray(solver.collider_body_index.numpy(), dtype=int)
    matches = np.flatnonzero(body_indices == int(body_index))
    if matches.size != 1:
        raise ValueError(
            "expected exactly one collider for activation override body "
            f"{body_index}, found {matches.size}"
        )
    target_collider = int(matches[0])
    original: Callable[..., Any] = _solver_module.rasterize_collider
    cached: dict[tuple[int, int, str], wp.array] = {}

    def rasterize_with_override(
        collider,
        body_q,
        body_qd,
        body_q_prev,
        voxel_size,
        dt,
        collider_space_restriction,
        collider_node_volume,
        collider_position_field,
        collider_distance_field,
        collider_normal_field,
        collider_velocity,
        collider_friction,
        collider_adhesion,
        collider_ids,
        temporary_store,
        node_environment_offsets=None,
    ):
        collision_node_count = collider_position_field.dof_values.shape[0]
        collider_position_field.dof_values.fill_(wp.vec3(fem.OUTSIDE))
        fem.interpolate(
            _collisions.world_position,
            dest=collider_position_field,
            at=collider_space_restriction,
            reduction="first",
            temporary_store=temporary_store,
        )

        degree = int(collider_position_field.degree)
        default_distance = 0.0 if degree == 0 else 0.5 / degree
        device = str(collider_position_field.dof_values.device)
        key = (int(collider.collider_mesh.shape[0]), degree, device)
        activation = cached.get(key)
        if activation is None:
            values = np.full(key[0], default_distance, dtype=np.float32)
            values[target_collider] = np.float32(activation_distance_voxels)
            activation = wp.array(values, dtype=float, device=device)
            cached[key] = activation

        wp.launch(
            _rasterize_collider_with_per_collider_activation,
            dim=collision_node_count,
            inputs=[
                collider,
                body_q,
                body_qd,
                body_q_prev,
                voxel_size,
                activation,
                dt,
                collider_position_field.dof_values,
                node_environment_offsets,
                collider_node_volume,
                collider_distance_field.dof_values,
                collider_velocity,
                collider_normal_field.dof_values,
                collider_friction,
                collider_adhesion,
                collider_ids,
            ],
        )

    if original.__module__ != _collisions.__name__:
        raise RuntimeError("Newton collider rasterizer was already overridden")
    _solver_module.rasterize_collider = rasterize_with_override
    return {
        "implementation": "process-local per-collider rasterization threshold",
        "target_collider_id": target_collider,
        "target_body_index": int(body_index),
        "requested_activation_distance_voxels": float(activation_distance_voxels),
        "containment_uses_newton_default": True,
        "signed_distance_geometry_unchanged": True,
        "project_outside_geometry_unchanged": True,
    }
