# -*- coding: utf-8 -*-
"""渠道注册表 —— 所有平台在此登记，doctor/引擎据此工作。"""

from reach_enterprise.base import Channel
from reach_enterprise.channels.github import GitHubChannel
from reach_enterprise.channels.rss import RSSChannel
from reach_enterprise.channels.web import WebChannel

ALL_CHANNELS: list = [WebChannel(), GitHubChannel(), RSSChannel()]


def get_channel(name: str):
    for ch in ALL_CHANNELS:
        if ch.name == name:
            return ch
    return None


def get_all_channels():
    return list(ALL_CHANNELS)


__all__ = ["Channel", "ALL_CHANNELS", "get_channel", "get_all_channels"]
