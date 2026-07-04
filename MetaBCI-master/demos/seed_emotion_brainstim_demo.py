# -*- coding: utf-8 -*-
# SEED 被动情绪范式 — MetaBCI brainstim 可运行 Demo
#
# 用法:
#   cd emo-system/MetaBCI-master
#   PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --dry-run
#   PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --run
#   PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --run --windowed --fast
#
# 说明:
#   - --dry-run: 无 GUI，仅探测 brainstim/PsychoPy 并打印 4 步范式与 marker
#   - --run:     弹出 PsychoPy 窗口运行范式（需 DISPLAY）
#   - --fast:    缩短各阶段时长，便于答辩快速演示

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# MetaBCI 根目录加入 path
_METABCI_ROOT = Path(__file__).resolve().parents[1]
if str(_METABCI_ROOT) not in sys.path:
    sys.path.insert(0, str(_METABCI_ROOT))

PARADIGM_NAME = "SEEDPassiveEmotion"

PARADIGM_STEPS: List[Dict[str, Any]] = [
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
        "description": "通过 LsLPort 发送 marker，供 brainflow 对齐 epoch。",
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

EMOTION_BLOCKS = [
    {"label": "积极 Positive", "color": "#44cc88", "marker": 21, "folder": "positive"},
    {"label": "中性 Neutral", "color": "#8899cc", "marker": 22, "folder": "neutral"},
    {"label": "消极 Negative", "color": "#cc4466", "marker": 23, "folder": "negative"},
]

STIMULI_ROOT = _METABCI_ROOT / "stimuli" / "seed_emotion"


def _list_stimulus_images(folder: str) -> List[Path]:
    target = STIMULI_ROOT / folder
    if not target.is_dir():
        return []
    return sorted(
        p for p in target.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}
    )


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _guess_display_hint() -> str:
    if _has_display():
        return ""
    if Path("/tmp/.X11-unix/X0").exists():
        return (
            "检测到本机有 X 服务 (X0)，但 DISPLAY 未设置。"
            "请在当前终端执行: export DISPLAY=:0"
            "（若仍报 Authorization，在本机桌面终端运行，或执行 xhost +local:）"
        )
    return "当前无图形环境。SSH 远程请用 curl/API 答辩；GUI 需在本机桌面或 xvfb-run 下运行。"


def _is_display_error(msg: str) -> bool:
    lower = msg.lower()
    return "cannot connect" in lower or "display" in lower or "authorization" in lower


def _send_marker(port: Any, code: int) -> None:
    """发送 LSL marker；无 outlet 时打印到控制台。"""
    label = str(code)
    if port is not None:
        try:
            port.setData(label)
            print(f"  [marker] LSL → {label}")
            return
        except Exception as exc:
            print(f"  [marker] LSL 失败 ({exc})，改用控制台输出")
    print(f"  [marker] console → {label}")


def _probe_runtime() -> Dict[str, Any]:
    probe: Dict[str, Any] = {
        "psychopy_available": False,
        "brainstim_framework": False,
        "brainstim_utils": False,
        "display_available": _has_display(),
        "strict_functions": [],
    }
    try:
        import psychopy  # noqa: F401

        probe["psychopy_available"] = True
        probe["psychopy_version"] = psychopy.__version__
    except Exception as exc:
        probe["error"] = f"psychopy: {exc}"
        return probe

    try:
        from metabci.brainstim.utils import LsLPort, _check_array_like  # noqa: F401

        probe["brainstim_utils"] = True
        probe["strict_functions"].extend([
            "metabci.brainstim.utils.LsLPort.setData",
            "metabci.brainstim.utils._check_array_like",
        ])
    except Exception as exc:
        probe["utils_error"] = str(exc)

    try:
        from metabci.brainstim.framework import Experiment  # noqa: F401

        probe["brainstim_framework"] = True
        probe["strict_functions"].extend([
            "metabci.brainstim.framework.Experiment.register_paradigm",
            "metabci.brainstim.framework.Experiment.get_window",
        ])
    except Exception as exc:
        probe["framework_error"] = str(exc)

    probe["runtime_ready"] = (
        probe["psychopy_available"]
        and probe["brainstim_framework"]
        and probe["brainstim_utils"]
    )
    return probe


