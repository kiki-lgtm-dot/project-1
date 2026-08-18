# -*- coding: utf-8 -*-
"""统一数据模型 —— 所有渠道/后端都返回同一套结构，便于清洗、脱敏、入库。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FetchRequest:
    """一次标准化的数据获取请求。"""

    url: str
    platform: str = ""          # 渠道名（web / rss / github / ...）
    query: Optional[str] = None  # 搜索关键词（可选）
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.url = (self.url or "").strip()


@dataclass
class ComplianceInfo:
    """合规元数据 —— 每次抓取都记录，供审计与合规过滤使用。"""

    allowed: bool = True
    reason: str = ""
    source_type: str = "public"      # public | official-api | self-built | fallback
    robots_checked: bool = False
    personal_data_detected: bool = False


@dataclass
class FetchResult:
    """统一的数据出口结构。"""

    ok: bool
    platform: str
    backend: str
    data: Any = None                # 结构化结果
    raw: Optional[str] = None       # 原始文本（可空，用于审计留痕）
    error: str = ""
    compliance: ComplianceInfo = field(default_factory=ComplianceInfo)
    fetched_at: str = field(default_factory=_now_utc)
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "platform": self.platform,
            "backend": self.backend,
            "data": self.data,
            "error": self.error,
            "compliance": {
                "allowed": self.compliance.allowed,
                "reason": self.compliance.reason,
                "source_type": self.compliance.source_type,
                "robots_checked": self.compliance.robots_checked,
                "personal_data_detected": self.compliance.personal_data_detected,
            },
            "fetched_at": self.fetched_at,
            "latency_ms": self.latency_ms,
        }


@dataclass
class ProbeResult:
    """后端真实探活结果。"""

    status: str = "ok"  # ok | unavailable | error
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"
