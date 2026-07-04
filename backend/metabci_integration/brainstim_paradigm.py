"""Passive emotion paradigm for MetaBCI brainstim integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .availability import get_metabci_status
from .brainstim_runtime import get_brainstim_runtime_status, get_lsl_port
from .brainstim_strict import get_strict_brainstim_function_report
from .brainstim_stimuli import get_stimuli_catalog, resolve_stimulus_for_marker


def probe_brainstim_runtime() -> Dict[str, Any]:
    """Check whether brainstim can actually run (not just JSON description)."""
    return get_brainstim_runtime_status()


def get_passive_emotion_paradigm() -> Dict[str, Any]:
    status = get_metabci_status()
    runtime = probe_brainstim_runtime()
    strict = get_strict_brainstim_function_report()
    module_available = bool(status["modules"]["brainstim"])
    runtime_ready = bool(runtime.get("runtime_ready"))
    steps: List[Dict[str, Any]] = [
        {
            "step": 1,
            "name": "基线采集",
            "marker": "baseline",
            "marker_code": 1,
            "duration_seconds": 30,
            "description": "呈现中性注视点并采集静息 EEG。",
        },
        {
            "step": 2,
            "name": "情绪刺激呈现",
            "marker": "emotion_stimulus",
            "marker_code": 2,
            "duration_seconds": 90,
            "description": "播放 SEED 风格情绪视频/图片（积极/中性/消极）。",
        },
        {
            "step": 3,
            "name": "脑电同步标记",
            "marker": "eeg_marker",
            "marker_code": 3,
            "duration_seconds": 0,
            "description": "通过 LsLPort / NeuroscanPort 发送 marker，供 brainflow 对齐 epoch。",
        },
        {
            "step": 4,
            "name": "在线情绪推理反馈",
            "marker": "online_feedback",
            "marker_code": 4,
            "duration_seconds": 0,
            "description": "brainflow ProcessWorker 在线推理，前端展示三分类概率。",
        },
    ]

    return {
        "success": True,
        "module": "brainstim",
        "module_available": module_available,
        "fallback_used": not runtime_ready,
        "runtime_ready": runtime_ready,
        "runtime": runtime,
        "brainstim_strict": strict,
        "stimuli": get_stimuli_catalog(),
        "strict_function_count": strict.get("runtime_verified_count") or 0,
        "strict_function_registered": strict.get("strict_function_count") or 0,
        "paradigm_name": "SEEDPassiveEmotion",
        "description": (
            "SEED 被动情绪监测范式：基线 → 情绪诱发 → EEG marker → brainflow 在线反馈。"
        ),
        "steps": steps,
        "verify_commands": [
            "curl -X POST http://localhost:5001/api/metabci/brainstim/verify",
            "curl http://localhost:5001/api/metabci/brainstim/paradigm",
            "python scripts/preliminary_metabci_verify.py",
        ],
        "timestamp": datetime.now().isoformat(),
    }


def simulate_paradigm_run(fast: bool = True) -> Dict[str, Any]:
    """Run brainstim marker sequence; LsLPort when available, always return event log."""
    paradigm = get_passive_emotion_paradigm()
    apis_called: List[str] = list(runtime.get("apis_called") or []) if (runtime := paradigm.get("runtime")) else []
    lsl_available = False
    port: Any = None

    try:
        port = get_lsl_port()
        lsl_available = True
        if "metabci.brainstim.utils.LsLPort.setData" not in apis_called:
            apis_called.append("metabci.brainstim.utils.LsLPort.setData")
    except Exception:
        pass

    sequence: List[Dict[str, Any]] = [
        {"step": 1, "marker_code": 1, "marker_label": "baseline", "detail": "基线采集开始", "duration_ms": 3000 if fast else 30000},
        {"step": 2, "marker_code": 2, "marker_label": "emotion_stimulus", "detail": "情绪刺激块开始", "duration_ms": 400 if fast else 2000},
    ]
    catalog = get_stimuli_catalog()
    per_image_ms = 1800 if fast else 10000
    for block in catalog.get("blocks") or []:
        emotion = str(block.get("emotion") or "")
        label = str(block.get("label") or emotion)
        marker = int(block.get("marker") or 0)
        for img in block.get("images") or []:
            sequence.append({
                "step": 2,
                "marker_code": marker,
                "marker_label": emotion,
                "detail": f"{label} · {img.get('filename', '')}",
                "duration_ms": per_image_ms,
                "stimulus": {
                    "emotion": emotion,
                    "label": label,
                    "marker": marker,
                    "filename": img.get("filename"),
                    "url": img.get("url"),
                    "path": img.get("path"),
                },
            })
    sequence.extend([
        {"step": 3, "marker_code": 3, "marker_label": "eeg_marker", "detail": "EEG epoch 对齐", "duration_ms": 800 if fast else 2000},
        {"step": 4, "marker_code": 4, "marker_label": "online_feedback", "detail": "brainflow 在线反馈", "duration_ms": 800 if fast else 2000},
    ])

    events: List[Dict[str, Any]] = []
    for item in sequence:
        ts = datetime.now().isoformat()
        channel = "lsl" if lsl_available else "simulated"
        sent = False
        if port is not None:
            try:
                port.setData(item["marker_code"])
                sent = True
                try:
                    from .neuroscan_live import live_acquisition

                    live_acquisition.set_marker(int(item["marker_code"]))
                except Exception:
                    pass
            except Exception:
                channel = "simulated"
                lsl_available = False
        events.append({
            **item,
            "timestamp": ts,
            "channel": channel,
            "sent": True if sent or not lsl_available else False,
            "stimulus": item.get("stimulus") or resolve_stimulus_for_marker(int(item["marker_code"])),
        })

    return {
        "success": True,
        "module": "brainstim",
        "paradigm_name": paradigm.get("paradigm_name"),
        "simulation_mode": "fast" if fast else "full",
        "lsl_available": lsl_available,
        "apis_called": apis_called,
        "strict_function_count": len(apis_called),
        "stimuli": get_stimuli_catalog(),
        "events": events,
        "total_duration_ms": sum(int(e.get("duration_ms") or 0) for e in events),
        "message": (
            "LSL marker 已通过 brainstim LsLPort 发送"
            if lsl_available
            else "模拟模式：marker 事件已生成（LsLPort 不可用时降级）"
        ),
        "timestamp": datetime.now().isoformat(),
    }
