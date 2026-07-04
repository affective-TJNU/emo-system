# -*- coding: utf-8 -*-
"""
SEED emotion dataset loader for MetaBCI brainda.

Loads preprocessed SEED `.mat` trials, converts them to MNE Raw objects with
emotion annotations, and supports sliding 1.5 s windows for competition eval.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, cast

import mne
import numpy as np
import scipy.io as sio
from mne.io import Raw

from .base import BaseDataset

# Official SEED 62-channel montage (10-20 extension)
SEED_CHANNELS = [
    "FP1", "FPZ", "FP2", "AF3", "AF4", "F7", "F5", "F3", "F1", "FZ",
    "F2", "F4", "F6", "F8", "FT7", "FC5", "FC3", "FC1", "FCZ", "FC2",
    "FC4", "FC6", "FT8", "T7", "C5", "C3", "C1", "CZ", "C2", "C4",
    "C6", "T8", "TP7", "CP5", "CP3", "CP1", "CPZ", "CP2", "CP4", "CP6",
    "TP8", "P7", "P5", "P3", "P1", "PZ", "P2", "P4", "P6", "P8",
    "PO7", "PO5", "PO3", "POZ", "PO4", "PO6", "PO8", "CB1", "O1", "OZ",
    "O2", "CB2",
]

# SEED label encoding: -1 negative, 0 neutral, 1 positive
SEED_LABEL_NAMES = {
    -1: "negative",
    0: "neutral",
    1: "positive",
}

DEFAULT_SEED_ROOT = Path(
    os.environ.get("SEED_PATH", "./data/SEED")
)


def _load_seed_labels(seed_root: Path) -> np.ndarray:
    """Load the 15 trial labels shared by SEED preprocessed EEG."""
    candidates = [
        seed_root / "ExtractedFeatures" / "label.mat",
        seed_root / "data_label" / "label.mat",
        seed_root / "label.mat",
    ]
    for label_path in candidates:
        if label_path.exists():
            mat = sio.loadmat(str(label_path))
            if "label" in mat:
                return mat["label"].reshape(-1).astype(int)
    raise FileNotFoundError(
        "Cannot find SEED label.mat under ExtractedFeatures/ or data_label/."
    )


def _trial_keys(mat: dict) -> List[str]:
    keys = [k for k in mat.keys() if not k.startswith("_")]
    keys.sort(key=lambda name: int("".join(ch for ch in name if ch.isdigit()) or 0))
    if len(keys) != 15:
        raise ValueError(f"Expected 15 trials in mat file, got {len(keys)}: {keys}")
    return keys


def _label_to_event_id(label: int) -> int:
    return int(label)


def add_sliding_annotations(
    raw: Raw,
    label: int,
    window_sec: float = 1.5,
    step_sec: float = 1.5,
) -> Raw:
    """Add non-overlapping window onset annotations on a continuous trial."""
    duration = raw.n_times / raw.info["sfreq"]
    onsets = np.arange(0.0, duration - window_sec + 1e-6, step_sec)
    if len(onsets) == 0:
        onsets = np.array([0.0])

    descriptions = [str(_label_to_event_id(label))] * len(onsets)
    annotations = mne.Annotations(
        onset=onsets,
        duration=[window_sec] * len(onsets),
        description=descriptions,
    )
    raw.set_annotations(annotations)
    return raw


def mat_trial_to_raw(
    trial_data: np.ndarray,
    label: int,
    srate: int = 200,
    window_sec: float = 1.5,
    step_sec: float = 1.5,
) -> Raw:
    """Convert one SEED trial array (channels x time) to annotated MNE Raw."""
    info = mne.create_info(
        ch_names=SEED_CHANNELS,
        sfreq=srate,
        ch_types="eeg",
    )
    raw = mne.io.RawArray(trial_data.astype(np.float64), info, verbose=False)
    raw = add_sliding_annotations(raw, label, window_sec=window_sec, step_sec=step_sec)
    return raw


class SEED(BaseDataset):
    """SEED emotion dataset (preprocessed EEG, 15 subjects x 3 sessions)."""

    _EVENTS = {
        "negative": (-1, (0, 1.5)),
        "neutral": (0, (0, 1.5)),
        "positive": (1, (0, 1.5)),
    }

    def __init__(
        self,
        seed_root: Optional[Union[str, Path]] = None,
        window_sec: float = 1.5,
        step_sec: float = 1.5,
    ):
        self.seed_root = Path(seed_root) if seed_root else DEFAULT_SEED_ROOT
        self.preprocessed_dir = self.seed_root / "Preprocessed_EEG"
        self.window_sec = window_sec
        self.step_sec = step_sec
        self._labels = _load_seed_labels(self.seed_root)

        super().__init__(
            dataset_code="seed",
            subjects=list(range(1, 16)),
            events=self._EVENTS,
            channels=SEED_CHANNELS,
            srate=200,
            paradigm="emotion",
        )

    def data_path(
        self,
        subject: Union[str, int],
        path: Optional[Union[str, Path]] = None,
        force_update: bool = False,
        update_path: Optional[bool] = None,
        proxies: Optional[Dict[str, str]] = None,
        verbose: Optional[Union[bool, str, int]] = None,
    ) -> List[List[Union[str, Path]]]:
        if subject not in self.subjects:
            raise ValueError(f"Invalid subject id: {subject}")
        subject = cast(int, subject)

        if not self.preprocessed_dir.exists():
            raise FileNotFoundError(
                f"SEED preprocessed directory not found: {self.preprocessed_dir}"
            )

        sessions: List[List[Union[str, Path]]] = []
        for session in range(1, 4):
            mat_path = self.preprocessed_dir / f"{subject}_{session}.mat"
            if not mat_path.exists():
                raise FileNotFoundError(f"Missing SEED file: {mat_path}")
            sessions.append([mat_path])
        return sessions

    def _get_single_subject_data(
        self,
        subject: Union[str, int],
        verbose: Optional[Union[bool, str, int]] = None,
    ) -> Dict[str, Dict[str, Raw]]:
        subject = cast(int, subject)
        dests = self.data_path(subject)
        sess: Dict[str, Dict[str, Raw]] = {}

        for isess, session_files in enumerate(dests, start=1):
            mat_path = session_files[0]
            mat = sio.loadmat(str(mat_path))
            trial_keys = _trial_keys(mat)
            runs: Dict[str, Raw] = {}

            for trial_idx, key in enumerate(trial_keys):
                label = int(self._labels[trial_idx])
                raw = mat_trial_to_raw(
                    mat[key],
                    label=label,
                    srate=self.srate,
                    window_sec=self.window_sec,
                    step_sec=self.step_sec,
                )
                runs[f"trial_{trial_idx + 1:02d}"] = raw

            sess[f"session_{isess}"] = runs
        return sess
