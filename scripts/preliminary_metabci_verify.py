#!/usr/bin/env python3
"""Preliminary competition video helper: verify MetaBCI strict API counts."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:5001"


def fetch(path: str, method: str = "GET") -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        method=method,
        headers={"Content-Type": "application/json"},
        data=b"{}" if method == "POST" else None,
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    print("=== MetaBCI 初赛自检（录视频时可终端并排展示）===\n")

    try:
        status = fetch("/api/metabci/status")
    except urllib.error.URLError as exc:
        print(f"后端未启动: {exc}")
        print("请先: cd backend && python app.py")
        return 1

    brainda = status.get("brainda_strict") or {}
    brainstim = status.get("brainstim_strict") or {}
    print(f"brainda  严格 API: {brainda.get('strict_function_count')} 项注册, meets_three={brainda.get('meets_minimum_three')}")
    print(
        f"brainstim 严格 API: {brainstim.get('strict_function_count')} 项注册, "
        f"已验证={brainstim.get('runtime_verified_count', 0)}"
    )

    print("\n--- POST /api/metabci/brainstim/verify ---")
    verify = fetch("/api/metabci/brainstim/verify", method="POST")
    print(json.dumps(verify, ensure_ascii=False, indent=2))

    print("\n--- GET /api/metabci/brainflow/device-sources (Neuroscan 40导预留) ---")
    devices = fetch("/api/metabci/brainflow/device-sources")
    print(f"设备厂商: {devices.get('device_vendor')} | 导联: {devices.get('cap_channels')}")
    for src in devices.get("sources") or []:
        extra = ""
        if src.get("id") == "neuroscan_lsl":
            extra = f" | LSL={src.get('lsl_available')}"
        print(f"  - {src.get('id')}: {src.get('label')}{extra}")

    verified = int(verify.get("runtime_verified_count") or 0)
    if verified >= 3:
        print("\n✓ brainstim 严格验证 3/3 — 可对应评分表 10 分档")
        return 0
    if verified >= 1:
        print(f"\n△ brainstim 已验证 {verified}/3 — 至少 5 分档；录视频请在本地桌面环境重跑 verify 以拿满 3 项")
        return 0
    print("\n✗ brainstim 未通过有效 API 验证")
    return 1


if __name__ == "__main__":
    sys.exit(main())
