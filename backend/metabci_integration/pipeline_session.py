"""Cross-step pipeline session: SEED offline vs Neuroscan live acquisition."""

from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

ACQUISITION_MODES: Dict[str, Dict[str, str]] = {
    "seed_offline": {
        "label": "SEED 数据集演示",
        "dataset_label": "SEED 数据集",
        "dataset_type": "seed",
        "description": "无电极帽：brainda 预处理 SEED DE 特征 → 训练 → seed_replay 在线推理",
        "device_source": "seed_replay",
        "data_source": "seed",
        "requires_hardware": "false",
    },
    "neuroscan_live": {
        "label": "Neuroscan 实时采集",
        "dataset_label": "自采数据集",
        "dataset_type": "self_collected",
        "description": "有电极帽：实验范式 + LSL 40 导采集 → 原始数据 DE 提取 → brainflow 推理",
        "device_source": "neuroscan_lsl",
        "data_source": "live",
        "requires_hardware": "true",
    },
}

_DEFAULT_MODE = "seed_offline"
_lock = Lock()
_session: Dict[str, Any] = {
    "acquisition_mode": _DEFAULT_MODE,
    "device_source": ACQUISITION_MODES[_DEFAULT_MODE]["device_source"],
    "data_source": ACQUISITION_MODES[_DEFAULT_MODE]["data_source"],
    "live_probe": None,
    "preprocess_done": False,
    "feature_learning_mode": "train",
    "updated_at": datetime.now().isoformat(),
}


def normalize_acquisition_mode(mode: Optional[str]) -> str:
    key = (mode or _DEFAULT_MODE).strip().lower()
    if key in ACQUISITION_MODES:
        return key
    legacy = {
        "seed": "seed_offline",
        "offline": "seed_offline",
        "live": "neuroscan_live",
        "neuroscan": "neuroscan_live",
        "hardware": "neuroscan_live",
    }
    return legacy.get(key, _DEFAULT_MODE)


def device_source_for_mode(mode: Optional[str]) -> str:
    normalized = normalize_acquisition_mode(mode)
    return ACQUISITION_MODES[normalized]["device_source"]


def _session_payload_unlocked() -> Dict[str, Any]:
    payload = dict(_session)
    payload["modes"] = [
        {"id": mode_id, **meta} for mode_id, meta in ACQUISITION_MODES.items()
    ]
    payload["is_live_mode"] = payload["acquisition_mode"] == "neuroscan_live"
    return payload


def get_pipeline_session() -> Dict[str, Any]:
    with _lock:
        return _session_payload_unlocked()


def update_pipeline_session(
    *,
    acquisition_mode: Optional[str] = None,
    live_probe: Optional[Dict[str, Any]] = None,
    preprocess_done: Optional[bool] = None,
    feature_learning_mode: Optional[str] = None,
) -> Dict[str, Any]:
    with _lock:
        if acquisition_mode is not None:
            mode = normalize_acquisition_mode(acquisition_mode)
            _session["acquisition_mode"] = mode
            _session["device_source"] = device_source_for_mode(mode)
            _session["data_source"] = ACQUISITION_MODES[mode]["data_source"]
            if mode == "seed_offline":
                _session["live_probe"] = None
                _session["feature_learning_mode"] = "train"
        if live_probe is not None:
            _session["live_probe"] = live_probe
        if preprocess_done is not None:
            _session["preprocess_done"] = bool(preprocess_done)
        if feature_learning_mode is not None:
            _session["feature_learning_mode"] = feature_learning_mode
        _session["updated_at"] = datetime.now().isoformat()
        return _session_payload_unlocked()


def reset_pipeline_session() -> Dict[str, Any]:
    with _lock:
        _session.clear()
        _session.update(
            {
                "acquisition_mode": _DEFAULT_MODE,
                "device_source": device_source_for_mode(_DEFAULT_MODE),
                "data_source": ACQUISITION_MODES[_DEFAULT_MODE]["data_source"],
                "live_probe": None,
                "preprocess_done": False,
                "feature_learning_mode": "train",
                "updated_at": datetime.now().isoformat(),
            }
        )
        return _session_payload_unlocked()
