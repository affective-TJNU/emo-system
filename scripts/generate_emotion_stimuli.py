#!/usr/bin/env python3
"""Generate placeholder emotion stimulus images (fallback only).

Prefer real OASIS images:
  python scripts/download_oasis_stimuli.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MetaBCI-master" / "stimuli" / "seed_emotion"


def main() -> int:
    print("推荐使用公开 OASIS 情绪图片库（已含效价评分）：")
    print("  python scripts/download_oasis_stimuli.py")
    if OUT.joinpath("STIMULI_MANIFEST.json").exists():
        print("\n检测到已有 OASIS 图片，无需重新生成占位图。")
        return 0
    print("\n未检测到 OASIS 图片，请先运行 download_oasis_stimuli.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
