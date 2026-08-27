"""Frozen contextual-bandit model for animal-service selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "v1327-service-bandit-depth2.json"
)
MODEL_REPORT: dict[str, Any] = json.loads(
    MODEL_PATH.read_text(encoding="utf-8")
)
SERVICE_MODEL: dict[str, Any] = MODEL_REPORT["model"]
MODEL_METADATA = {
    "selection_day": 1,
    "training_contexts": 80,
    "validation_contexts": 40,
    "model_type": "depth-2 decision tree",
    "validation_wins": 37,
    "baseline_validation_wins": 35,
    "paired_validation_wins": 36,
    "oracle_validation_wins": 37,
    "status": "advanced to direct runtime and fresh promotion gates",
}
