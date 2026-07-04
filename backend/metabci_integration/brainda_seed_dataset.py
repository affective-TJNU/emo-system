"""MetaBCI brainda unified dataset for SEED emotion recognition."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    from mne import create_info
    from mne.io import Raw, RawArray
    from metabci.brainda.datasets.base import BaseDataset
    from metabci.brainda.utils.io import loadmat

    BRAIN_DA_DATASET_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    BaseDataset = object  # type: ignore
    BRAIN_DA_DATASET_AVAILABLE = False


DEFAULT_TRIAL_LABELS = [1, 0, -1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 0, 1, -1]
DEFAULT_CHANNELS = ["AF3", "AF4", "F3", "F4"]
DEFAULT_CHANNEL_INDICES = [1, 17, 3, 19]
DEFAULT_RAW_DATA_DIR = "/home/lihanyue/home/data/Preprocessed_EEG"


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_feature_dir(seed_root: str, feature_type: str) -> Path:
    feature_dir = Path(seed_root) / feature_type
    if feature_dir.exists():
        return feature_dir
    project_dir = _backend_root() / "seed" / feature_type
    if project_dir.exists():
        return project_dir
    raise FileNotFoundError(f"SEED feature directory not found: {feature_dir}")


def _load_metadata(feature_dir: Path) -> Dict[str, Any]:
    metadata_file = feature_dir / "metadata.json"
    if not metadata_file.exists():
        return {}
    return json.loads(metadata_file.read_text(encoding="utf-8"))


def _discover_trial_keys(mat_data: Dict[str, Any]) -> List[str]:
    trial_keys = [
        key
        for key in mat_data.keys()
        if not key.startswith("__") and re.match(r".+_eeg\d+$", key)
    ]
    if not trial_keys:
        raise KeyError("No trial keys matching '*_eegN' were found in SEED mat file")

    return sorted(
        trial_keys,
        key=lambda name: int(re.search(r"(\d+)$", name).group(1)),
    )


class SEEDEmotionDataset(BaseDataset):
    """SEED 15-subject emotion dataset in MetaBCI BaseDataset format.

    Each subject has 3 sessions. Every session contains 15 emotion trials stored
    in Preprocessed_EEG ``{subject}_{session}.mat`` as ``ww_eeg1..15``.
    """

    EVENTS = {
        "positive": (1, (0, 1.5)),
        "neutral": (0, (0, 1.5)),
        "negative": (-1, (0, 1.5)),
    }

    def __init__(
        self,
        raw_data_dir: Optional[Union[str, Path]] = None,
        feature_type: str = "de_comp_4ch_1p5s",
        seed_root: Union[str, Path] = "./seed",
    ):
        if not BRAIN_DA_DATASET_AVAILABLE:
            raise ImportError("metabci.brainda BaseDataset is not available")

        feature_dir = _resolve_feature_dir(str(seed_root), feature_type)
        metadata = _load_metadata(feature_dir)
        self.feature_type = feature_type
        self.seed_root = Path(seed_root)
        self.feature_dir = feature_dir
        self.raw_data_dir = Path(
            raw_data_dir
            or metadata.get("raw_data_dir")
            or DEFAULT_RAW_DATA_DIR
        )
        if not self.raw_data_dir.exists() or not os.access(self.raw_data_dir, os.R_OK):
            fallback = Path(DEFAULT_RAW_DATA_DIR)
            if fallback.exists() and os.access(fallback, os.R_OK):
                self.raw_data_dir = fallback
        self.trial_labels = metadata.get("trial_labels", DEFAULT_TRIAL_LABELS)
        self.channel_indices = metadata.get(
            "channel_indices_seed62", DEFAULT_CHANNEL_INDICES
        )
        channels = metadata.get("channels", DEFAULT_CHANNELS)
        self.session_num = int(metadata.get("session_num", 3))
        self.trial_num = int(metadata.get("exp_num", 15))
        self.srate_value = int(metadata.get("sample_rate", 200))

        super().__init__(
            dataset_code="seed_emotion_4ch",
            subjects=list(range(1, 16)),
            events=self.EVENTS,
            channels=channels,
            srate=self.srate_value,
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
        del force_update, update_path, proxies, verbose
        subject_id = int(subject)
        if subject_id not in self.subjects:
            raise ValueError(f"Invalid subject id: {subject_id}")

        root = Path(path) if path is not None else self.raw_data_dir
        session_paths: List[List[Union[str, Path]]] = []
        for session in range(1, self.session_num + 1):
            mat_file = root / f"{subject_id}_{session}.mat"
            if not mat_file.exists():
                raise FileNotFoundError(f"SEED mat file not found: {mat_file}")
            session_paths.append([mat_file])
        return session_paths

    def _get_single_subject_data(
        self,
        subject: Union[str, int],
        verbose: Optional[Union[bool, str, int]] = None,
    ) -> Dict[str, Dict[str, Raw]]:
        del verbose
        session_paths = self.data_path(subject)
        sessions: Dict[str, Dict[str, Raw]] = {}

        for session_idx, run_paths in enumerate(session_paths, start=1):
            mat_file = Path(run_paths[0])
            mat_data = loadmat(mat_file)
            runs: Dict[str, Raw] = {}
            trial_keys = _discover_trial_keys(mat_data)

            for trial_idx, trial_key in enumerate(trial_keys, start=1):
                trial_array = np.asarray(mat_data[trial_key], dtype=np.float64)
                picked = trial_array[self.channel_indices, :]
                data_volts = picked * 1e-6

                info = create_info(
                    ch_names=[ch.upper() for ch in self.channels],
                    ch_types=["eeg"] * len(self.channels),
                    sfreq=self.srate,
                )
                raw = RawArray(data_volts, info=info, verbose=False)
                label = int(
                    self.trial_labels[trial_idx - 1]
                    if trial_idx - 1 < len(self.trial_labels)
                    else 0
                )
                duration = picked.shape[1] / float(self.srate)
                raw.set_annotations(
                    mne_annotations(
                        onset=[0.0],
                        duration=[duration],
                        description=[str(label)],
                    )
                )
                runs[f"trial_{trial_idx}"] = raw

            sessions[f"session_{session_idx}"] = runs

        return sessions


def mne_annotations(onset, duration, description):
    from mne import Annotations

    return Annotations(onset=onset, duration=duration, description=description)


def create_seed_emotion_dataset(
    raw_data_dir: Optional[Union[str, Path]] = None,
    feature_type: str = "de_comp_4ch_1p5s",
    seed_root: Union[str, Path] = "./seed",
) -> SEEDEmotionDataset:
    return SEEDEmotionDataset(
        raw_data_dir=raw_data_dir,
        feature_type=feature_type,
        seed_root=seed_root,
    )


def summarize_seed_dataset(
    dataset: SEEDEmotionDataset,
    subjects: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Return a JSON-friendly summary of the unified dataset."""
    subjects = subjects or [1]
    subject_raw = dataset.get_data(subjects=subjects)
    first_subject = subjects[0]
    first_sessions = subject_raw[first_subject]
    first_session_key = next(iter(first_sessions.keys()))
    first_run_key = next(iter(first_sessions[first_session_key].keys()))
    first_raw = first_sessions[first_session_key][first_run_key]

    return {
        "dataset_code": dataset.dataset_code,
        "paradigm": dataset.paradigm,
        "subjects": len(dataset.subjects),
        "sessions_per_subject": dataset.session_num,
        "trials_per_session": dataset.trial_num,
        "channels": dataset.channels,
        "srate": dataset.srate,
        "events": dataset.events,
        "raw_data_dir": str(dataset.raw_data_dir),
        "feature_dir": str(dataset.feature_dir),
        "structure": "{subject: {session: {run: mne.io.Raw}}}",
        "sample_subject": first_subject,
        "sample_session": first_session_key,
        "sample_run": first_run_key,
        "sample_shape": list(first_raw.get_data().shape),
        "metabci_unified": True,
    }


def verify_seed_dataset_files(dataset: SEEDEmotionDataset) -> Dict[str, Any]:
    """Check whether all subject/session mat files exist."""
    missing: List[str] = []
    available = 0
    for subject in dataset.subjects:
        try:
            dataset.data_path(subject)
            available += 1
        except FileNotFoundError as exc:
            missing.append(str(exc))

    return {
        "subject_count": len(dataset.subjects),
        "available_subjects": available,
        "missing_messages": missing[:5],
        "raw_data_complete": len(missing) == 0,
    }
