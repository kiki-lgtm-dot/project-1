# -*- coding: utf-8 -*-
"""真实探活 —— 判断后端「现在是否可用」，而不是「看起来装了」。"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Callable, Optional

from reach_enterprise.models import ProbeResult


def probe_http(url: str, timeout: int = 5, headers: Optional[dict] = None) -> ProbeResult:
    """用一次真实 HTTP 请求探测后端健康。"""
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "reach-enterprise/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 400:
                return ProbeResult("ok")
            return ProbeResult("error", f"HTTP {resp.status}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return ProbeResult("unavailable", str(exc))


def probe_callable(fn: Callable[[], bool], label: str = "") -> ProbeResult:
    """执行一个无副作用的探测函数，区分异常。"""
    try:
        if fn():
            return ProbeResult("ok")
        return ProbeResult("unavailable", label or "探测返回 False")
    except Exception as exc:  # noqa: BLE001 —— 探活必须吞掉一切异常
        return ProbeResult("error", f"{label or '探测'}: {exc}")
