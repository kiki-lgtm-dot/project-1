# -*- coding: utf-8 -*-
"""合规过滤 —— 抓取前的域名策略检查 + 抓取后的个人信息标记。

说明：本模块是「最小可行」实现。生产环境需接入：
  1. 完整 robots.txt 解析（本模块仅提供接入点说明）
  2. 法务维护的域名白名单/黑名单
  3. 成熟的 PII 识别（正则只是占位，生产应换 NER 模型）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from reach_enterprise.models import ComplianceInfo

# 个人信息识别（占位实现：邮箱 + 大陆手机号）
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_CN_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


@dataclass
class DomainPolicy:
    """域名策略：白名单优先；黑名单一票否决。"""

    allow: tuple = ()   # 允许的域名（后缀匹配）；空 = 不限制
    deny: tuple = ()    # 禁止的域名（后缀匹配）

    def evaluate(self, url: str) -> ComplianceInfo:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return ComplianceInfo(False, "无法解析域名", "public")

        for bad in self.deny:
            if host == bad or host.endswith("." + bad):
                return ComplianceInfo(False, f"域名命中禁止名单：{bad}", "public")

        if self.allow:
            for good in self.allow:
                if host == good or host.endswith("." + good):
                    return ComplianceInfo(True, "", "public")
            return ComplianceInfo(False, "域名不在允许名单内", "public")

        return ComplianceInfo(True, "", "public")


def detect_personal_data(text: str) -> bool:
    """检测文本中是否含疑似个人信息（占位实现）。"""
    if not text:
        return False
    return bool(_EMAIL_RE.search(text) or _PHONE_CN_RE.search(text))


def mark_personal_data(result) -> None:
    """抓取后标记个人信息（配合下游脱敏流程）。"""
    if result.raw:
        result.compliance.personal_data_detected = detect_personal_data(result.raw)
