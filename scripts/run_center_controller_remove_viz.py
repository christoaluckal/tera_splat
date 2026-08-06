#!/usr/bin/env python3
"""Run a PD-controlled center indenter press-and-remove visualization."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "outputs" / "center_controller_remove_r010_m20")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "physgaussian_sand_sinkage_mid.json")
    parser.add_argument("--initial-particles-ply", type=Path, default=None)
    parser.add_argument("--initial-metadata-json", type=Path, default=None)
    parser.add_argument("--radius", type=float, default=0.10)
    parser.add_argument("--mass", type=float, default=20.0)
    parser.add_argument("--indent-depth", type=float, default=0.08)
    parser.add_argument("--indent-start-time", type=float, default=0.15)
    parser.add_argument("--indent-ramp-time", type=float, default=0.80)
    parser.add_argument("--indent-hold-time", type=float, default=0.55)
    parser.add_argument("--retract-ramp-time", type=float, default=1.10)
    parser.add_argument("--remove-clearance", type=float, default=0.18)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--dt", type=float, default=0.00025)
    parser.add_argument("--save-every", type=int, default=20)
    parser.add_argument("--pre-roll-steps", type=int, default=10000)
    parser.add_argument("--pre-roll-clearance", type=float, default=0.35)
    parser.add_argument("--debug-contact-mode", choices=("none", "surface-plastic", "bounded-imprint"), default="none")
    parser.add_argument("--surface-lateral-scale", type=float, default=0.6)
    parser.add_argument("--rim-height-scale", type=float, default=0.75)
    parser.add_argument("--rim-width-scale", type=float, default=0.45)
    parser.add_argument("--video-duration", type=float, default=8.0)
    parser.add_argument("--fps", type=float, default=60.0)
    return parser.parse_args()


def run(command: list[str]) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def write_overlay(path: Path, args: argparse.Namespace) -> None:
    lines = [
        "center controller remove viz",
        f"m={args.mass:.3g} kg  r={args.radius:.3g} m",
        f"indent={args.indent_depth * 100.0:.1f} cm",
        f"ramp={args.indent_ramp_time:.1f}s hold={args.indent_hold_time:.1f}s",
        f"remove clearance={args.remove_clearance * 100.0:.1f} cm",
        "control=PD rigid-MPM",
        f"contact={args.debug_contact_mode}",
        f"pre-roll={args.pre_roll_steps} steps",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    run(
        [
            sys.executable,
            "scripts/run_genesis_indenter_test.py",
            "--config",
            str(args.config),
            "--output-dir",
            str(args.output_dir),
            "--query-xy",
            "0.0",
            "0.0",
            "--indenter-body-mode",
            "rigid",
            "--debug-contact-mode",
            args.debug_contact_mode,
            "--indenter-control-mode",
            "pd",
            "--indenter-radius",
            str(args.radius),
            "--indenter-height",
            "0.05",
            "--indenter-mass",
            str(args.mass),
            "--indenter-softness",
            "0.005",
            "--indenter-friction",
            "0.8",
            "--indenter-restitution",
            "0.0",
            "--indenter-kp",
            "800000",
            "--indenter-kv",
            "20000",
            "--indenter-force-limit",
            "200000",
            "--indent-depth",
            str(args.indent_depth),
            "--indent-start-time",
            str(args.indent_start_time),
            "--indent-ramp-time",
            str(args.indent_ramp_time),
            "--indent-hold-time",
            str(args.indent_hold_time),
            "--retract-ramp-time",
            str(args.retract_ramp_time),
            "--remove-clearance",
            str(args.remove_clearance),
            "--start-clearance",
            "0.03",
            "--steps",
            str(args.steps),
            "--dt",
            str(args.dt),
            "--substeps",
            "10",
            "--save-every",
            str(args.save_every),
            "--pre-roll-steps",
            str(args.pre_roll_steps),
            "--pre-roll-clearance",
            str(args.pre_roll_clearance),
            "--surface-lateral-scale",
            str(args.surface_lateral_scale),
            "--rim-height-scale",
            str(args.rim_height_scale),
            "--rim-width-scale",
            str(args.rim_width_scale),
            "--particle-size",
            "0.0125",
            "--n-grid",
            "64",
        ]
        + (
            [
                "--initial-particles-ply",
                str(args.initial_particles_ply),
                "--initial-metadata-json",
                str(args.initial_metadata_json),
            ]
            if args.initial_particles_ply is not None and args.initial_metadata_json is not None
            else []
        )
    )
    write_overlay(args.output_dir / "video_overlay_stats.txt", args)
    run(
        [
            sys.executable,
            "scripts/render_indenter_animation.py",
            str(args.output_dir),
            "--output",
            str(args.output_dir / "center_controller_remove_solid.mp4"),
            "--duration",
            str(args.video_duration),
            "--fps",
            str(args.fps),
            "--width",
            "1280",
            "--height",
            "720",
            "--point-radius",
            "1",
            "--view",
            "oblique",
            "--stats-text",
            str(args.output_dir / "video_overlay_stats.txt"),
            "--indenter-style",
            "solid",
            "--particle-view",
            "surface",
        ]
    )


if __name__ == "__main__":
    main()
