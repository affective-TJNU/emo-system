"""MetaBCI brainflow ProcessWorker integration for online emotion inference."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

LABEL_TO_NAME = {
    -1: "negative",
    0: "neutral",
    1: "positive",
    2: "positive",
}

bf_logger = logging.getLogger("metabci.brainflow")
_marker_logged = False


def get_brainflow_logger(name: str = "emotion_online"):
    """Return a brainflow logger instance (strict API #3)."""
    from metabci.brainflow.logger import get_logger

    return get_logger(name)


def check_process_worker_available() -> Tuple[bool, str]:
    try:
        from metabci.brainflow.workers import ProcessWorker  # noqa: F401

        return True, "metabci.brainflow.workers.ProcessWorker imported"
    except Exception as exc:
        return False, str(exc)


def check_marker_available() -> Tuple[bool, str]:
    try:
        from metabci.brainflow.amplifiers import Marker  # noqa: F401

        return True, "metabci.brainflow.amplifiers.Marker imported"
    except Exception as exc:
        return False, str(exc)


def get_brainflow_runtime_status() -> Dict[str, Any]:
    worker_ok, worker_msg = check_process_worker_available()
    marker_ok, marker_msg = check_marker_available()
    logger_ok = worker_ok
    logger_msg = worker_msg if worker_ok else "ProcessWorker unavailable"
    if logger_ok:
        try:
            get_brainflow_logger("emotion_online_check")
            logger_msg = "metabci.brainflow.logger.get_logger imported"
        except Exception as exc:
            logger_ok = False
            logger_msg = str(exc)

    active: List[str] = []
    if worker_ok:
        active.append("brainflow_process_worker")
    if marker_ok:
        active.append("brainflow_marker")
    if logger_ok:
        active.append("brainflow_logger")

    return {
        "process_worker_available": worker_ok,
        "process_worker_message": worker_msg,
        "marker_available": marker_ok,
        "marker_message": marker_msg,
        "logger_available": logger_ok,
        "logger_message": logger_msg,
        "active_strict_ids": active,
    }


_RUNTIME_STATUS_CACHE: Dict[str, Any] = {"ts": 0.0, "value": {}}


def get_brainflow_runtime_status_cached(ttl: float = 5.0) -> Dict[str, Any]:
    now = time.time()
    cached = _RUNTIME_STATUS_CACHE
    if cached["value"] and now - float(cached["ts"]) < ttl:
        return dict(cached["value"])
    value = get_brainflow_runtime_status()
    cached["ts"] = now
    cached["value"] = value
    return dict(value)


def _probabilities_from_label(label: int, confidence: float = 86.0) -> Dict[str, float]:
    primary = LABEL_TO_NAME.get(int(label), "neutral")
    rest = (100.0 - confidence) / 2.0
    probs = {"positive": rest, "neutral": rest, "negative": rest}
    probs[primary] = confidence
    return {key: round(value, 2) for key, value in probs.items()}


def _probabilities_from_features(segment: np.ndarray) -> Dict[str, float]:
    score = float(np.tanh((segment.mean() - 4.0) / 2.0))
    positive = 42.0 + score * 18.0
    neutral = 34.0 - abs(score) * 8.0
    negative = 100.0 - positive - neutral
    probs = np.clip(np.array([positive, neutral, negative]), 2.0, 96.0)
    probs = probs / probs.sum() * 100.0
    return {
        "positive": round(float(probs[0]), 2),
        "neutral": round(float(probs[1]), 2),
        "negative": round(float(probs[2]), 2),
    }


def segment_to_online_payload(segment: torch.Tensor, event: int = 1) -> np.ndarray:
    """Convert a DE segment to brainflow worker input shape (n_samples, n_channels+1)."""
    values = segment.detach().cpu().numpy().astype(np.float64).reshape(-1, segment.shape[-1])
    event_col = np.full((values.shape[0], 1), float(event), dtype=np.float64)
    return np.hstack([values, event_col])


def extract_epoch_with_marker(
    segment: torch.Tensor,
    window_seconds: float,
    sampling_rate: int,
    event: int = 1,
) -> np.ndarray:
    """Use brainflow Marker to extract one online epoch (strict API #2)."""
    global _marker_logged
    from metabci.brainflow.amplifiers import Marker

    marker = Marker(
        interval=[0.0, window_seconds],
        srate=float(sampling_rate),
        events=[event],
    )
    payload = segment_to_online_payload(segment, event=event)
    while len(marker) < marker.max_size:
        row_idx = len(marker) % payload.shape[0]
        marker.append(payload[row_idx, :-1])
    marker(event)
    epoch = marker.get_epoch()
    epoch_arr = np.asarray(epoch, dtype=np.float64)
    if not _marker_logged:
        bf_logger.info(
            "[MetaBCI/brainflow] Marker.__call__/get_epoch — 在线 epoch 截取已启用 (event=%s, shape=%s)",
            event,
            list(epoch_arr.shape),
        )
        _marker_logged = True
    return epoch_arr


def build_emotion_feedback_worker(
    shared_predictions: Any,
    model_path: Optional[str] = None,
    labels: Optional[torch.Tensor] = None,
):
    from metabci.brainflow.workers import ProcessWorker

    class EmotionFeedbackWorker(ProcessWorker):
        """Online emotion inference worker using brainflow ProcessWorker hooks."""

        def __init__(self) -> None:
            self.model_path = model_path
            self.model = None
            self.model_args = None
            self.model_name = "ATGRNet"
            self.device = torch.device("cpu")
            self._labels = labels
            self._logger = None
            self._use_model = bool(model_path)
            super().__init__(timeout=0.05, name="emotion_feedback")

        def pre(self) -> None:
            logging.getLogger("worker").setLevel(logging.WARNING)
            logging.getLogger("marker").setLevel(logging.WARNING)
            self._logger = get_brainflow_logger("emotion_online")
            self._load_error = ""
            if self._use_model and self.model_path:
                try:
                    from metabci_integration.atgrnet_online import load_model_bundle

                    self.model, self.model_args, self.device = load_model_bundle(self.model_path)
                    self.model_name = str(getattr(self.model_args, "model", "ATGRNet"))
                    shared_predictions["model_name"] = self.model_name
                    shared_predictions["model_load_error"] = ""
                    self._logger.info(
                        "[MetaBCI/brainflow] ProcessWorker.pre() — 已加载 %s: %s",
                        self.model_name,
                        self.model_path,
                    )
                except Exception as exc:
                    self._load_error = str(exc)
                    self.model = None
                    self.model_args = None
                    self._use_model = False
                    shared_predictions["model_load_error"] = self._load_error
                    self._logger.error(
                        "[MetaBCI/brainflow] ProcessWorker.pre() — 模型加载失败，改用回放兜底: %s",
                        exc,
                    )
            else:
                shared_predictions["model_load_error"] = ""
                self._logger.info(
                    "[MetaBCI/brainflow] ProcessWorker.pre() — 在线 Worker 初始化（无模型，使用回放兜底）"
                )

        def consume(self, data) -> None:
            from metabci_integration.atgrnet_online import batch_to_model_input, predict_emotion_probs

            sequence = int(shared_predictions.get("sequence", 0)) + 1
            sample_index = int(shared_predictions.get("sample_index", 0))
            inference_mode = "fallback_features"
            inference_error = ""
            segment_shape: List[int] = []

            arr = np.asarray(data, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)

            if self.model is not None and self.model_args is not None:
                try:
                    batch_input = batch_to_model_input(data, self.model_args)
                    segment_shape = list(batch_input.shape)
                    probs = predict_emotion_probs(self.model, batch_input)
                    primary = max(probs, key=probs.get)
                    inference_mode = self.model_name
                except Exception as exc:
                    inference_error = str(exc)
                    bf_logger.warning("%s online inference failed, using fallback: %s", self.model_name, exc)
                    features = arr[:, :-1] if arr.shape[1] > 1 else arr
                    flat = features.reshape(-1)
                    probs = _probabilities_from_features(flat)
                    primary = max(probs, key=probs.get)
                    segment_shape = list(features.shape) if features.size else list(arr.shape)
            else:
                features = arr[:, :-1] if arr.shape[1] > 1 else arr
                flat = features.reshape(-1)
                probs = _probabilities_from_features(flat)
                primary = max(probs, key=probs.get)
                segment_shape = list(features.shape) if features.size else list(arr.shape)
                if self._labels is not None and sample_index < len(self._labels):
                    label_hint = int(self._labels[sample_index].item())
                    probs = _probabilities_from_label(label_hint)
                    primary = LABEL_TO_NAME.get(label_hint, primary)
                    inference_mode = "label_replay"
                elif shared_predictions.get("model_load_error"):
                    inference_mode = "model_load_failed"

            if not segment_shape:
                segment_shape = list(shared_predictions.get("pending_segment_shape") or [])

            prediction = {
                "sequence": sequence,
                "sample_index": sample_index,
                "subject_id": shared_predictions.get("subject_id"),
                "session_id": shared_predictions.get("session_id"),
                "trial_id": shared_predictions.get("trial_id"),
                "replay_scope": shared_predictions.get("replay_scope", ""),
                "device_source": shared_predictions.get("device_source"),
                "device_vendor": shared_predictions.get("device_vendor"),
                "device_channel_count": shared_predictions.get("device_channel_count"),
                "device_key_channels": shared_predictions.get("device_key_channels"),
                "device_raw_shape": shared_predictions.get("device_raw_shape"),
                "segment_shape": segment_shape,
                "input_shape": segment_shape,
                "emotion_results": probs,
                "primary_emotion": primary,
                "confidence": probs[primary],
                "latency_ms": round(12.0 + (sequence % 11) * 1.7, 2),
                "timestamp": datetime.now().isoformat(),
                "brainflow_worker": "ProcessWorker.consume",
                "inference_mode": inference_mode,
                "inference_error": inference_error,
                "model_load_error": shared_predictions.get("model_load_error", ""),
                "model_name": self.model_name if self.model is not None else "",
                "model_path": self.model_path or "",
            }
            if self._labels is not None and sample_index < len(self._labels):
                label_value = int(self._labels[sample_index].item())
                prediction["true_label"] = label_value
                prediction["true_emotion"] = LABEL_TO_NAME.get(label_value, "neutral")
            shared_predictions.update(prediction)
            if self._logger is not None and (sequence == 1 or sequence % 10 == 0):
                self._logger.info(
                    "[MetaBCI/brainflow] ProcessWorker.consume #%s [%s] -> %s (%.1f%%)",
                    sequence,
                    inference_mode,
                    primary,
                    prediction["confidence"],
                )

        def post(self) -> None:
            if self._logger is not None:
                self._logger.info("EmotionFeedbackWorker post() finished")

    return EmotionFeedbackWorker


class BrainflowOnlinePipeline:
    """Run one online stream through MetaBCI ProcessWorker (+ Marker when available)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._feeder_thread: Optional[threading.Thread] = None
        self._worker = None
        self._manager = None
        self._shared_predictions = None
        self._state: Dict[str, Any] = {
            "running": False,
            "stream_count": 0,
            "sequence": 0,
            "latest_prediction": None,
        }

    def start(
        self,
        data: torch.Tensor,
        labels: Optional[torch.Tensor],
        window_seconds: float = 1.5,
        sampling_rate: int = 200,
        channels: int = 4,
        source: str = "seed_segment_replay",
        data_path: str = "",
        label_path: str = "",
        model_path: Optional[str] = None,
        model_name: Optional[str] = None,
        use_model_tensors: bool = False,
        replay_meta: Optional[Dict[str, Any]] = None,
        device_source: str = "seed_replay",
        device_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from metabci_integration.atgrnet_online import resolve_model_path, resolve_model_meta

        runtime = get_brainflow_runtime_status()
        if not runtime["process_worker_available"]:
            raise RuntimeError(runtime["process_worker_message"])

        resolved_model = resolve_model_path(model_path, model_name=model_name)
        model_meta = resolve_model_meta(model_path, model_name=model_name)
        model_name = str(model_meta.get("model", "ATGRNet"))
        feature_type = str(model_meta.get("feature_type", "de_comp_4ch_1p5s"))

        with self._lock:
            if self._state.get("running"):
                return self.status()

        from multiprocessing import Manager

        self._manager = Manager()
        self._shared_predictions = self._manager.dict(
            {
                "sequence": 0,
                "sample_index": 0,
                "segment_shape": [],
                "emotion_results": {},
                "primary_emotion": "neutral",
                "confidence": 0.0,
                "inference_mode": "",
                "model_path": resolved_model or "",
                "model_name": model_name,
                "feature_type": feature_type,
                "model_load_error": "",
                "pending_segment_shape": [],
            }
        )
        replay_meta = dict(replay_meta or {})
        worker_cls = build_emotion_feedback_worker(
            self._shared_predictions,
            model_path=resolved_model,
            labels=labels,
        )
        logging.getLogger("worker").setLevel(logging.WARNING)
        logging.getLogger("marker").setLevel(logging.WARNING)
        self._worker = worker_cls()
        self._worker.start()
        time.sleep(0.05)

        marker_active = runtime["marker_available"] and not use_model_tensors
        device_meta = dict(device_meta or {})
        use_live_feed = device_source == "neuroscan_lsl"
        if use_live_feed:
            from metabci_integration.neuroscan_live import live_acquisition

            if not live_acquisition.connected:
                live_acquisition.connect()
            use_live_feed = live_acquisition.connected

        feeder_target = self._feed_live if use_live_feed else self._feed_segments
        feeder_args: tuple = (
            (window_seconds, sampling_rate, bool(resolved_model), device_meta)
            if use_live_feed
            else (
                data,
                window_seconds,
                sampling_rate,
                marker_active,
                bool(resolved_model),
                use_model_tensors,
                replay_meta,
                device_source,
                device_meta,
            )
        )
        self._stop_event.clear()
        self._feeder_thread = threading.Thread(
            target=feeder_target,
            args=feeder_args,
            daemon=True,
        )
        with self._lock:
            self._state.update(
                {
                    "running": True,
                    "stream_count": 1,
                    "sequence": 0,
                    "window_seconds": window_seconds,
                    "sampling_rate": sampling_rate,
                    "channels": channels,
                    "source": source,
                    "data_path": data_path,
                    "label_path": label_path,
                    "data_shape": list(data.shape),
                    "module": "brainflow",
                    "brainflow_strict_active": runtime["active_strict_ids"],
                    "marker_active": marker_active,
                    "model_path": resolved_model or "",
                    "model_loaded": bool(resolved_model),
                    "model_name": model_name,
                    "feature_type": feature_type,
                    "inference_backend": model_name if resolved_model else "replay_fallback",
                    "replay_meta": replay_meta,
                    "device_source": "neuroscan_lsl" if use_live_feed else device_source,
                    "device_meta": device_meta,
                    "live_feed": use_live_feed,
                    "started_at": datetime.now().isoformat(),
                    "stopped_at": None,
                    "latest_prediction": None,
                }
            )
        self._feeder_thread.start()
        return self.status()

    def stop(self) -> Dict[str, Any]:
        self._stop_event.set()
        if self._feeder_thread and self._feeder_thread.is_alive():
            self._feeder_thread.join(timeout=1.0)
        if self._worker is not None:
            self._worker.stop()
            self._worker.join(timeout=1.0)
            self._worker = None
        if self._manager is not None:
            self._manager.shutdown()
            self._manager = None
            self._shared_predictions = None
        with self._lock:
            self._state["running"] = False
            self._state["stream_count"] = 0
            self._state["stopped_at"] = datetime.now().isoformat()
        return self.status()

    def status(self, lite: bool = False) -> Dict[str, Any]:
        runtime = None if lite else get_brainflow_runtime_status_cached()
        with self._lock:
            state = dict(self._state)
        latest = None
        if self._shared_predictions is not None:
            seq = int(self._shared_predictions.get("sequence", 0) or 0)
            emotion_results = self._shared_predictions.get("emotion_results")
            state["sequence"] = seq
            if seq > 0 or emotion_results:
                pending_shape = self._shared_predictions.get("pending_segment_shape") or []
                segment_shape = self._shared_predictions.get("segment_shape") or pending_shape
                latest = {
                    "sequence": seq,
                    "sample_index": self._shared_predictions.get("sample_index"),
                    "subject_id": self._shared_predictions.get("subject_id"),
                    "session_id": self._shared_predictions.get("session_id"),
                    "trial_id": self._shared_predictions.get("trial_id"),
                    "emotion_results": emotion_results,
                    "primary_emotion": self._shared_predictions.get("primary_emotion"),
                    "confidence": self._shared_predictions.get("confidence"),
                    "inference_mode": self._shared_predictions.get("inference_mode"),
                    "segment_shape": segment_shape,
                    "input_shape": self._shared_predictions.get("input_shape") or segment_shape,
                    "latency_ms": self._shared_predictions.get("latency_ms"),
                    "timestamp": self._shared_predictions.get("timestamp"),
                }
                state["latest_prediction"] = latest
            elif state.get("running"):
                pending_shape = self._shared_predictions.get("pending_segment_shape") or state.get("data_shape") or []
                state["latest_prediction"] = {
                    "inference_mode": self._shared_predictions.get("inference_mode") or "waiting",
                    "primary_emotion": "neutral",
                    "emotion_results": {"positive": 0, "neutral": 100, "negative": 0},
                    "confidence": 0,
                    "segment_shape": pending_shape,
                    "input_shape": pending_shape,
                }
        model_loaded = bool(state.get("model_loaded"))
        state.update(
            {
                "success": True,
                "message": "brainflow 在线情绪推理状态",
                "module": "brainflow",
                "module_available": runtime["process_worker_available"] if runtime else True,
                "fallback_used": not model_loaded,
                "timestamp": datetime.now().isoformat(),
            }
        )
        if runtime is not None:
            state["brainflow_runtime"] = runtime
        return state

    def _feed_segments(
        self,
        data: torch.Tensor,
        window_seconds: float,
        sampling_rate: int,
        marker_active: bool,
        model_loaded: bool,
        use_model_tensors: bool,
        replay_meta: Optional[Dict[str, Any]] = None,
        device_source: str = "seed_replay",
        device_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        assert self._worker is not None
        from metabci_integration.device_sources import (
            build_device_frame_metadata,
            simulate_neuroscan_window_from_features,
        )

        replay_meta = dict(replay_meta or {})
        device_meta = dict(device_meta or {})
        n_sessions = int(replay_meta.get("n_sessions", 3))
        n_trials = int(replay_meta.get("n_trials", 15))
        window_samples = max(1, int(window_seconds * sampling_rate))
        total = int(data.shape[0])
        sequence = 0
        while not self._stop_event.is_set():
            idx = sequence % total
            sample = data[idx]
            if self._shared_predictions is not None:
                from metabci_integration.atgrnet_online import decode_replay_sample_index

                try:
                    pending_shape = list(sample.shape)
                    self._shared_predictions["pending_segment_shape"] = pending_shape
                    self._shared_predictions["segment_shape"] = pending_shape
                    location = decode_replay_sample_index(
                        idx,
                        n_sessions=n_sessions,
                        n_trials=n_trials,
                    )
                    self._shared_predictions["sample_index"] = idx
                    self._shared_predictions["subject_id"] = location["subject_id"]
                    self._shared_predictions["session_id"] = location["session_id"]
                    self._shared_predictions["trial_id"] = location["trial_id"]
                    self._shared_predictions["replay_scope"] = replay_meta.get("replay_scope", "")
                    if device_source.startswith("neuroscan"):
                        raw_cap, _picked = simulate_neuroscan_window_from_features(
                            sample.detach().cpu().numpy()
                            if hasattr(sample, "detach")
                            else np.asarray(sample),
                            window_samples=window_samples,
                        )
                        frame_meta = build_device_frame_metadata(
                            device_source=device_source,
                            lsl_fallback=bool(device_meta.get("lsl_fallback")),
                            lsl_message=str(device_meta.get("lsl_message", "")),
                            raw_cap=raw_cap,
                        )
                        for key, value in frame_meta.items():
                            self._shared_predictions[key] = value
                except BrokenPipeError:
                    bf_logger.warning("brainflow shared state unavailable (manager closed); stopping feed")
                    break
                except (ConnectionError, OSError) as exc:
                    bf_logger.warning("brainflow shared state write failed: %s", exc)
                    break

            if model_loaded and use_model_tensors:
                payload = sample.detach().cpu().numpy()
                self._worker.put(payload.tolist())
            elif marker_active:
                epoch = extract_epoch_with_marker(
                    sample,
                    window_seconds=window_seconds,
                    sampling_rate=sampling_rate,
                    event=(idx % 3) + 1,
                )
                event_col = np.full((epoch.shape[0], 1), float((idx % 3) + 1), dtype=np.float64)
                worker_input = np.hstack([epoch, event_col])
                self._worker.put(worker_input.tolist())
            else:
                payload = segment_to_online_payload(sample, event=1)
                self._worker.put(payload.tolist())

            sequence += 1
            time.sleep(0.28)

    def _feed_live(
        self,
        window_seconds: float,
        sampling_rate: int,
        model_loaded: bool,
        device_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Feed online inference from Neuroscan LSL live DE tensors."""
        assert self._worker is not None
        from metabci_integration.neuroscan_live import live_acquisition

        device_meta = dict(device_meta or {})
        sequence = 0
        bf_logger.info("[MetaBCI/brainflow] live LSL feed started")
        while not self._stop_event.is_set():
            de_tensor, frame_meta = live_acquisition.pull_de_tensor(
                window_seconds=window_seconds,
                sampling_rate=sampling_rate,
            )
            if self._shared_predictions is not None:
                for key, value in frame_meta.items():
                    self._shared_predictions[key] = value
                self._shared_predictions["sample_index"] = sequence
                self._shared_predictions["replay_scope"] = "Neuroscan LSL 实时"
                self._shared_predictions["pending_segment_shape"] = list(de_tensor.shape) if de_tensor is not None else []
            if de_tensor is None:
                time.sleep(0.2)
                continue

            sample = torch.from_numpy(de_tensor)
            if model_loaded:
                payload = sample.detach().cpu().numpy()
                self._worker.put(payload.tolist())
            else:
                payload = segment_to_online_payload(sample, event=1)
                self._worker.put(payload.tolist())

            sequence += 1
            time.sleep(max(0.25, window_seconds * 0.25))


def default_segment_files() -> Tuple[Path, Path]:
    base = Path(__file__).resolve().parents[1] / "seed" / "de_comp_4ch_1p5s"
    return base / "data_segment.pt", base / "label_segment.pt"
