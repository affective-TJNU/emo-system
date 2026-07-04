"""Helpers for MetaBCI unified (X, y, meta) data access."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch

from .availability import check_brainda_available
from .brainda_seed_dataset import (
    BRAIN_DA_DATASET_AVAILABLE,
    create_seed_emotion_dataset,
    summarize_seed_dataset,
    verify_seed_dataset_files,
)


LABEL_TO_EVENT = {
    -1: "negative",
    0: "neutral",
    1: "positive",
}


def build_de_feature_meta_dataframe(
    labels: torch.Tensor,
    dataset_code: str = "seed_emotion_4ch",
) -> pd.DataFrame:
    """Build brainda-style meta DataFrame from SEED DE tensor labels."""
    rows: List[Dict[str, Any]] = []
    label_array = labels.detach().cpu().numpy()
    subject_count, session_count, trial_count = label_array.shape

    for subject in range(subject_count):
        for session in range(session_count):
            for trial in range(trial_count):
                label_value = int(label_array[subject, session, trial])
                rows.append(
                    {
                        "subject": subject + 1,
                        "session": f"session_{session + 1}",
                        "run": f"trial_{trial + 1}",
                        "event": LABEL_TO_EVENT.get(label_value, "neutral"),
                        "trial_id": trial + 1,
                        "dataset": dataset_code,
                        "label": label_value,
                    }
                )
    return pd.DataFrame(rows)


def load_de_features_unified(
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = "de_comp_4ch_1p5s",
    raw_data_dir: Optional[Union[str, Path]] = None,
) -> Tuple[torch.Tensor, torch.Tensor, pd.DataFrame, Dict[str, Any]]:
    """Load DE tensors and attach MetaBCI unified meta information."""
    from .brainda_seed import load_seed_feature_tensors

    X, y, tensor_meta = load_seed_feature_tensors(str(seed_root), feature_type, raw_data_dir=raw_data_dir)
    meta_df = build_de_feature_meta_dataframe(y)

    dataset_summary: Dict[str, Any] = {
        "metabci_unified": False,
        "dataset_code": "seed_emotion_4ch",
        "meta_rows": int(len(meta_df)),
        "meta_columns": list(meta_df.columns),
    }

    if BRAIN_DA_DATASET_AVAILABLE:
        try:
            dataset = create_seed_emotion_dataset(
                raw_data_dir=raw_data_dir,
                feature_type=feature_type,
                seed_root=seed_root,
            )
            file_check = verify_seed_dataset_files(dataset)
            dataset_summary.update(
                {
                    "metabci_unified": True,
                    "dataset_code": dataset.dataset_code,
                    "raw_data_dir": str(dataset.raw_data_dir),
                    "file_check": file_check,
                }
            )
        except Exception as exc:
            dataset_summary.update(
                {
                    "metabci_unified": True,
                    "dataset_code": "seed_emotion_4ch",
                    "file_check_error": str(exc),
                }
            )

    brainda_available, brainda_message = check_brainda_available()
    unified_meta = {
        "loader": "brainda_unified_de_loader",
        "brainda_available": brainda_available,
        "brainda_message": brainda_message,
        "tensor_meta": tensor_meta,
        "dataset_summary": dataset_summary,
        "unified_outputs": {
            "X": list(X.shape),
            "y": list(y.shape),
            "meta": [len(meta_df), len(meta_df.columns)],
        },
        "note": "DE features are exposed with brainda-style meta DataFrame for downstream CV/evaluation.",
    }
    return X, y, meta_df, unified_meta


def get_seed_unified_dataset_report(
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = "de_comp_4ch_1p5s",
    raw_data_dir: Optional[Union[str, Path]] = None,
    sample_subjects: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """API helper: verify and summarize MetaBCI unified SEED dataset access."""
    brainda_available, brainda_message = check_brainda_available()
    sample_subjects = sample_subjects or [1]

    if not BRAIN_DA_DATASET_AVAILABLE:
        return {
            "success": False,
            "module": "brainda",
            "module_available": brainda_available,
            "module_imported": brainda_available,
            "brainda_message": brainda_message,
            "metabci_unified": False,
            "message": "metabci.brainda BaseDataset is not available in the current environment",
        }

    try:
        dataset = create_seed_emotion_dataset(
            raw_data_dir=raw_data_dir,
            feature_type=feature_type,
            seed_root=seed_root,
        )
        file_check = verify_seed_dataset_files(dataset)
        summary = summarize_seed_dataset(dataset, subjects=sample_subjects)
        _, _, meta_df, unified_meta = load_de_features_unified(
            seed_root=seed_root,
            feature_type=feature_type,
            raw_data_dir=raw_data_dir,
        )

        return {
            "success": True,
            "module": "brainda",
            "module_available": True,
            "module_imported": True,
            "brainda_message": brainda_message,
            "metabci_unified": True,
            "message": "SEED emotion dataset is accessible through MetaBCI BaseDataset.get_data()",
            "dataset": summary,
            "file_check": file_check,
            "de_feature_meta_preview": meta_df.head(5).to_dict(orient="records"),
            "unified_meta": unified_meta,
            "usage_example": {
                "python": (
                    "from metabci_integration.brainda_seed_dataset import create_seed_emotion_dataset\n"
                    "dataset = create_seed_emotion_dataset()\n"
                    "raw = dataset.get_data(subjects=[1])"
                ),
            },
        }
    except Exception as exc:
        return {
            "success": False,
            "module": "brainda",
            "module_available": brainda_available,
            "module_imported": brainda_available,
            "brainda_message": brainda_message,
            "metabci_unified": False,
            "message": f"MetaBCI unified dataset verification failed: {exc}",
        }
