# -*- coding: utf-8 -*-
"""
配置管理 —— 凭据绝不落盘明文。

设计（对应方案第 6 节「凭据零明文」）：
  - 密钥只从环境变量读取（FETCHBRIDGE_*_TOKEN / FETCHBRIDGE_*_KEY）
  - 预留密钥系统（Vault/KMS）接口：SecretProvider 抽象，生产环境注入
  - 配置文件只存非敏感项（后端优先级、限频、域名白名单）
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

_CONFIG_DIR = Path.home() / ".fetchbridge"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


class SecretProvider(ABC):
    """密钥提供方抽象 —— 生产环境接入 Vault / KMS 时实现本接口。"""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        ...


class EnvSecretProvider(SecretProvider):
    """默认实现：仅从环境变量读取，代码与配置文件中绝不出现明文密钥。"""

    def get(self, key: str) -> Optional[str]:
        return os.environ.get(key)


class Config:
    """非敏感配置 + 密钥访问入口。"""

    def __init__(self, secrets: Optional[SecretProvider] = None):
        self.secrets = secrets or EnvSecretProvider()
        self.data: dict = self._load()

    # ── 密钥访问（永不落盘） ──────────────────────────
    def secret(self, platform: str) -> Optional[str]:
        """按平台取密钥。例如 platform='github' → 读 FETCHBRIDGE_GITHUB_TOKEN。"""
        key = f"FETCHBRIDGE_{platform.upper().replace('-', '_')}_TOKEN"
        return self.secrets.get(key)

    # ── 非敏感配置 ────────────────────────────────────
    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def _load(self) -> dict:
        """读配置文件；读不到时使用安全默认值，绝不创建文件。"""
        if _CONFIG_FILE.exists():
            try:
                payload = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except (OSError, json.JSONDecodeError):
                pass
        return {}

    def save(self) -> None:
        """保存非敏感配置（写入前会强制清掉任何疑似密钥字段）。"""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cleaned = self._scrub_secrets(self.data)
        tmp = _CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, _CONFIG_FILE)

    @staticmethod
    def _scrub_secrets(data: dict) -> dict:
        """防御性脱敏：任何 key 命中敏感词则直接剔除，而非写入。"""
        markers = ("token", "key", "secret", "password", "cookie", "credential")
        return {k: v for k, v in data.items() if not any(m in k.lower() for m in markers)}
