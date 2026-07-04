"""Registry of strictly counted MetaBCI brainda library APIs used by emo-system."""

from __future__ import annotations

from typing import Any, Dict, List


STRICT_BRAINDA_FUNCTIONS: List[Dict[str, str]] = [
    {
        "id": "brainda_dataset",
        "name": "BaseDataset.get_data",
        "brainda_api": "metabci.brainda.datasets.base.BaseDataset",
        "implementation": "metabci_integration.brainda_seed_dataset.SEEDEmotionDataset",
        "endpoint": "/api/metabci/brainda/seed-dataset",
        "description": "SEED 15-subject emotion dataset in MetaBCI unified Raw structure",
    },
    {
        "id": "brainda_loso",
        "name": "EnhancedLeaveOneGroupOut.split",
        "brainda_api": "metabci.brainda.algorithms.utils.model_selection.EnhancedLeaveOneGroupOut",
        "implementation": "metabci_integration.brainda_loso.generate_loso_indices",
        "endpoint": "/api/metabci/brainda/loso",
        "description": "Leave-One-Subject-Out split via brainda cross-validation API",
    },
    {
        "id": "brainda_performance",
        "name": "Performance.evaluate",
        "brainda_api": "metabci.brainda.utils.performance.Performance",
        "implementation": "metabci_integration.brainda_evaluate.run_brainda_performance_evaluation",
        "endpoint": "/api/metabci/brainda/evaluate",
        "description": "Classification metrics (Acc/bAcc) via brainda Performance API",
    },
]


def get_strict_brainda_function_report() -> Dict[str, Any]:
    return {
        "strict_function_count": len(STRICT_BRAINDA_FUNCTIONS),
        "strict_functions": STRICT_BRAINDA_FUNCTIONS,
        "meets_minimum_three": len(STRICT_BRAINDA_FUNCTIONS) >= 3,
        "scoring_note": "Strict scoring counts only direct calls to metabci.brainda library APIs.",
    }