def dry_run() -> int:
    print("=" * 60)
    print(f"MetaBCI brainstim Demo — {PARADIGM_NAME}")
    print("=" * 60)

    probe = _probe_runtime()
    print("\n[运行时探测]")
    print(json.dumps(probe, indent=2, ensure_ascii=False))

    print("\n[范式 4 步流程 + Marker 码]")
    for step in PARADIGM_STEPS:
        dur = step["duration_seconds"]
        dur_text = f"{dur}s" if dur else "事件触发"
        print(
            f"  Step {step['step']}: {step['name']}"
            f" | marker={step['marker']} (#{step['marker_code']})"
            f" | {dur_text}"
        )
        print(f"           {step['description']}")

    print("\n[情绪块附加 marker + 图片刺激]")
    for block in EMOTION_BLOCKS:
        n = len(_list_stimulus_images(block["folder"]))
        print(f"  {block['label']} → marker #{block['marker']} | {n} 张 ImageStim")
    if not STIMULI_ROOT.is_dir():
        print(f"\n  提示: 运行 python scripts/generate_emotion_stimuli.py 生成刺激图片")

    print("\n[验证命令]")
    print("  curl http://localhost:5001/api/metabci/brainstim/paradigm")
    print("  curl http://localhost:5001/api/metabci/status")

    if not probe.get("psychopy_available"):
        print("\n✗ PsychoPy 未安装。请: conda install -c conda-forge psychopy")
        return 1

    if probe.get("runtime_ready"):
        print("\n✓ brainstim 完全就绪。")
        if not probe.get("display_available"):
            print("  提示: 运行 GUI 前请 export DISPLAY=:0")
        else:
            print("  运行 GUI: python demos/seed_emotion_brainstim_demo.py --run --windowed --fast")
        return 0

    utils_err = str(probe.get("utils_error") or probe.get("framework_error") or "")
    if _is_display_error(utils_err) or not probe.get("display_available"):
        print("\n✓ PsychoPy 已安装 — 依赖没问题")
        print("△ brainstim 完整 import 需要图形会话（当前终端无 DISPLAY / X 授权）")
        hint = _guess_display_hint()
        if hint:
            print(f"  → {hint}")
        print("\n  答辩可用: curl API + 前端 brainstim 面板（无需 GUI）")
        print("  弹窗演示: 在本机桌面终端执行")
        print("    export DISPLAY=:0")
        print("    PYTHONPATH=. python demos/seed_emotion_brainstim_demo.py --run --windowed --fast")
        return 0

    print("\n✗ brainstim 导入失败（非 DISPLAY 问题）:")
    if probe.get("utils_error"):
        print(f"  utils: {probe['utils_error']}")
    if probe.get("framework_error"):
        print(f"  framework: {probe['framework_error']}")
    print("  请确认: pip install -e . && pip install pylsl")
    return 1


