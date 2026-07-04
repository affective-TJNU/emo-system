"""Device source abstraction for brainflow online inference.

Supports SEED replay (default) and reserved Neuroscan 40-channel acquisition paths.
Without real hardware, ``neuroscan_sim`` synthesizes a 40-ch window then picks the
SEED-aligned key channels (AF3/AF4/F3/F4) before ATGRNet inference.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Typical Neuroscan / extended 10-20 40-channel montage (competition/demo layout).
NEUROSCAN_40_CHANNELS: List[str] = [
    "Fp1", "Fpz", "Fp2", "AF3", "AF4",
    "F7", "F3", "Fz", "F4", "F8",
    "FC5", "FC1", "FC2", "FC6",
    "T7", "C3", "Cz", "C4", "T8",
    "CP5", "CP1", "CP2", "CP6",
    "P7", "P3", "Pz", "P4", "P8",
    "PO7", "PO3", "PO4", "PO8",
    "O1", "Oz", "O2",
    "FT9", "FT10", "TP9", "TP10", "Cz2",
]

# SEED 4-ch roles mapped to Neuroscan 40-ch cap indices (0-based).
KEY_CHANNEL_MAP: Dict[str, Dict[str, Any]] = {
    "AF3": {"cap_index": 3, "seed_role": "AF3"},
    "AF4": {"cap_index": 4, "seed_role": "AF4"},
    "F3": {"cap_index": 6, "seed_role": "F3"},
    "F4": {"cap_index": 8, "seed_role": "F4"},
}

KEY_CHANNEL_ORDER: List[str] = ["AF3", "AF4", "F3", "F4"]

SUPPORTED_DEVICE_SOURCES: Dict[str, Dict[str, str]] = {
    "seed_replay": {
        "label": "SEED 全被试 DE 回放",
        "description": "Use cached SEED DE tensors for ATGRNet online replay (default).",
        "hardware_required": "false",
    },
    "neuroscan_sim": {
        "label": "Neuroscan 40 导模拟采集",
        "description": "Simulate 40-ch Neuroscan stream, pick AF3/AF4/F3/F4, then run ATGRNet.",
        "hardware_required": "false",
    },
    "neuroscan_lsl": {
        "label": "Neuroscan 40 导 LSL 接入（预留）",
        "description": "Resolve LSL EEG stream named like Neuroscan; fallback to sim when unavailable.",
        "hardware_required": "true",
    },
}


def normalize_device_source(device_source: Optional[str]) -> str:
    key = (device_source or "seed_replay").strip().lower()
    if key in SUPPORTED_DEVICE_SOURCES:
        return key
    legacy = {
        "simulated_replay": "seed_replay",
        "seed_segment_replay": "seed_replay",
        "atgrnet_all_subjects_replay": "seed_replay",
        "neuroscan": "neuroscan_sim",
    }
    return legacy.get(key, "seed_replay")


def get_device_source_catalog() -> Dict[str, Any]:
    """Return device sources for API / competition documentation."""
    lsl_ok, lsl_msg = probe_neuroscan_lsl()
    catalog = []
    for source_id, meta in SUPPORTED_DEVICE_SOURCES.items():
        entry = {"id": source_id, **meta}
        if source_id == "neuroscan_lsl":
            entry["lsl_available"] = lsl_ok
            entry["lsl_message"] = lsl_msg
        catalog.append(entry)
    return {
        "device_vendor": "Neuroscan",
        "cap_channels": len(NEUROSCAN_40_CHANNELS),
        "key_channels": KEY_CHANNEL_ORDER,
        "key_channel_map": KEY_CHANNEL_MAP,
        "sampling_rate_default": 200,
        "window_seconds_default": 1.5,
        "sources": catalog,
        "pipeline_note": (
            "40-ch raw EEG -> key channel pick (AF3/AF4/F3/F4) -> DE/ATGRNet features -> "
            "brainflow ProcessWorker -> Web visualization"
        ),
    }


def probe_neuroscan_lsl(stream_name: str = "Neuroscan") -> Tuple[bool, str]:
    """Check whether pylsl is importable (real cap needs an LSL outlet)."""
    try:
        import pylsl  # noqa: F401

        return True, "pylsl available; connect Neuroscan LSL outlet to enable neuroscan_lsl"
    except Exception as exc:
        return False, f"pylsl unavailable: {exc}"


def resolve_lsl_stream(stream_name: str = "Neuroscan", timeout: float = 1.0) -> Tuple[Optional[Any], str]:
    """Resolve an active LSL EEG stream by name/type substring."""
    try:
        from pylsl import StreamInlet, resolve_byprop
    except Exception as exc:
        return None, f"pylsl unavailable: {exc}"

    wait_time = max(0.1, min(timeout, 2.0))
    try:
        streams = resolve_byprop("type", "EEG", minimum=1, timeout=wait_time)
        if not streams:
            streams = resolve_byprop("name", stream_name, minimum=1, timeout=wait_time)
    except Exception as exc:
        return None, f"resolve_byprop failed: {exc}"

    if not streams:
        return None, "no active LSL streams found"

    needle = (stream_name or "Neuroscan").strip().lower()
    candidates = []
    for info in streams:
        name = (info.name() or "").lower()
        stype = (info.type() or "").lower()
        if needle in name or needle in stype or "eeg" in stype:
            candidates.append(info)

    if not candidates:
        return None, f"no LSL stream matching '{stream_name}' (found {len(streams)} other stream(s))"

    info = candidates[0]
    try:
        inlet = StreamInlet(info, max_buflen=360)
        return inlet, f"resolved LSL stream '{info.name()}' type={info.type()}"
    except Exception as exc:
        return None, f"StreamInlet failed: {exc}"


def pick_key_channels_from_40ch(raw_40: np.ndarray) -> np.ndarray:
    """Pick SEED key channels from a (40, T) or (T, 40) Neuroscan window."""
    arr = np.asarray(raw_40, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D 40-ch window, got shape {arr.shape}")
    if arr.shape[0] == len(NEUROSCAN_40_CHANNELS):
        cap = arr
    elif arr.shape[1] == len(NEUROSCAN_40_CHANNELS):
        cap = arr.T
    else:
        raise ValueError(f"40-ch window shape mismatch: {arr.shape}")

    picked = np.stack([cap[KEY_CHANNEL_MAP[name]["cap_index"]] for name in KEY_CHANNEL_ORDER], axis=0)
    return picked


def simulate_neuroscan_window_from_features(
    sample: np.ndarray,
    *,
    window_samples: int = 300,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Build a synthetic (40, T) cap window from a 4-ch DE/feature sample.

    Used when no real Neuroscan is connected. Key cap electrodes carry signal
    derived from the replay sample; other electrodes carry low-amplitude noise.
    """
    rng = rng or np.random.default_rng(42)
    sample_arr = np.asarray(sample, dtype=np.float64)

    cap = rng.normal(0.0, 0.05, size=(len(NEUROSCAN_40_CHANNELS), window_samples))

    if sample_arr.ndim == 3 and sample_arr.shape[0] == 4:
        # Trial tensor (4, segments, bands): use first segment band energy as proxy waveform.
        proxy = sample_arr[:, 0, :].mean(axis=-1, keepdims=True)
        wave = np.tile(proxy, (1, window_samples)) + rng.normal(0, 0.02, size=(4, window_samples))
        for ch_idx, name in enumerate(KEY_CHANNEL_ORDER):
            cap[KEY_CHANNEL_MAP[name]["cap_index"]] = wave[ch_idx]
    elif sample_arr.ndim == 2 and sample_arr.shape[0] == 4:
        proxy = sample_arr.mean(axis=-1, keepdims=True)
        wave = np.tile(proxy, (1, window_samples)) + rng.normal(0, 0.02, size=(4, window_samples))
        for ch_idx, name in enumerate(KEY_CHANNEL_ORDER):
            cap[KEY_CHANNEL_MAP[name]["cap_index"]] = wave[ch_idx]
    else:
        flat = sample_arr.reshape(-1)
        base = float(np.tanh(flat[: min(40, flat.size)].mean())) if flat.size else 0.0
        wave = base + rng.normal(0, 0.03, size=window_samples)
        for name in KEY_CHANNEL_ORDER:
            cap[KEY_CHANNEL_MAP[name]["cap_index"]] = wave

    picked = pick_key_channels_from_40ch(cap)
    return cap, picked


