"""In-memory feature-learning progress for frontend polling."""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_VALIDATION_RE = re.compile(
    r"Validation Results \[([^\]]+)\] - Epoch: (\d+) acc: ([\d.]+) loss: ([\d.]+)"
)

_LOCK = threading.Lock()
_TRAINING_STATUS: Dict[str, Any] = {
    "state": "idle",
    "model": None,
    "epoch": -1,
    "total_epochs": 0,
    "accuracy": 0.0,
    "loss": 0.0,
    "percent": 0,
    "message": "No training in progress",
    "started_at": None,
    "finished_at": None,
    "error": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_percent(epoch: int, total_epochs: int, state: str) -> int:
    if state == "completed":
        return 95
    if state in {"idle", "failed"}:
        return 0
    if total_epochs <= 0:
        return 0
    completed = max(0, epoch + 1)
    return min(95, round(completed / total_epochs * 95))


def reset_training_progress(model: str, total_epochs: int) -> None:
    with _LOCK:
        _TRAINING_STATUS.update(
            {
                "state": "running",
                "model": model,
                "epoch": -1,
                "total_epochs": int(total_epochs),
                "accuracy": 0.0,
                "loss": 0.0,
                "percent": 0,
                "message": f"{model} 模型训练启动中…",
                "started_at": _utc_now(),
                "finished_at": None,
                "error": None,
            }
        )


def update_training_epoch(
    epoch: int,
    accuracy: float,
    loss: float,
    model: Optional[str] = None,
) -> None:
    with _LOCK:
        if _TRAINING_STATUS.get("state") not in {"running", "completed"}:
            return
        total_epochs = int(_TRAINING_STATUS.get("total_epochs") or 0)
        if model:
            _TRAINING_STATUS["model"] = model
        _TRAINING_STATUS["epoch"] = int(epoch)
        _TRAINING_STATUS["accuracy"] = float(accuracy)
        _TRAINING_STATUS["loss"] = float(loss)
        _TRAINING_STATUS["percent"] = _compute_percent(int(epoch), total_epochs, "running")
        _TRAINING_STATUS["message"] = (
            f"Epoch {epoch + 1}/{total_epochs} | acc={accuracy:.4f} loss={loss:.4f}"
        )


def mark_training_completed(message: str = "训练完成") -> None:
    with _LOCK:
        total_epochs = int(_TRAINING_STATUS.get("total_epochs") or 0)
        epoch = int(_TRAINING_STATUS.get("epoch") or -1)
        if total_epochs > 0 and epoch < total_epochs - 1:
            epoch = total_epochs - 1
            _TRAINING_STATUS["epoch"] = epoch
        _TRAINING_STATUS["state"] = "completed"
        _TRAINING_STATUS["percent"] = 95
        _TRAINING_STATUS["message"] = message
        _TRAINING_STATUS["finished_at"] = _utc_now()


def mark_training_failed(error: str) -> None:
    with _LOCK:
        _TRAINING_STATUS["state"] = "failed"
        _TRAINING_STATUS["error"] = error
        _TRAINING_STATUS["message"] = error
        _TRAINING_STATUS["finished_at"] = _utc_now()


def parse_training_output_line(line: str) -> None:
    text = (line or "").strip()
    if not text:
        return

    match = _VALIDATION_RE.search(text)
    if match:
        model, epoch, acc, loss = match.groups()
        update_training_epoch(int(epoch), float(acc), float(loss), model)
        return

    if "===== 训练开始" in text or "训练开始 | model=" in text:
        with _LOCK:
            if _TRAINING_STATUS.get("state") == "running":
                _TRAINING_STATUS["message"] = "模型训练中…"
        return

    if "debug is done" in text or "max acc=" in text:
        mark_training_completed()


def get_training_progress() -> Dict[str, Any]:
    with _LOCK:
        return dict(_TRAINING_STATUS)
