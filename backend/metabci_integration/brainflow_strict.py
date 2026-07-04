"""Registry of strictly counted MetaBCI brainflow library APIs used by emo-system."""

from __future__ import annotations

from typing import Any, Dict, List


STRICT_BRAINFLOW_FUNCTIONS: List[Dict[str, str]] = [
    {
        "id": "brainflow_process_worker",
        "name": "ProcessWorker.pre/consume/post",
        "brainflow_api": "metabci.brainflow.workers.ProcessWorker",
        "implementation": "metabci_integration.brainflow_worker.EmotionFeedbackWorker",
        "endpoint": "/api/metabci/brainflow/start",
        "description": "Online emotion inference via brainflow worker hooks",
    },
    {
        "id": "brainflow_marker",
        "name": "Marker.__call__/get_epoch",
        "brainflow_api": "metabci.brainflow.amplifiers.Marker",
        "implementation": "metabci_integration.brainflow_worker.extract_epoch_with_marker",
        "endpoint": "/api/metabci/brainflow/start",
        "description": "1.5s online epoch extraction for SEED segment replay",
    },
    {
        "id": "brainflow_logger",
        "name": "get_logger",
        "brainflow_api": "metabci.brainflow.logger.get_logger",
        "implementation": "metabci_integration.brainflow_worker.get_brainflow_logger",
        "endpoint": "/api/metabci/brainflow/status",
        "description": "brainflow online pipeline logging",
    },
]


def get_strict_brainflow_function_report() -> Dict[str, Any]:
    from .brainflow_worker import get_brainflow_runtime_status

    runtime = get_brainflow_runtime_status()
    active_ids = set(runtime.get("active_strict_ids", []))
    functions = []
    for item in STRICT_BRAINFLOW_FUNCTIONS:
        entry = dict(item)
        entry["runtime_active"] = item["id"] in active_ids
        functions.append(entry)

    active_count = sum(1 for item in functions if item["runtime_active"])
    return {
        "strict_function_count": len(STRICT_BRAINFLOW_FUNCTIONS),
        "runtime_active_count": active_count,
        "strict_functions": functions,
        "meets_minimum_one": active_count >= 1,
        "meets_minimum_three": active_count >= 3,
        "runtime": runtime,
        "scoring_note": (
            "Strict scoring counts only direct calls to metabci.brainflow library APIs. "
            "Marker requires a working liblsl (conda install -c conda-forge liblsl libstdcxx-ng)."
        ),
    }