def resolve_runtime_device_source(requested: Optional[str]) -> Tuple[str, bool, str]:
    """Resolve requested source; LSL falls back to simulation when no stream."""
    source = normalize_device_source(requested)
    if source != "neuroscan_lsl":
        return source, False, ""

    stream, stream_msg = resolve_lsl_stream("Neuroscan", timeout=1.0)
    if stream is not None:
        return "neuroscan_lsl", False, stream_msg

    lsl_ok, lsl_msg = probe_neuroscan_lsl()
    if not lsl_ok:
        return "neuroscan_sim", True, lsl_msg
    return "neuroscan_sim", True, f"{stream_msg or lsl_msg}; using neuroscan_sim fallback"


def build_device_frame_metadata(
    *,
    device_source: str,
    lsl_fallback: bool,
    lsl_message: str,
    raw_cap: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    meta = {
        "device_source": device_source,
        "device_vendor": "Neuroscan",
        "device_channel_count": len(NEUROSCAN_40_CHANNELS),
        "device_key_channels": KEY_CHANNEL_ORDER,
        "device_key_indices": [KEY_CHANNEL_MAP[n]["cap_index"] for n in KEY_CHANNEL_ORDER],
        "lsl_fallback": bool(lsl_fallback),
        "lsl_message": lsl_message or "",
    }
    if raw_cap is not None:
        meta["device_raw_shape"] = list(raw_cap.shape)
    return meta

