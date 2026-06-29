#!/usr/bin/env python3
"""Print quick stats for the EDGS iteration-7000 scene."""

from __future__ import annotations

from view_iteration_7000 import DEFAULT_PLY, load_3dgs_ply


def main() -> None:
    data = load_3dgs_ply(
        DEFAULT_PLY,
        opacity_threshold=0.02,
        max_gaussians=0,
        seed=0,
        scale_multiplier=1.0,
        axis_transform="opencv-to-zup",
        align_ground_z=True,
    )
    print("scene: EDGS/output/point_cloud/iteration_7000/point_cloud.ply")
    print("material assumption: all_sand")
    print(f"retained_gaussians: {data.centers.shape[0]}")
    print(f"bounds_min: {data.bounds_min.tolist()}")
    print(f"bounds_max: {data.bounds_max.tolist()}")


if __name__ == "__main__":
    main()
