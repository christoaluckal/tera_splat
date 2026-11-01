#!/usr/bin/env python3
"""Continue the conditional v2 analysis through a JSON scalar compatibility shim.

The frozen evaluator is intentionally left unchanged. Its sensitivity result can
contain NumPy scalar booleans, which the standard JSON encoder rejects. This
wrapper converts only NumPy JSON values to their built-in equivalents and then
delegates the requested stage to the frozen evaluator.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

import evaluate_phase1_bed_state as evaluation


def json_builtin(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return {key: json_builtin(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [json_builtin(item) for item in value]
    return value


def write_json_compatible(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(json_builtin(value), indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> None:
    evaluation.write_json = write_json_compatible
    evaluation.main()


if __name__ == "__main__":
    main()
