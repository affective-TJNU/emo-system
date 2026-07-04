"""Neuroscan 40-ch LSL live acquisition and DE feature extraction (aligned with brainda_raw_to_de)."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

from .brainda_raw_to_de import (
    SELF_COLLECTED_ROOT,
    compute_de_segment,
    save_self_collected_de_features,
    trial_to_de_tensor,
)
from .device_sources import (
    KEY_CHANNEL_MAP,
    KEY_CHANNEL_ORDER,
    NEUROSCAN_40_CHANNELS,
    build_device_frame_metadata,
    pick_key_channels_from_40ch,
    probe_neuroscan_lsl,
    resolve_lsl_stream,
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLING_RATE = 200
DEFAULT_WINDOW_SECONDS = 1.5
DEFAULT_FEATURE_TYPE = "de_comp_4ch_1p5s"


class NeuroscanLiveAcquisition:
    """Thread-safe LSL inlet with ring buffer for 40-ch Neuroscan cap."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._inlet: Any = None
        self._stream_info: Dict[str, Any] = {}
        self._buffer: Deque[np.ndarray] = deque(maxlen=4000)
        self._channel_count = len(NEUROSCAN_40_CHANNELS)
        self._sampling_rate = DEFAULT_SAMPLING_RATE
        self._connected = False
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_marker: Optional[int] = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def stream_info(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._stream_info)

    def probe(self, stream_name: str = "Neuroscan") -> Dict[str, Any]:
        """Probe LSL without starting acquisition."""
        lsl_ok, lsl_msg = probe_neuroscan_lsl(stream_name)
        stream, stream_msg = resolve_lsl_stream(stream_name, timeout=1.0)
        payload: Dict[str, Any] = {
            "success": True,
            "pylsl_available": lsl_ok,
            "pylsl_message": lsl_msg,
            "stream_found": stream is not None,
            "stream_message": stream_msg,
            "cap_channels": len(NEUROSCAN_40_CHANNELS),
            "key_channels": KEY_CHANNEL_ORDER,
            "sampling_rate_default": DEFAULT_SAMPLING_RATE,
            "window_seconds_default": DEFAULT_WINDOW_SECONDS,
            "timestamp": datetime.now().isoformat(),
        }
        if stream is not None:
            try:
                info = stream.info()
                payload["stream_name"] = info.name()
                payload["stream_type"] = info.type()
                payload["channel_count"] = info.channel_count()
                payload["nominal_srate"] = info.nominal_srate()
            except Exception as exc:
                payload["stream_parse_error"] = str(exc)
        return payload

    def connect(self, stream_name: str = "Neuroscan", timeout: float = 3.0) -> Tuple[bool, str]:
        with self._lock:
            if self._connected:
                return True, "already connected"

        stream, msg = resolve_lsl_stream(stream_name, timeout=timeout)
        if stream is None:
            return False, msg

        try:
            inlet = stream
            info = inlet.info()
            channel_count = int(info.channel_count())
            srate = float(info.nominal_srate() or DEFAULT_SAMPLING_RATE)
            with self._lock:
                self._inlet = inlet
                self._channel_count = channel_count
                self._sampling_rate = srate
                self._stream_info = {
                    "stream_name": info.name(),
                    "stream_type": info.type(),
                    "channel_count": channel_count,
                    "nominal_srate": srate,
                }
                self._buffer.clear()
                self._connected = True
                self._stop_event.clear()
            self._start_reader()
            return True, f"connected to LSL stream '{info.name()}' ({channel_count} ch @ {srate} Hz)"
        except Exception as exc:
            return False, str(exc)

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2.0)
        with self._lock:
            self._inlet = None
            self._connected = False
            self._buffer.clear()

    def _start_reader(self) -> None:
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True, name="neuroscan-lsl")
        self._reader_thread.start()

    def _read_loop(self) -> None:
        while not self._stop_event.is_set():
            inlet = None
            with self._lock:
                inlet = self._inlet
            if inlet is None:
                break
            try:
                sample, _timestamp = inlet.pull_sample(timeout=0.05)
                if sample is None:
                    continue
                arr = np.asarray(sample, dtype=np.float64)
                with self._lock:
                    self._buffer.append(arr)
            except Exception as exc:
                logger.warning("LSL read error: %s", exc)
                time.sleep(0.1)

    def set_marker(self, marker_code: int) -> None:
        with self._lock:
            self._last_marker = int(marker_code)

    @property
    def last_marker(self) -> Optional[int]:
        with self._lock:
            return self._last_marker

    def buffer_samples(self) -> int:
        with self._lock:
            return len(self._buffer)

    def pull_full_buffered_raw(self) -> Optional[np.ndarray]:
        """Return full ring buffer as (n_channels, n_samples) or None if empty."""
        with self._lock:
            if not self._buffer:
                return None
            samples = list(self._buffer)
        window = np.stack(samples, axis=1)
        if window.shape[0] not in (len(NEUROSCAN_40_CHANNELS), window.shape[1]):
            if window.shape[1] in (len(NEUROSCAN_40_CHANNELS), 40, 32, 64):
                window = window.T
        return window

    def pull_raw_window(
        self,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        sampling_rate: Optional[int] = None,
    ) -> Optional[np.ndarray]:
        """Return (n_channels, window_samples) raw window or None if insufficient data."""
        srate = int(sampling_rate or self._sampling_rate or DEFAULT_SAMPLING_RATE)
        need = max(1, int(window_seconds * srate))
        with self._lock:
            if len(self._buffer) < need:
                return None
            samples = list(self._buffer)[-need:]
            window = np.stack(samples, axis=1)
        if window.shape[0] not in (len(NEUROSCAN_40_CHANNELS), window.shape[1]):
            if window.shape[1] in (len(NEUROSCAN_40_CHANNELS), 40, 32, 64):
                window = window.T
        return window

    def pull_de_tensor(
        self,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        sampling_rate: Optional[int] = None,
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """Build (4, 1, 5) DE tensor from latest live window."""
        srate = int(sampling_rate or self._sampling_rate or DEFAULT_SAMPLING_RATE)
        window = self.pull_raw_window(window_seconds, srate)
        meta = build_device_frame_metadata(
            device_source="neuroscan_lsl",
            lsl_fallback=False,
            lsl_message="live LSL stream",
            raw_cap=window,
        )
        meta["buffer_samples"] = self.buffer_samples()
        meta["last_marker"] = self._last_marker
        if window is None:
            meta["waiting"] = True
            return None, meta

        try:
            if window.shape[0] >= len(NEUROSCAN_40_CHANNELS):
                cap = window[: len(NEUROSCAN_40_CHANNELS)]
            elif window.shape[0] == 4:
                picked = window
                de = compute_de_segment(picked, sampling_rate=srate)
                tensor = de.reshape(4, 1, de.shape[1])
                meta["de_shape"] = list(tensor.shape)
                return tensor.astype(np.float32), meta
            else:
                cap = window
            picked = pick_key_channels_from_40ch(cap)
        except Exception as exc:
            meta["pick_error"] = str(exc)
            if window.shape[0] >= 4:
                picked = window[:4]
            else:
                return None, meta

        de = compute_de_segment(picked, sampling_rate=srate)
        tensor = de.reshape(picked.shape[0], 1, de.shape[1])
        meta["de_shape"] = list(tensor.shape)
        meta["waiting"] = False
        return tensor.astype(np.float32), meta


live_acquisition = NeuroscanLiveAcquisition()


def check_neuroscan_device_connection(
    stream_name: str = "Neuroscan",
    *,
    try_connect: bool = True,
) -> Dict[str, Any]:
    """Probe Neuroscan LSL without running DE preprocessing."""
    probe = live_acquisition.probe(stream_name)
    connected = bool(live_acquisition.connected)
    connect_msg = ""

    if try_connect and probe.get("stream_found") and not connected:
        connected, connect_msg = live_acquisition.connect(stream_name)
    elif connected:
        connect_msg = "LSL 已连接"
    elif probe.get("stream_found"):
        connect_msg = str(probe.get("stream_message") or "检测到 LSL 流但尚未建立连接")
    else:
        connect_msg = str(probe.get("stream_message") or "未检测到 Neuroscan LSL 数据流")

    device_connected = bool(connected)
    if not probe.get("pylsl_available", True):
        device_connected = False
        connect_msg = str(probe.get("pylsl_message") or "pylsl 不可用，无法连接 Neuroscan 设备")

    return {
        "success": True,
        "device_connected": device_connected,
        "stream_found": bool(probe.get("stream_found")),
        "connected": device_connected,
        "pylsl_available": bool(probe.get("pylsl_available")),
        "stream_name": probe.get("stream_name") or stream_name,
        "connect_message": connect_msg,
        "message": (
            "Neuroscan 设备已连接"
            if device_connected
            else "未连接 Neuroscan 设备，请检查电极帽与 LSL 数据流后重试"
        ),
        "cap_channels": probe.get("cap_channels") or len(NEUROSCAN_40_CHANNELS),
        "key_channels": KEY_CHANNEL_ORDER,
        "sampling_rate": probe.get("nominal_srate") or DEFAULT_SAMPLING_RATE,
        "timestamp": datetime.now().isoformat(),
        "probe": probe,
    }


def _synthesize_demo_raw_buffer(
    window_samples: int,
    n_segments: int = 8,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
) -> np.ndarray:
    """Build demo 40-ch continuous raw when LSL buffer is insufficient."""
    rng = np.random.default_rng(42)
    total = window_samples * max(1, n_segments)
    cap = rng.normal(0.0, 0.05, size=(len(NEUROSCAN_40_CHANNELS), total))
    t = np.arange(total, dtype=np.float64) / float(sampling_rate)
    for ch_idx, name in enumerate(KEY_CHANNEL_ORDER):
        wave = 0.35 * np.sin(2.0 * np.pi * (7.0 + ch_idx * 1.5) * t) + rng.normal(0.0, 0.02, size=total)
        cap[KEY_CHANNEL_MAP[name]["cap_index"]] = wave
    return cap


def _raw_to_picked_four_channel(raw: np.ndarray) -> np.ndarray:
    arr = np.asarray(raw, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D raw EEG, got shape {arr.shape}")
    if arr.shape[0] >= len(NEUROSCAN_40_CHANNELS):
        return pick_key_channels_from_40ch(arr[: len(NEUROSCAN_40_CHANNELS)])
    if arr.shape[1] >= len(NEUROSCAN_40_CHANNELS):
        return pick_key_channels_from_40ch(arr[:, : len(NEUROSCAN_40_CHANNELS)].T)
    if arr.shape[0] == 4:
        return arr
    if arr.shape[1] == 4:
        return arr.T
    return arr[:4]


def run_self_collected_de_preprocess(
    stream_name: str = "Neuroscan",
    feature_type: str = DEFAULT_FEATURE_TYPE,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    max_segments: int = 32,
    *,
    require_device: bool = True,
) -> Dict[str, Any]:
    """Step-1 self-collected path: LSL raw buffer -> brainda DE tensors (same as SEED pipeline)."""
    device_status = check_neuroscan_device_connection(stream_name, try_connect=True)
    connected = bool(device_status.get("device_connected"))
    connect_msg = str(device_status.get("connect_message") or "")
    probe = dict(device_status.get("probe") or {})

    if require_device and not connected:
        probe_payload = {
            **probe,
            "connected": False,
            "connect_message": connect_msg,
            "device_connected": False,
        }
        return {
            "success": False,
            "device_connected": False,
            "message": device_status.get("message") or "未连接 Neuroscan 设备",
            "module": "brainda",
            "dataset": "自采数据集",
            "dataset_type": "self_collected",
            "dataset_label": "自采数据集",
            "acquisition_mode": "neuroscan_live",
            "preprocess_mode": "raw_to_de",
            "feature_type": feature_type,
            "live_probe": probe_payload,
            "error_code": "device_not_connected",
        }

    srate = int(
        probe.get("nominal_srate")
        or live_acquisition.stream_info.get("nominal_srate")
        or sampling_rate
    )
    window_samples = max(1, int(window_seconds * srate))

    deadline = time.time() + min(4.0, window_seconds * 3)
    while time.time() < deadline and live_acquisition.buffer_samples() < window_samples:
        time.sleep(0.1)

    raw_full = live_acquisition.pull_full_buffered_raw()
    if raw_full is None or raw_full.shape[1] < window_samples:
        probe_payload = {
            **probe,
            "connected": True,
            "connect_message": connect_msg,
            "device_connected": True,
            "buffer_samples": live_acquisition.buffer_samples(),
        }
        return {
            "success": False,
            "device_connected": True,
            "message": (
                f"设备已连接，但缓冲数据不足（需要至少 {window_samples} 采样点）。"
                "请先完成 Step0 实验范式采集后再启动数据处理。"
            ),
            "module": "brainda",
            "dataset": "自采数据集",
            "dataset_type": "self_collected",
            "dataset_label": "自采数据集",
            "acquisition_mode": "neuroscan_live",
            "preprocess_mode": "raw_to_de",
            "feature_type": feature_type,
            "live_probe": probe_payload,
            "error_code": "insufficient_buffer",
            "metrics": {
                "buffer_samples": live_acquisition.buffer_samples(),
                "required_samples": window_samples,
            },
        }

    picked = _raw_to_picked_four_channel(raw_full)
    n_valid = picked.shape[1] // window_samples
    seg_cap = max(1, min(max_segments, n_valid or 1))
    de, n_valid_segments = trial_to_de_tensor(
        picked,
        channel_indices=[0, 1, 2, 3],
        window_samples=window_samples,
        max_segments=seg_cap,
        sampling_rate=srate,
    )

    marker_label = live_acquisition.last_marker
    label_value = 0 if marker_label is None else max(0, int(marker_label) - 1)
    save_info = save_self_collected_de_features(
        de,
        seed_root=SELF_COLLECTED_ROOT,
        feature_type=feature_type,
        label_value=label_value,
    )

    probe_payload = {
        **probe,
        "connected": True,
        "connect_message": connect_msg,
        "device_connected": True,
        "buffer_samples": live_acquisition.buffer_samples(),
        "used_simulated_raw": False,
    }

    processing_steps = [
        {
            "step": 0,
            "name": "自采原始脑电导入 (LSL / 缓冲)",
            "status": "completed",
        },
        {
            "step": 1,
            "name": "Neuroscan 40导 → 4导关键通道映射",
            "status": "completed",
        },
        {
            "step": 2,
            "name": "brainda compute_de_segment 差分熵提取",
            "status": "completed",
        },
        {
            "step": 3,
            "name": "五频段滤波 + DE 张量构建",
            "status": "completed",
        },
        {
            "step": 4,
            "name": "自采 DE 特征保存 (data.pt / label.pt)",
            "status": "completed",
        },
    ]

    data_shape = save_info.get("data_shape", [1, 1, 1, 4, de.shape[1], 5])
    message = f"自采数据集：已从原始脑电提取 DE 特征（{n_valid_segments} 片段）"

    return {
        "success": True,
        "device_connected": True,
        "message": message,
        "module": "brainda",
        "dataset": "自采数据集",
        "dataset_type": "self_collected",
        "dataset_label": "自采数据集",
        "acquisition_mode": "neuroscan_live",
        "preprocess_mode": "raw_to_de",
        "feature_type": feature_type,
        "de_built_from_raw": True,
        "used_simulated_raw": False,
        "live_probe": probe_payload,
        "processing_steps": processing_steps,
        "de_build_info": save_info,
        "metrics": {
            "source": "brainda_raw_to_de",
            "data_shape": data_shape,
            "label_shape": save_info.get("label_shape", [1, 1, 1]),
            "channels": 4,
            "channel_names": KEY_CHANNEL_ORDER,
            "sampling_rate": srate,
            "window_seconds": window_seconds,
            "segments": int(de.shape[1]),
            "n_valid_segments": int(n_valid_segments),
            "raw_samples": int(raw_full.shape[1]),
            "buffer_samples": live_acquisition.buffer_samples(),
            "last_marker": marker_label,
            "output_dir": save_info.get("output_dir"),
            "used_simulated_raw": False,
        },
        "notes": [
            "自采路径与 SEED 共用 brainda compute_de_segment / trial_to_de_tensor 逻辑。",
            "特征保存至 backend/seed/self_collected/de_comp_4ch_1p5s/。",
        ],
    }


def run_live_preprocess_probe(stream_name: str = "Neuroscan") -> Dict[str, Any]:
    """Backward-compatible alias: full raw->DE preprocess for self-collected data."""
    result = run_self_collected_de_preprocess(stream_name=stream_name)
    result["preprocess_mode"] = "raw_to_de"
    return result
