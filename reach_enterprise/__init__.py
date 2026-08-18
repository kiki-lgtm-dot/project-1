# -*- coding: utf-8 -*-
"""
reach-enterprise —— 企业级多平台数据获取框架（MVP）。

设计原则（对应《企业爬虫系统重写方案》）：
  1. 官方 API 优先，自研次之，开源工具仅作兜底
  2. 每个平台 =「首选 + 备选」有序后端列表，坏了自动切换
  3. 真实探活（不只是检查命令/依赖是否存在）
  4. 统一数据出口 + 合规过滤 + 全程审计
  5. 零第三方运行时依赖，便于企业安全审计
"""

__version__ = "0.1.0"

from reach_enterprise.core import ReachEngine

__all__ = ["ReachEngine", "__version__"]
