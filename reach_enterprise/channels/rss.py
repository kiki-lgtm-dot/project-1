# -*- coding: utf-8 -*-
"""RSS 渠道 —— 解析 RSS/Atom 订阅源（公开数据，自研后端）。"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from reach_enterprise.backends.http import HttpBackend
from reach_enterprise.base import Channel
from reach_enterprise.config import Config
from reach_enterprise.models import ComplianceInfo, FetchRequest, FetchResult


class RSSChannel(Channel):
    name = "rss"
    description = "RSS/Atom 订阅源"
    backends = [HttpBackend()]

    def can_handle(self, url: str) -> bool:
        # RSS 源无固定域名，仅按常见特征判断；引擎通常显式指定 platform=rss
        lowered = url.lower()
        return any(s in lowered for s in ("/feed", "/rss", ".xml", "atom"))

    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        backend = self.route(config)
        if backend is None:
            return FetchResult(ok=False, platform=self.name, backend="none", error="无可用后端")

        http_result = backend.fetch(request, config)
        if not http_result.ok:
            return http_result

        try:
            items = self._parse_feed(http_result.raw or "")
        except ET.ParseError as exc:
            return FetchResult(
                ok=False, platform=self.name, backend=backend.name,
                error=f"RSS 解析失败：{exc}",
                compliance=ComplianceInfo(allowed=True, source_type=backend.source_type),
            )

        return FetchResult(
            ok=True,
            platform=self.name,
            backend=backend.name,
            data={"items": items},
            raw=http_result.raw,
            compliance=ComplianceInfo(allowed=True, source_type=backend.source_type),
        )

    @staticmethod
    def _parse_feed(raw: str) -> list:
        root = ET.fromstring(raw)
        items = []
        for node in root.iter():
            if node.tag.endswith(("item", "entry")):
                title = node.findtext("title") or ""
                link = node.findtext("link") or ""
                if not link and node.find("link") is not None:
                    link = node.find("link").get("href", "")
                items.append({"title": title.strip(), "link": link.strip()})
        return items[:20]
