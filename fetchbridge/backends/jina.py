# -*- coding: utf-8 -*-
"""Jina Reader 后端（tier 3，开源/第三方兜底）—— 把网页转成可读文本。

说明：属于第三方服务，企业生产使用前需单独评估其服务条款与数据出境问题。
"""

from __future__ import annotations

import urllib.parse
import urllib.request

from fetchbridge.base import Backend, TIER_FALLBACK
from fetchbridge.config import Config
from fetchbridge.models import ComplianceInfo, FetchRequest, FetchResult, ProbeResult

_ENDPOINT = "https://r.jina.ai/"


class JinaReaderBackend(Backend):
    name = "jina"
    tier = TIER_FALLBACK
    source_type = "fallback"

    def probe(self, config: Config) -> ProbeResult:
        req = urllib.request.Request(_ENDPOINT, headers={"User-Agent": "fetchbridge/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return ProbeResult("ok") if resp.status < 500 else ProbeResult("error", f"HTTP {resp.status}")
        except Exception as exc:  # noqa: BLE001
            return ProbeResult("unavailable", str(exc))

    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        target = _ENDPOINT + urllib.parse.quote(request.url, safe="")
        req = urllib.request.Request(target, headers={"User-Agent": "fetchbridge/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            return FetchResult(
                ok=True,
                platform=request.platform,
                backend=self.name,
                data={"content_type": "text", "length": len(text)},
                raw=text,
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
