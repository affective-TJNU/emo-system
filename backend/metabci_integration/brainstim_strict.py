"""Registry of strictly counted MetaBCI brainstim library APIs used by emo-system."""

from __future__ import annotations

from typing import Any, Dict, List


STRICT_BRAINSTIM_FUNCTIONS: List[Dict[str, str]] = [
    {
        "id": "brainstim_lsl_port",
        "name": "LsLPort.setData",
        "brainstim_api": "metabci.brainstim.utils.LsLPort.setData",
        "implementation": "metabci_integration.brainstim_runtime.verify_lsl_port_set_data",
        "endpoint": "/api/metabci/brainstim/verify",
        "description": "Send LSL markers for EEG epoch alignment (brainstim ↔ brainflow)",
    },
    {
        "id": "brainstim_check_array",
        "name": "_check_array_like",
        "brainstim_api": "metabci.brainstim.utils._check_array_like",
        "implementation": "metabci_integration.brainstim_runtime.verify_check_array_like",
        "endpoint": "/api/metabci/brainstim/verify",
        "description": "Validate paradigm stimulus array dimensions via brainstim utils",
    },
    {
        "id": "brainstim_clean_dict",
        "name": "_clean_dict",
        "brainstim_api": "metabci.brainstim.utils._clean_dict",
        "implementation": "metabci_integration.brainstim_runtime.verify_clean_dict",
        "endpoint": "/api/metabci/brainstim/verify",
        "description": "Clean paradigm stimulus cache via brainstim utils",
    },
    {
        "id": "brainstim_register_paradigm",
        "name": "Experiment.register_paradigm",
        "brainstim_api": "metabci.brainstim.framework.Experiment.register_paradigm",
        "implementation": "metabci_integration.brainstim_runtime.verify_register_paradigm",
        "endpoint": "/api/metabci/brainstim/verify",
        "description": "Register SEED passive emotion paradigm (bonus when DISPLAY available)",
        "bonus": True,
    },
]


def get_strict_brainstim_function_report() -> Dict[str, Any]:
    from .brainstim_runtime import get_brainstim_runtime_status

    runtime = get_brainstim_runtime_status()
    verified_ids = set(runtime.get("verified_strict_ids") or [])
    functions = []
    for item in STRICT_BRAINSTIM_FUNCTIONS:
        entry = dict(item)
        is_bonus = bool(item.get("bonus"))
        entry["runtime_verified"] = item["id"] in verified_ids
        entry["counts_for_strict"] = not is_bonus
        functions.append(entry)

    verified_count = sum(
        1 for item in functions if item["runtime_verified"] and item.get("counts_for_strict", True)
    )
    return {
        "strict_function_count": sum(1 for item in functions if item.get("counts_for_strict", True)),
        "runtime_verified_count": verified_count,
        "strict_functions": functions,
        "meets_minimum_one": verified_count >= 1,
        "meets_minimum_three": verified_count >= 3,
        "runtime": runtime,
        "scoring_note": (
            "Strict scoring counts only direct calls to metabci.brainstim library APIs. "
            "Run POST /api/metabci/brainstim/verify while recording the preliminary video."
        ),
    }
