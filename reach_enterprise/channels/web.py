# -*- coding: utf-8 -*-
"""Web 渠道 —— 读取公开网页。

后端优先级：自研 HTTP（首选）→ Jina Reader（兜底）。
合规：抓取前先过域名策略；默认无限制，企业可注入法务维护的白/黑名单。
"""

from __future__ import annotations

from reach_enterprise.backends.http import HttpBackend
from reach_enterprise.backends.jina import JinaReaderBackend
from reach_enterprise.base import Channel
from reach_enterprise.compliance import DomainPolicy, mark_personal_data
from reach_enterprise.config import Config
from reach_enterprise.models import FetchRequest, FetchResult


class WebChannel(Channel):
    name = "web"
    description = "公开网页阅读"
    backends = [HttpBackend(), JinaReaderBackend()]
    is_fallback = True  # 匹配一切 http(s)，必须最后匹配

    def __init__(self, policy: DomainPolicy | None = None):
        # 默认放行；生产环境注入法务维护的 DomainPolicy
        self.policy = policy or DomainPolicy()

    def can_handle(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        # 1. 合规过滤（域名策略）
        verdict = self.policy.evaluate(request.url)
        if not verdict.allowed:
            return FetchResult(
                ok=False,
                platform=self.name,
                backend="compliance",
                error=f"合规拦截：{verdict.reason}",
                compliance=verdict,
            )

        # 2. 路由到可用后端
        backend = self.route(config)
        if backend is None:
            return FetchResult(
                ok=False,
                platform=self.name,
                backend="none",
                error="无可用后端",
                compliance=verdict,
            )

        # 3. 抓取 + 个人信息标记
        result = backend.fetch(request, config)
        result.compliance = verdict
        mark_personal_data(result)
        return result