def _make_paradigm_func(
    baseline_sec: float,
    block_sec: float,
) -> Callable:
    """构建 register_paradigm 使用的范式函数。"""

    def seed_passive_emotion(win) -> None:
        from psychopy import core, visual, event
        from metabci.brainstim.utils import LsLPort

        port: Optional[Any] = None
        try:
            port = LsLPort()
            print("LSL Marker outlet 已创建")
        except Exception as exc:
            print(f"LSL outlet 不可用: {exc}，marker 将打印到控制台")

        def draw_text(msg: str, color: str = "white", height: float = 0.05) -> None:
            stim = visual.TextStim(
                win, text=msg, color=color, height=height,
                wrapWidth=1.6, alignText="center",
            )
            stim.draw()

        def wait_seconds(seconds: float, draw_fn) -> None:
            clock = core.Clock()
            while clock.getTime() < seconds:
                if "escape" in event.getKeys(["escape"]):
                    return
                draw_fn()
                win.flip()

        # Step 1: 基线
        print(f"\n>>> Step 1 基线采集 ({baseline_sec}s), marker=1")
        _send_marker(port, 1)

        def draw_baseline() -> None:
            visual.Circle(win, radius=8, fillColor="white", lineColor=None).draw()
            draw_text("基线采集 — 请注视十字\nBaseline", "#aaccff", 0.04)

        wait_seconds(baseline_sec, draw_baseline)
        if "escape" in event.getKeys(["escape"]):
            return

        # Step 2: 情绪刺激（3 类各 block_sec 秒）
        print(f"\n>>> Step 2 情绪刺激呈现, marker=2")
        _send_marker(port, 2)

        for block in EMOTION_BLOCKS:
            images = _list_stimulus_images(block["folder"])
            print(f"    呈现: {block['label']}, marker={block['marker']}, images={len(images)}")
            _send_marker(port, block["marker"])
            elapsed = core.Clock()
            img_idx = 0

            while elapsed.getTime() < block_sec:
                if "escape" in event.getKeys(["escape"]):
                    return
                if images:
                    img_path = images[img_idx % len(images)]
                    stim = visual.ImageStim(
                        win, image=str(img_path), size=(1.25, 0.85), interpolate=True,
                    )
                    stim.draw()
                    # 每张图至少展示 2s（fast 模式）或按总数均分
                    per_img = max(2.0, block_sec / max(len(images), 1))
                    if elapsed.getTime() >= img_idx * per_img and img_idx < len(images) - 1:
                        img_idx += 1
                else:
                    rect = visual.Rect(
                        win, width=1.2, height=0.7,
                        fillColor=block["color"], lineColor=None, opacity=0.85,
                    )
                    rect.draw()
                draw_text(block["label"], "white", 0.05)
                win.flip()

        # Step 3: EEG marker 同步
        print("\n>>> Step 3 脑电同步标记, marker=3")
        _send_marker(port, 3)
        draw_text("Marker 已发送\nEEG 同步完成", "#00eeff", 0.05)
        win.flip()
        core.wait(1.5)

        # Step 4: 在线反馈占位
        print("\n>>> Step 4 在线情绪推理反馈, marker=4")
        _send_marker(port, 4)
        draw_text(
            "在线推理反馈\n请在前端「情绪识别」步骤查看 brainflow 结果",
            "#ffcc44", 0.045,
        )
        win.flip()
        core.wait(2.0)
        print("\n范式运行完成。")

    return seed_passive_emotion


def run_gui(*, windowed: bool, fast: bool) -> int:
    if not _has_display():
        print("错误: 未检测到 DISPLAY，无法启动 GUI。请使用 --dry-run。")
        return 1

    probe = _probe_runtime()
    if not probe.get("runtime_ready"):
        print("错误: brainstim 运行时未就绪。")
        print(json.dumps(probe, indent=2, ensure_ascii=False))
        return 1

    import numpy as np
    from metabci.brainstim.framework import Experiment

    baseline_sec = 5.0 if fast else 30.0
    block_sec = 8.0 if fast else 30.0

    print(f"启动 GUI 范式 | baseline={baseline_sec}s | block={block_sec}s | windowed={windowed}")

    ex = Experiment(
        win_size=(1280, 720),
        screen_id=0,
        is_fullscr=not windowed,
        bg_color_warm=np.array([-1.0, -1.0, -0.2]),
        record_frames=False,
        disable_gc=False,
    )
    ex.register_paradigm(PARADIGM_NAME, _make_paradigm_func(baseline_sec, block_sec))

    print("\n操作说明:")
    print("  Enter → 运行 SEEDPassiveEmotion 范式")
    print("  q     → 退出")
    print("  Esc   → 范式内中断")

    ex.run()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SEED 被动情绪 brainstim 范式 Demo")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="探测环境并打印范式步骤（无 GUI）")
    mode.add_argument("--run", action="store_true", help="启动 PsychoPy GUI 运行范式")
    parser.add_argument("--windowed", action="store_true", help="窗口模式（非全屏）")
    parser.add_argument("--fast", action="store_true", help="缩短各阶段时长")
    args = parser.parse_args()

    if args.dry_run:
        return dry_run()
    return run_gui(windowed=args.windowed, fast=args.fast)


if __name__ == "__main__":
    raise SystemExit(main())
