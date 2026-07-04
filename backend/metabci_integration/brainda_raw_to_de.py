"""Build SEED 4-channel 1.5s DE tensors from raw Preprocessed_EEG via MetaBCI brainda.

Pipeline (strict brainda entry: ``metabci.brainda.utils.io.loadmat``):
  raw .mat trial (62 ch) -> pick AF3/AF4/F3/F4 -> non-overlapping 1.5s windows
  -> band-pass (5 bands) -> differential entropy -> pad to max_segments
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
from scipy.signal import butter, filtfilt

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DATA_DIR = BACKEND_DIR / "seed" / "Preprocessed_EEG"
SELF_COLLECTED_ROOT = BACKEND_DIR / "seed" / "self_collected"
DEFAULT_FEATURE_TYPE = "de_comp_4ch_1p5s"
DEFAULT_CHANNELS = ["AF3", "AF4", "F3", "F4"]
DEFAULT_CHANNEL_INDICES = [1, 17, 3, 19]
DEFAULT_TRIAL_LABELS = [1, 0, -1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 0, 1, -1]
DEFAULT_BANDS: Dict[str, Tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 14.0),
    "beta": (14.0, 31.0),
    "gamma": (31.0, 50.0),
}


def _brainda_loadmat(mat_file: Path) -> Dict[str, Any]:
    from metabci.brainda.utils.io import loadmat

    return loadmat(mat_file)


def _discover_trial_keys(mat_data: Dict[str, Any]) -> List[str]:
    trial_keys = [
        key
        for key in mat_data.keys()
        if not key.startswith("__") and re.match(r".+_eeg\d+$", key)
    ]
    if not trial_keys:
        raise KeyError(f"No trial keys matching '*_eegN' in {mat_data.keys()}")
    return sorted(trial_keys, key=lambda name: int(re.search(r"(\d+)$", name).group(1)))


def _resolve_raw_dir(raw_data_dir: Optional[Union[str, Path]]) -> Path:
    if raw_data_dir is None:
        candidate = DEFAULT_RAW_DATA_DIR
    else:
        candidate = Path(raw_data_dir)
    if not candidate.is_absolute():
        candidate = (BACKEND_DIR / candidate).resolve()
    if not candidate.exists():
        legacy = Path("/home/lihanyue/home/data/Preprocessed_EEG")
        if legacy.exists():
            return legacy
    return candidate


def _resolve_output_dir(seed_root: Union[str, Path], feature_type: str) -> Path:
    root = Path(seed_root)
    if not root.is_absolute():
        root = (BACKEND_DIR / root).resolve()
    out = root / feature_type
    out.mkdir(parents=True, exist_ok=True)
    return out


def compute_de_segment(
    segment: np.ndarray,
    bands: Dict[str, Tuple[float, float]] = DEFAULT_BANDS,
    sampling_rate: int = 200,
) -> np.ndarray:
    """Compute DE features for one window. segment shape: (n_channels, n_samples)."""
    n_channels = segment.shape[0]
    n_bands = len(bands)
    features = np.zeros((n_channels, n_bands), dtype=np.float32)
    nyquist = sampling_rate / 2.0

    for band_idx, (_, (low, high)) in enumerate(bands.items()):
        lo = max(low / nyquist, 1e-6)
        hi = min(high / nyquist, 0.999)
        if lo >= hi:
            continue
        b, a = butter(4, [lo, hi], btype="band")
        for ch in range(n_channels):
            filtered = filtfilt(b, a, segment[ch].astype(np.float64))
            variance = max(float(np.var(filtered)), 1e-12)
            features[ch, band_idx] = np.float32(0.5 * np.log(2.0 * np.pi * np.e * variance))
    return features


def trial_to_de_tensor(
    trial_array: np.ndarray,
    channel_indices: Sequence[int] = DEFAULT_CHANNEL_INDICES,
    window_samples: int = 300,
    max_segments: int = 176,
    bands: Dict[str, Tuple[float, float]] = DEFAULT_BANDS,
    sampling_rate: int = 200,
) -> Tuple[np.ndarray, int]:
    """Convert one trial (62, T) to (4, max_segments, 5) with zero padding."""
    picked = np.asarray(trial_array, dtype=np.float64)[list(channel_indices), :]
    n_samples = picked.shape[1]
    n_valid = n_samples // window_samples
    de = np.zeros((len(channel_indices), max_segments, len(bands)), dtype=np.float32)

    for seg_idx in range(min(n_valid, max_segments)):
        start = seg_idx * window_samples
        end = start + window_samples
        de[:, seg_idx, :] = compute_de_segment(
            picked[:, start:end],
            bands=bands,
            sampling_rate=sampling_rate,
        )
    return de, n_valid


def _scan_max_segments(
    raw_dir: Path,
    subjects: Sequence[int],
    window_samples: int,
) -> int:
    max_segments = 0
    for subject in subjects:
        for session in (1, 2, 3):
            mat_file = raw_dir / f"{subject}_{session}.mat"
            if not mat_file.exists():
                continue
            mat_data = _brainda_loadmat(mat_file)
            for key in _discover_trial_keys(mat_data):
                trial = np.asarray(mat_data[key])
                max_segments = max(max_segments, trial.shape[1] // window_samples)
    return max(max_segments, 1)


def build_de_features_from_raw(
    raw_data_dir: Optional[Union[str, Path]] = None,
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = DEFAULT_FEATURE_TYPE,
    subjects: Optional[Sequence[int]] = None,
    sampling_rate: int = 200,
    window_seconds: float = 1.5,
    channel_indices: Sequence[int] = DEFAULT_CHANNEL_INDICES,
    trial_labels: Sequence[int] = DEFAULT_TRIAL_LABELS,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
    max_segments: Optional[int] = None,
    save: bool = True,
) -> Dict[str, Any]:
    """Build (15,3,15,4,S,5) DE tensors and labels from Preprocessed_EEG .mat files."""
    from .availability import check_brainda_available

    brainda_ok, brainda_msg = check_brainda_available()
    if not brainda_ok:
        raise RuntimeError(f"metabci.brainda unavailable: {brainda_msg}")

    raw_dir = _resolve_raw_dir(raw_data_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw SEED directory not found: {raw_dir}")

    subject_list = list(subjects) if subjects is not None else list(range(1, 16))
    window_samples = int(round(window_seconds * sampling_rate))
    band_map = bands or DEFAULT_BANDS

    if max_segments is None:
        max_segments = _scan_max_segments(raw_dir, subject_list, window_samples)

    n_sub = len(subject_list)
    n_sess = 3
    n_trial = 15
    n_ch = len(channel_indices)
    n_band = len(band_map)

    data = np.zeros((n_sub, n_sess, n_trial, n_ch, max_segments, n_band), dtype=np.float32)
    labels = np.zeros((n_sub, n_sess, n_trial), dtype=np.int64)
    segment_counts = np.zeros((n_sub, n_sess, n_trial), dtype=np.int32)

    for sub_idx, subject in enumerate(subject_list):
        for sess_idx, session in enumerate((1, 2, 3)):
            mat_file = raw_dir / f"{subject}_{session}.mat"
            if not mat_file.exists():
                raise FileNotFoundError(f"Missing SEED mat file: {mat_file}")
            mat_data = _brainda_loadmat(mat_file)
            trial_keys = _discover_trial_keys(mat_data)
            if len(trial_keys) < n_trial:
                raise ValueError(f"{mat_file} has {len(trial_keys)} trials, expected {n_trial}")

            for trial_idx, trial_key in enumerate(trial_keys[:n_trial]):
                trial_array = np.asarray(mat_data[trial_key])
                de, n_valid = trial_to_de_tensor(
                    trial_array,
                    channel_indices=channel_indices,
                    window_samples=window_samples,
                    max_segments=max_segments,
                    bands=band_map,
                    sampling_rate=sampling_rate,
                )
                data[sub_idx, sess_idx, trial_idx] = de
                segment_counts[sub_idx, sess_idx, trial_idx] = n_valid
                label = int(trial_labels[trial_idx] if trial_idx < len(trial_labels) else 0)
                labels[sub_idx, sess_idx, trial_idx] = label

    data_tensor = torch.from_numpy(data)
    label_tensor = torch.from_numpy(labels)

    output_dir = _resolve_output_dir(seed_root, feature_type)
    meta = {
        "channels": DEFAULT_CHANNELS,
        "channel_indices_seed62": list(channel_indices),
        "window_sec": window_seconds,
        "sample_rate": sampling_rate,
        "window_samples": window_samples,
        "bands": {name: list(freqs) for name, freqs in band_map.items()},
        "feature_type": "DE",
        "max_segments_per_trial": max_segments,
        "data_shape_trial": list(data.shape),
        "label_values": {"negative": -1, "neutral": 0, "positive": 1},
        "trial_labels": list(trial_labels),
        "raw_data_dir": str(raw_dir),
        "pipeline": "brainda_raw_to_de",
        "brainda_api": "metabci.brainda.utils.io.loadmat",
        "segmentation": "non_overlapping_1.5s_pad_to_max",
        "segment_count_min": int(segment_counts.min()),
        "segment_count_max": int(segment_counts.max()),
    }

    paths: Dict[str, str] = {}
    if save:
        data_path = output_dir / "data.pt"
        label_path = output_dir / "label.pt"
        meta_path = output_dir / "metadata.json"
        torch.save(data_tensor, data_path)
        torch.save(label_tensor, label_path)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        paths = {
            "data_path": str(data_path),
            "label_path": str(label_path),
            "meta_path": str(meta_path),
        }
        logger.info(
            "brainda raw->DE saved: shape=%s max_segments=%s -> %s",
            list(data.shape),
            max_segments,
            output_dir,
        )

    return {
        "success": True,
        "module": "brainda",
        "brainda_api": "metabci.brainda.utils.io.loadmat",
        "message": "SEED raw Preprocessed_EEG -> 4ch 1.5s DE features completed",
        "raw_data_dir": str(raw_dir),
        "output_dir": str(output_dir),
        "data_shape": list(data.shape),
        "label_shape": list(labels.shape),
        "max_segments_per_trial": max_segments,
        "segment_count_range": [int(segment_counts.min()), int(segment_counts.max())],
        "channels": DEFAULT_CHANNELS,
        "label_values": sorted({int(v) for v in labels.reshape(-1).tolist()}),
        "paths": paths,
        "metadata": meta,
    }


_BUILD_STATUS: Dict[str, Any] = {
    "state": "idle",
    "message": "No DE build in progress",
    "started_at": None,
    "finished_at": None,
    "output_dir": None,
    "error": None,
}


def get_de_build_status() -> Dict[str, Any]:
    """Return the latest raw->DE build progress for API polling."""
    return dict(_BUILD_STATUS)


def save_self_collected_de_features(
    de_tensor: np.ndarray,
    *,
    seed_root: Optional[Union[str, Path]] = None,
    feature_type: str = DEFAULT_FEATURE_TYPE,
    label_value: int = 0,
) -> Dict[str, Any]:
    """Persist one live/self-collected trial as SEED-compatible (1,1,1,4,S,5) tensors."""
    root = Path(seed_root) if seed_root is not None else SELF_COLLECTED_ROOT
    output_dir = _resolve_output_dir(root, feature_type)
    de = np.asarray(de_tensor, dtype=np.float32)
    if de.ndim != 3 or de.shape[0] != 4 or de.shape[2] != 5:
        raise ValueError(f"Expected DE tensor (4, segments, 5), got {de.shape}")

    data = torch.from_numpy(de).unsqueeze(0).unsqueeze(0).unsqueeze(0)
    labels = torch.tensor([[[int(label_value)]]], dtype=torch.long)
    data_path = output_dir / "data.pt"
    label_path = output_dir / "label.pt"
    torch.save(data, data_path)
    torch.save(labels, label_path)

    return {
        "success": True,
        "output_dir": str(output_dir),
        "data_path": str(data_path),
        "label_path": str(label_path),
        "data_shape": list(data.shape),
        "label_shape": list(labels.shape),
        "segments": int(de.shape[1]),
    }


def de_feature_tensors_exist(
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = DEFAULT_FEATURE_TYPE,
) -> bool:
    """Return True when both data.pt and label.pt exist under seed_root/feature_type."""
    output_dir = _resolve_output_dir(seed_root, feature_type)
    return (output_dir / "data.pt").is_file() and (output_dir / "label.pt").is_file()


def ensure_de_features_from_raw(
    raw_data_dir: Optional[Union[str, Path]] = None,
    seed_root: Union[str, Path] = "./seed",
    feature_type: str = DEFAULT_FEATURE_TYPE,
    rebuild: bool = False,
    **build_kwargs: Any,
) -> Dict[str, Any]:
    """Ensure data.pt/label.pt exist, building from Preprocessed_EEG when missing."""
    output_dir = _resolve_output_dir(seed_root, feature_type)
    data_path = output_dir / "data.pt"
    label_path = output_dir / "label.pt"

    if data_path.exists() and label_path.exists() and not rebuild:
        return {
            "success": True,
            "built": False,
            "message": "SEED DE feature tensors already exist",
            "output_dir": str(output_dir),
            "data_path": str(data_path),
            "label_path": str(label_path),
        }

    global _BUILD_STATUS
    _BUILD_STATUS = {
        "state": "running",
        "message": "Building DE features from Preprocessed_EEG via brainda loadmat",
        "started_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "output_dir": str(output_dir),
        "error": None,
    }
    try:
        result = build_de_features_from_raw(
            raw_data_dir=raw_data_dir,
            seed_root=seed_root,
            feature_type=feature_type,
            save=True,
            **build_kwargs,
        )
        _BUILD_STATUS.update(
            {
                "state": "completed",
                "message": result.get("message", "DE build completed"),
                "finished_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "data_shape": result.get("data_shape"),
            }
        )
        result["built"] = True
        return result
    except Exception as exc:
        _BUILD_STATUS.update(
            {
                "state": "failed",
                "message": str(exc),
                "finished_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "error": str(exc),
            }
        )
        raise
