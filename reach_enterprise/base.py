# -*- coding: utf-8 -*-
"""渠道与后端抽象 —— 统一契约，一平台一模块。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from reach_enterprise.config import Config
from reach_enterprise.models import FetchRequest, FetchResult, ProbeResult

# 后端分级：1=官方API（首选） 2=自研（次选） 3=开源工具（兜底，需单独法务评估）
TIER_OFFICIAL = 1
TIER_SELF_BUILT = 2
TIER_FALLBACK = 3


class Backend(ABC):
    """单个后端实现。一个平台可挂多个后端，按顺序路由。"""

    name: str = ""
    tier: int = TIER_FALLBACK  # 越高优先级越低，必须显式声明
    source_type: str = "fallback"

    @abstractmethod
    def probe(self, config: Config) -> ProbeResult:
        """真实探活：现在是否可用。"""

    @abstractmethod
    def fetch(self, request: FetchRequest, config: Config) -> FetchResult:
        """执行一次数据获取。"""


class Channel(ABC):
    """一个平台渠道：持有有序后端列表，负责路由与体检。"""

    name: str = ""
    description: str = ""
    backends: List[Backend] = []  # 有序：index 0 = 首选
    is_fallback: bool = False    # True = 通用兜底渠道（匹配一切，最后才轮到它）

    def can_handle(self, url: str) -> bool:
        """默认按域名判断，子类可覆写。"""
        return False

    def ordered_backends(self, config: Config) -> List[Backend]:
        """候选后端，按声明顺序（支持用户配置强制指定首选）。"""
        forced = config.get(f"{self.name}_backend")
        if forced:
            for i, b in enumerate(self.backends):
                if b.name == forced:
                    return [b] + [x for j, x in enumerate(self.backends) if j != i]
        return list(self.backends)

    def route(self, config: Config) -> Optional[Backend]:
        """按顺序探测，返回第一个真正可用的后端；全挂返回 None。"""
        for backend in self.ordered_backends(config):
            if backend.probe(config).ok:
                return backend
        return None

    def check(self, config: Config) -> tuple:
        """体检：返回 (status, message)，status ∈ ok/warn/off。"""
        active = self.route(config)
        if active is not None:
            return "ok", f"可用（后端：{active.name}）"
        return "off", "所有后端均不可用"
