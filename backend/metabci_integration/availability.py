"""MetaBCI module availability checks."""

from __future__ import annotations

import importlib.util
from typing import Dict, Tuple


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def check_brainda_available() -> Tuple[bool, str]:
    """Check whether metabci.brainda can be imported in the current runtime."""
    if not _has_module("metabci.brainda"):
        return False, "metabci.brainda not installed"
    try:
        import metabci.brainda  # noqa: F401
        return True, "metabci.brainda imported"
    except Exception as exc:
        return False, str(exc)


def check_brainda_available_fast() -> Tuple[bool, str]:
    """Non-blocking availability probe for interactive API paths."""
    if _has_module("metabci.brainda"):
        return True, "metabci.brainda available"
    return False, "metabci.brainda not installed"


def get_metabci_status() -> Dict[str, object]:
    from .brainda_strict import get_strict_brainda_function_report
    from .brainstim_strict import get_strict_brainstim_function_report

    modules = {
        "metabci": _has_module("metabci"),
        "brainda": _has_module("metabci.brainda"),
        "brainflow": _has_module("metabci.brainflow"),
        "brainstim": _has_module("metabci.brainstim"),
    }
    return {
        "module_available": modules["metabci"],
        "modules": modules,
        "fallback_supported": True,
        "brainda_strict": get_strict_brainda_function_report(),
        "brainstim_strict": get_strict_brainstim_function_report(),
    }
