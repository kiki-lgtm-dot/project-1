# -*- coding: utf-8 -*-
"""GitHub 渠道 —— 官方 API 优先（tier 1）。"""

from __future__ import annotations

from fetchbridge.backends.github_api import GitHubApiBackend
from fetchbridge.base import Channel


class GitHubChannel(Channel):
    name = "github"
    description = "GitHub 仓库信息"
    backends = [GitHubApiBackend()]  # 官方 API，唯一后端

    def can_handle(self, url: str) -> bool:
        return "github.com" in url
