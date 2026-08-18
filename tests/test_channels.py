# -*- coding: utf-8 -*-
"""渠道与路由核心测试。"""

from fetchbridge.channels import get_all_channels
from fetchbridge.channels.github import GitHubChannel
from fetchbridge.channels.web import WebChannel
from fetchbridge.config import Config


def test_all_channels_registered():
    names = {ch.name for ch in get_all_channels()}
    assert {"web", "github", "rss"} <= names


def test_web_can_handle_http():
    ch = WebChannel()
    assert ch.can_handle("https://example.com/article")
    assert not ch.can_handle("ftp://example.com")


def test_github_can_handle():
    ch = GitHubChannel()
    assert ch.can_handle("https://github.com/owner/repo")


def test_github_url_to_api():
    from fetchbridge.backends.github_api import GitHubApiBackend
    assert GitHubApiBackend._to_api_url(
        "https://github.com/psf/requests"
    ) == "https://api.github.com/repos/psf/requests"


def test_ordered_backends_override():
    ch = WebChannel()
    config = Config()
    # 强制指定首选后端
    config.data = {"web_backend": "jina"}
    ordered = ch.ordered_backends(config)
    assert ordered[0].name == "jina"


def test_compliance_domain_deny():
    from fetchbridge.compliance import DomainPolicy
    policy = DomainPolicy(deny=("blocked.com",))
    verdict = policy.evaluate("https://blocked.com/page")
    assert not verdict.allowed
    verdict2 = policy.evaluate("https://ok.com/page")
    assert verdict2.allowed
