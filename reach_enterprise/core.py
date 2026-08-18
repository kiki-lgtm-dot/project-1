# -*- coding: utf-8 -*-
"""ReachEngine —— 引擎入口：路由 + 抓取 + 审计 + 限频。"""

from __future__ import annotations

import sys
import time
from typing import Optional

from reach_enterprise.audit import audit_fetch, audit_route
from reach_enterprise.channels import get_all_channels, get_channel
from reach_enterprise.config import Config
from reach_enterprise.models import FetchRequest, FetchResult
from reach_enterprise.scheduler import RateLimiter


class ReachEngine:
    """统一数据获取入口。生产环境应注入 SecretProvider 与审计流。"""

    def __init__(self, config: Optional[Config] = None, audit_stream=None):
        self.config = config or Config()
        self.audit_stream = audit_stream or sys.stderr
        self.limiter = RateLimiter(min_interval_seconds=1.0)

    def resolve_channel(self, request: FetchRequest):
        """按 platform 显式指定；否则按 URL 自动识别。

        两遍匹配：先匹配具体渠道（github/rss 等），最后才轮到通用
        兜底渠道（web，is_fallback=True），避免宽泛匹配抢占具体平台。
        """
        if request.platform:
            return get_channel(request.platform)
        channels = get_all_channels()
        for ch in channels:
            if not ch.is_fallback and ch.can_handle(request.url):
                return ch
        for ch in channels:
            if ch.is_fallback and ch.can_handle(request.url):
                return ch
        return None

    def fetch(self, request: FetchRequest) -> FetchResult:
        """执行一次抓取，完整走 路由→限频→抓取→审计 链路。"""
        request.platform = request.platform or ""
        channel = self.resolve_channel(request)
        if channel is None:
            result = FetchResult(ok=False, platform=request.platform, backend="none",
                                 error=f"无渠道可处理：{request.url}")
            audit_fetch(self.audit_stream, result)
            return result

        request.platform = channel.name
        self.limiter.wait(channel.name)

        # 路由决策 + 审计
        backend = channel.route(self.config)
        if backend is None:
            audit_route(self.audit_stream, channel.name, "none", "所有后端探测失败")
            result = FetchResult(ok=False, platform=channel.name, backend="none",
                                 error="所有后端均不可用")
            audit_fetch(self.audit_stream, result)
            return result
        audit_route(self.audit_stream, channel.name, backend.name, "首个可用后端")

        start = time.monotonic()

        # 渠道自带合规过滤与解析逻辑（如 web 渠道的域名策略）
        if hasattr(channel, "fetch"):
            result = channel.fetch(request, self.config)
        else:
            result = backend.fetch(request, self.config)

        result.latency_ms = int((time.monotonic() - start) * 1000)
        audit_fetch(self.audit_stream, result)
        return result
