"""Frozen contextual-bandit model for capacity template selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "v1327-capacity-bandit-v3-knn.json"
)
MODEL_REPORT: dict[str, Any] = json.loads(
    MODEL_PATH.read_text(encoding="utf-8")
)
CAPACITY_MODEL: dict[str, Any] = MODEL_REPORT["model"]
MODEL_METADATA = {
    "selection_day": 4,
    "training_contexts": 28,
    "model_type": "knn",
    "k": 13,
    "distance_power": 2.0,
    "validation_games": 24,
    "validation_wins": 24,
    "validation_mean_margin": 12858.33,
    "fixed_wheat_mean_margin": 12648.96,
    "direct_rollout": "5-5 with exactly symmetric rewards versus fixed wheat",
    "status": "rejected; collapsed to fixed wheat in fresh rollouts",
}
