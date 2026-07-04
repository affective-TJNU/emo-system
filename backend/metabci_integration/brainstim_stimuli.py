"""Emotion image stimulus catalog for brainstim SEED passive paradigm."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

_METABCI_ROOT = Path(__file__).resolve().parents[2] / "MetaBCI-master"
STIMULI_ROOT = _METABCI_ROOT / "stimuli" / "seed_emotion"

EMOTION_BLOCKS: List[Dict[str, Any]] = [
    {
        "emotion": "positive",
        "label": "积极 Positive",
        "marker": 21,
        "color": "#44cc88",
    },
    {
        "emotion": "neutral",
        "label": "中性 Neutral",
        "marker": 22,
        "color": "#8899cc",
    },
    {
        "emotion": "negative",
        "label": "消极 Negative",
        "marker": 23,
        "color": "#cc4466",
    },
]

MARKER_TO_EMOTION = {int(b["marker"]): b["emotion"] for b in EMOTION_BLOCKS}


def _list_images(folder: Path) -> List[str]:
    if not folder.is_dir():
        return []
    files = sorted(
        p.name
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}
    )
    return files


def get_stimuli_catalog(*, api_prefix: str = "/api/metabci/brainstim/stimulus-file") -> Dict[str, Any]:
    """Return stimulus blocks with API URLs for frontend / demo."""
    blocks: List[Dict[str, Any]] = []
    for block in EMOTION_BLOCKS:
        emotion = str(block["emotion"])
        folder = STIMULI_ROOT / emotion
        images = []
        for name in _list_images(folder):
            images.append({
                "filename": name,
                "url": f"{api_prefix}/{emotion}/{name}",
                "path": str(folder / name),
            })
        blocks.append({**block, "images": images, "image_count": len(images)})

    return {
        "stimuli_root": str(STIMULI_ROOT),
        "stimuli_ready": all(b["image_count"] > 0 for b in blocks),
        "stimulus_source": "OASIS (Open Affective Standardized Image Set)",
        "stimulus_source_url": "https://osf.io/6pnd7/",
        "hardware_required": False,
        "demo_note": (
            "无电极帽可录视频：PsychoPy ImageStim 呈现图片 + LSL marker；"
            "EEG 由 neuroscan_sim/seed_replay 模拟。"
        ),
        "blocks": blocks,
        "baseline": {
            "type": "fixation_cross",
            "marker": 1,
            "description": "注视十字基线采集",
        },
    }


def resolve_stimulus_for_marker(marker_code: int) -> Optional[Dict[str, Any]]:
    emotion = MARKER_TO_EMOTION.get(int(marker_code))
    if not emotion:
        return None
    folder = STIMULI_ROOT / emotion
    names = _list_images(folder)
    if not names:
        return None
    filename = names[0]
    block = next(b for b in EMOTION_BLOCKS if b["emotion"] == emotion)
    return {
        "emotion": emotion,
        "label": block["label"],
        "marker": marker_code,
        "filename": filename,
        "url": f"/api/metabci/brainstim/stimulus-file/{emotion}/{filename}",
        "path": str(folder / filename),
    }


def resolve_stimulus_file(emotion: str, filename: str) -> Optional[Path]:
    safe_emotion = emotion.strip().lower()
    safe_name = Path(filename).name
    if safe_emotion not in {b["emotion"] for b in EMOTION_BLOCKS}:
        return None
    candidate = (STIMULI_ROOT / safe_emotion / safe_name).resolve()
    root = STIMULI_ROOT.resolve()
    if not str(candidate).startswith(str(root)):
        return None
    if candidate.is_file():
        return candidate
    return None
