# -*- coding: utf-8 -*-
"""GitHub 官方 REST API 后端（tier 1，首选）。

合规：官方 API，遵守其速率限制与条款；无 Token 时走公开接口（60 次/小时）。
Token 只从密钥系统（默认环境变量 REACH_GITHUB_TOKEN）读取，绝不落盘。
"""

from __future__ import annotations

import json
import urllib.request

from reach_enterprise.base import Backend, TIER_OFFICIAL
from reach_enterprise.config import Config
from reach_enterprise.models import ComplianceInfo, FetchRequest, FetchResult, ProbeResult

_API = "https://api.github.com"


class GitHubApiBackend(Backend):
    name = "github-api"
    tier = TIER_OFFICIAL
    source_type = "official-api"

    def _headers(self, config: Config) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "reach-enterprise",
        }
        token = config.secret("github")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def probe(self, config: Config) -> ProbeResult:
        req = urllib.request.Request(f"{_API}/rate_limit", headers=self._headers(config))
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if 200 <= resp.status < 400:
                    return ProbeResult("ok")
                return ProbeResult("error", f"HTTP {resp.status}")
        except Exception as exc:  # noqa: BLE001
            return ProbeResult("unavailable", str(exc))

    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        # request.url 形如 https://github.com/owner/repo → 转成 API 路径
        api_url = self._to_api_url(request.url)
        req = urllib.request.Request(api_url, headers=self._headers(config))
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return FetchResult(
                ok=True,
                platform=request.platform,
                backend=self.name,
                data=data,
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

    @staticmethod
    def _to_api_url(url: str) -> str:
        """把浏览器 URL 转成 REST API 端点（仅支持公开仓库主页）。"""
        path = url.split("github.com", 1)[-1].strip("/")
        if not path or "/" not in path:
            return f"{_API}/repos/{path or 'invalid/invalid'}"
        parts = path.split("/")
        owner, repo = parts[0], parts[1]
        return f"{_API}/repos/{owner}/{repo}"
