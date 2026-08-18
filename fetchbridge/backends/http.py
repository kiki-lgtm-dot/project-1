# -*- coding: utf-8 -*-
"""通用 HTTP 后端（自研，tier 2）—— 读取公开网页内容。"""

from __future__ import annotations

import urllib.request

from fetchbridge.base import Backend, TIER_SELF_BUILT
from fetchbridge.config import Config
from fetchbridge.models import ComplianceInfo, FetchRequest, FetchResult, ProbeResult
from fetchbridge.probe import probe_http

# 合规最佳实践：明确的 UA 与联系方式，便于站点方识别与联系
_DEFAULT_UA = "fetchbridge/0.1 (+https://github.com/kiki-lgtm-dot/fetchbridge)"


class HttpBackend(Backend):
    name = "http"
    tier = TIER_SELF_BUILT
    source_type = "self-built"

    def probe(self, config: Config) -> ProbeResult:
        # 探测网络与目标站点连通性（用公共可达地址，无副作用）
        return probe_http("https://example.com", timeout=5)

    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        req = urllib.request.Request(request.url, headers={"User-Agent": _DEFAULT_UA})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            return FetchResult(
                ok=True,
                platform=request.platform,
                backend=self.name,
                data={"content_type": "html", "length": len(body)},
                raw=body,
                compliance=ComplianceInfo(allowed=True, source_type=self.source_type),
            )
        except Exception as exc:  # noqa: BLE001
            return FetchResult(
                ok=False,
                platform=request.platform,
                backend=self.name,
                error=str(exc),
                compliance=ComplianceInfo(allowed=True, source_type=self.source_type),
            )
