# -*- coding: utf-8 -*-
"""引擎与审计测试。"""

import io

from reach_enterprise.audit import scrub_url
from reach_enterprise.config import Config
from reach_enterprise.core import ReachEngine
from reach_enterprise.models import FetchRequest


def test_scrub_url_credentials():
    assert scrub_url("https://user:pass@example.com/x") == "https://***@example.com/x"
    assert scrub_url("https://example.com/x") == "https://example.com/x"


def test_fetch_unknown_url():
    engine = ReachEngine(Config(), audit_stream=io.StringIO())
    result = engine.fetch(FetchRequest(url="not-a-url"))
    assert not result.ok


def test_compliance_blocked_domain():
    from reach_enterprise.channels.web import WebChannel
    from reach_enterprise.compliance import DomainPolicy

    ch = WebChannel(policy=DomainPolicy(deny=("blocked.com",)))
    from reach_enterprise.models import FetchRequest, FetchResult
    config = Config()
    result = ch.fetch(FetchRequest(url="https://blocked.com/x"), config)
    assert not result.ok
    assert "合规拦截" in result.error


def test_personal_data_detection():
    from reach_enterprise.compliance import detect_personal_data
    assert detect_personal_data("联系我 alice@example.com")
    assert detect_personal_data("电话 13812345678")
    assert not detect_personal_data("这是一段普通文本")


def test_resolve_specific_channel_before_fallback():
    """github.com 的 URL 应匹配 github 渠道，而不是被通用 web 渠道抢走。"""
    import io
    from reach_enterprise.core import ReachEngine
    from reach_enterprise.config import Config

    engine = ReachEngine(Config(), audit_stream=io.StringIO())
    ch = engine.resolve_channel(FetchRequest(url="https://github.com/psf/requests"))
    assert ch is not None
    assert ch.name == "github"

    # 普通网页仍走 web 渠道
    ch2 = engine.resolve_channel(FetchRequest(url="https://example.com/article"))
    assert ch2 is not None
    assert ch2.name == "web"
