# -*- coding: utf-8 -*-
"""限频 + 重试 —— 对应方案的「调度层」基础能力。

刻意保持轻量：企业生产环境应替换为真正的任务队列（如 Celery/RQ），
本模块只提供框架内可用的最小实现，接口保持稳定。
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RateLimiter:
    """按平台做最小间隔限频。"""

    def __init__(self, min_interval_seconds: float = 1.0):
        self.min_interval = min_interval_seconds
        self._last: dict = {}

    def wait(self, platform: str) -> None:
        now = time.monotonic()
        last = self._last.get(platform)
        if last is not None:
            gap = now - last
            if gap < self.min_interval:
                time.sleep(self.min_interval - gap)
        self._last[platform] = time.monotonic()


def with_retry(
    fn: Callable[[], T],
    *,
    retries: int = 2,
    delay_seconds: float = 0.5,
    should_retry: Callable[[Exception], bool] = lambda e: True,
) -> T:
    """简单重试；生产环境应换指数退避 + 熔断。"""
    last_exc: Exception
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= retries or not should_retry(exc):
                raise
            time.sleep(delay_seconds)
    raise last_exc  # pragma: no cover —— 循环必然 return 或 raise
