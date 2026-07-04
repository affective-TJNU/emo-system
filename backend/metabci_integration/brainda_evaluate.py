"""brainda Performance evaluation for SEED emotion LOSO."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from .brainda_loso import generate_loso_indices
from .brainda_unified import load_de_features_unified


def _map_seed_labels_to_class_indices(labels: np.ndarray) -> np.ndarray:
    """Map SEED labels (-1, 0, 1) to class indices (0, 1, 2)."""
    return (labels.astype(int) + 1).astype(int)


def _trial_feature_matrix(data_np: np.ndarray) -> np.ndarray:
    """Return [n_samples, n_features] trial-level feature matrix."""
    # [subject, session, trial, channel, segment, band]
    trial_mean = data_np.mean(axis=4)
    samples: List[np.ndarray] = []
    for subject in range(trial_mean.shape[0]):
        for session in range(trial_mean.shape[1]):
            for trial in range(trial_mean.shape[2]):
                samples.append(trial_mean[subject, session, trial].reshape(-1))
    return np.asarray(samples, dtype=np.float64)


def _trial_label_vector(labels_np: np.ndarray) -> np.ndarray:
    subject_count, session_count, trial_count = labels_np.shape
    values: List[int] = []
    for subject in range(subject_count):
        for session in range(session_count):
            for trial in range(trial_count):
                values.append(int(labels_np[subject, session, trial]))
    return np.asarray(values, dtype=int)


def run_brainda_performance_evaluation(
    config_path: str = "global.config",
    held_out_subject: int = 0,
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = "de_comp_4ch_1p5s",
    estimators_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Evaluate held-out subject predictions with brainda Performance API."""
    try:
        from metabci.brainda.utils.performance import Performance
        from sklearn.linear_model import LogisticRegression
    except Exception as exc:
        return {
            "success": False,
            "module": "brainda",
            "brainda_api": "metabci.brainda.utils.performance.Performance",
            "message": f"brainda Performance unavailable: {exc}",
        }

    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = Path(__file__).resolve().parents[1] / config_file
    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")
    subject_count = int(parser["seed"].get("sub_num", 15))

    X_tensor, y_tensor, meta_df, unified_meta = load_de_features_unified(
        seed_root=seed_root,
        feature_type=feature_type,
    )
    data_np = X_tensor.detach().cpu().numpy()
    labels_np = y_tensor.detach().cpu().numpy()

    train_subjects, test_subjects, split_meta = generate_loso_indices(
        subject_count,
        held_out_subject,
    )

    sample_subjects = np.repeat(
        np.arange(subject_count),
        labels_np.shape[1] * labels_np.shape[2],
    )
    features = _trial_feature_matrix(data_np)
    labels = _trial_label_vector(labels_np)
    mapped_labels = _map_seed_labels_to_class_indices(labels)

    train_mask = np.isin(sample_subjects, train_subjects)
    test_mask = np.isin(sample_subjects, test_subjects)

    if train_mask.sum() == 0 or test_mask.sum() == 0:
        return {
            "success": False,
            "module": "brainda",
            "brainda_api": "metabci.brainda.utils.performance.Performance",
            "message": "LOSO split produced empty train/test sets",
        }

    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(features[train_mask], mapped_labels[train_mask])
    y_pred = classifier.predict(features[test_mask])
    y_true = mapped_labels[test_mask]

    metrics = estimators_list or ["Acc", "bAcc"]
    performance = Performance(estimators_list=metrics)
    results = performance.evaluate(y_true=y_true, y_pred=y_pred)

    return {
        "success": True,
        "module": "brainda",
        "brainda_api": "metabci.brainda.utils.performance.Performance",
        "brainda_function": "Performance.evaluate",
        "strategy": "LOSO",
        "held_out_subject": held_out_subject,
        "train_subjects": train_subjects,
        "test_subjects": test_subjects,
        "sample_count": {
            "train": int(train_mask.sum()),
            "test": int(test_mask.sum()),
        },
        "metrics": results,
        "split_meta": split_meta,
        "unified_meta": unified_meta,
        "message": "brainda Performance.evaluate completed on SEED LOSO trial features",
    }
