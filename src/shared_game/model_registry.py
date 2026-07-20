from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "models.json"


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def available_models() -> list[str]:
    return [item["id"] for item in registry()["models"]]


def default_model() -> str:
    return registry()["default_model"]


def validate_model(model: str) -> str:
    if model not in available_models():
        raise ValueError(f"unsupported model: {model}; choose one of {available_models()}")
    return model
