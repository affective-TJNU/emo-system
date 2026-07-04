"""brainda LOSO split helpers using MetaBCI cross-validation APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np


def _check_brainda_available() -> Tuple[bool, str]:
    try:
        import metabci.brainda  # noqa: F401
        return True, "metabci.brainda imported"
    except Exception as exc:
        return False, str(exc)


def _manual_loso_indices(
    subject_count: int,
    held_out_subject: int,
) -> Tuple[List[int], List[int]]:
    train_subjects = [idx for idx in range(subject_count) if idx != held_out_subject]
    test_subjects = [held_out_subject]
    return train_subjects, test_subjects


def generate_loso_indices(subject_count: int, held_out_subject: int) -> Tuple[List[int], List[int], Dict[str, Any]]:
    """Generate LOSO indices using brainda EnhancedLeaveOneGroupOut when available."""
    if subject_count <= 1:
        raise ValueError("LOSO requires at least two subjects")
    if held_out_subject < 0 or held_out_subject >= subject_count:
        raise ValueError(
            f"held_out_subject {held_out_subject} out of range [0, {subject_count - 1}]"
        )

    brainda_available, brainda_message = _check_brainda_available()
    splitter_name = "manual_loso_subject_splitter"
    train_subjects: List[int]
    test_subjects: List[int]

    if brainda_available:
        try:
            from metabci.brainda.algorithms.utils.model_selection import EnhancedLeaveOneGroupOut

            X = np.arange(subject_count, dtype=np.float64).reshape(-1, 1)
            y = np.zeros(subject_count, dtype=np.int64)
            groups = np.arange(subject_count, dtype=np.int64)
            splitter = EnhancedLeaveOneGroupOut(return_validate=False)

            selected_train: List[int] = []
            selected_test: List[int] = []
            for train_idx, test_idx in splitter.split(X, y, groups=groups):
                if held_out_subject in test_idx.tolist():
                    selected_train = train_idx.tolist()
                    selected_test = test_idx.tolist()
                    break

            if selected_train and selected_test:
                train_subjects = selected_train
                test_subjects = selected_test
                splitter_name = "EnhancedLeaveOneGroupOut"
            else:
                train_subjects, test_subjects = _manual_loso_indices(subject_count, held_out_subject)
        except Exception:
            train_subjects, test_subjects = _manual_loso_indices(subject_count, held_out_subject)
    else:
        train_subjects, test_subjects = _manual_loso_indices(subject_count, held_out_subject)

    meta = {
        "splitter": splitter_name,
        "brainda_api": "metabci.brainda.algorithms.utils.model_selection.EnhancedLeaveOneGroupOut",
        "strategy": "LOSO",
        "brainda_available": brainda_available,
        "brainda_message": brainda_message,
        "subject_count": subject_count,
        "held_out_subject": held_out_subject,
        "train_subjects": train_subjects,
        "test_subjects": test_subjects,
        "note": "LOSO subject indices are generated through brainda cross-validation API when available.",
    }
    return train_subjects, test_subjects, meta
