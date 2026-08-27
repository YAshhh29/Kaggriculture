"""Inference for learned daily wheat seed admission."""

from __future__ import annotations

from typing import Any


BASELINE = 0
EXTRA = 1


def select_seed_admission(
    model: dict[str, Any],
    features: dict[str, float],
) -> int:
    """Evaluate a shallow binary admission tree."""
    node = model
    while "arm" not in node:
        feature = str(node["feature"])
        node = (
            node["left"]
            if float(features[feature]) <= float(node["threshold"])
            else node["right"]
        )
    arm = int(node["arm"])
    if arm not in {BASELINE, EXTRA}:
        raise ValueError(f"Unknown seed admission arm: {arm}")
    return arm
