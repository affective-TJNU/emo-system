"""Backward-compatible re-export — use models.registry as the single source of truth."""

from models.registry import (  # noqa: F401
    DEFAULT_FEATURE_TYPE,
    MODEL_ALIASES,
    MODEL_LABELS,
    MODEL_REGISTRY,
    build_model,
    list_models,
    normalize_model_name,
)

__all__ = [
    "DEFAULT_FEATURE_TYPE",
    "MODEL_ALIASES",
    "MODEL_LABELS",
    "MODEL_REGISTRY",
    "build_model",
    "list_models",
    "normalize_model_name",
]
