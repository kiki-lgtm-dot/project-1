# -*- coding: utf-8 -*-
"""审计日志 —— 谁、何时、抓了什么、走哪个后端、是否合规，全程可追溯。

日志只写结构化 JSON 行，不写敏感字段（URL 中的凭据会被剥离）。
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from typing import TextIO

_CRED_RE = re.compile(r"(://)[^/@\s]+@")  # 剥离 URL 中的 user:pass@


def scrub_url(url: str) -> str:
    return _CRED_RE.sub(r"\1***@", url)


def emit(stream: TextIO, event: str, **fields) -> None:
    """输出一条审计记录。默认写到 stderr，生产环境可换文件/采集器。"""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **{k: v for k, v in fields.items()},
    }
    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    stream.flush()


def audit_fetch(stream: TextIO, result) -> None:
    """记录一次抓取结果（自动剥离 URL 凭据，不落 data 内容避免泄密）。"""
    emit(
        stream,
        "fetch",
        ok=result.ok,
        platform=result.platform,
        backend=result.backend,
        source_type=result.compliance.source_type,
        allowed=result.compliance.allowed,
        reason=result.compliance.reason,
        latency_ms=result.latency_ms,
        error=result.error or None,
    )


def audit_route(stream: TextIO, platform: str, backend: str, reason: str) -> None:
    """记录一次路由决策。"""
    emit(stream, "route", platform=platform, backend=backend, reason=reason)
