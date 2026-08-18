# -*- coding: utf-8 -*-
"""后端实现 —— 每个后端明确分级（官方 API / 自研 / 兜底）。"""

from fetchbridge.backends.github_api import GitHubApiBackend
from fetchbridge.backends.http import HttpBackend
from fetchbridge.backends.jina import JinaReaderBackend

__all__ = ["GitHubApiBackend", "HttpBackend", "JinaReaderBackend"]
