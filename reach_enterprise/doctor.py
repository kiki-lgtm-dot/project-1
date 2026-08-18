# -*- coding: utf-8 -*-
"""体检 —— 输出每个平台当前状态与在用后端。"""

from __future__ import annotations

import json

from reach_enterprise.channels import get_all_channels
from reach_enterprise.config import Config


def check_all(config: Config) -> dict:
    results = {}
    for ch in get_all_channels():
        try:
            status, message = ch.check(config)
        except Exception as exc:  # noqa: BLE001 —— 单个渠道异常不能拖垮整体
            status, message = "error", f"体检异常：{exc}"
        results[ch.name] = {
            "status": status,
            "name": ch.description,
            "message": message,
            "backends": [b.name for b in ch.backends],
        }
    return results


def format_report(results: dict) -> str:
    lines = ["Reach Enterprise 状态", "=" * 40]
    for name, r in results.items():
        icon = {"ok": "✅", "warn": "⚠️", "off": "❌", "error": "❌"}.get(r["status"], "?")
        lines.append(f"{icon} {r['name']} — {r['message']}")
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    lines.append("=" * 40)
    lines.append(f"{ok}/{len(results)} 个渠道可用")
    return "\n".join(lines)


def to_json(results: dict) -> str:
    return json.dumps(results, ensure_ascii=False, indent=2)
