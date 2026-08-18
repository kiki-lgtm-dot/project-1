# -*- coding: utf-8 -*-
"""命令行入口：fetchbridge doctor / fetch。"""

from __future__ import annotations

import argparse
import json
import sys

from fetchbridge import __version__
from fetchbridge.config import Config
from fetchbridge.core import FetchBridge
from fetchbridge.doctor import check_all, format_report, to_json
from fetchbridge.models import FetchRequest


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="fetchbridge",
        description="企业级多平台数据获取框架（官方 API 优先、路由、体检、审计）",
    )
    parser.add_argument("--version", action="version", version=f"fetchbridge {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_doctor = sub.add_parser("doctor", help="体检：输出各平台状态与在用后端")
    p_doctor.add_argument("--json", action="store_true", help="输出 JSON")

    p_fetch = sub.add_parser("fetch", help="抓取一个 URL")
    p_fetch.add_argument("url", help="目标 URL")
    p_fetch.add_argument("--platform", default="", help="显式指定平台（web/rss/github）")
    p_fetch.add_argument("--json", action="store_true", help="输出 JSON")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    config = Config()

    if args.command == "doctor":
        results = check_all(config)
        print(to_json(results) if args.json else format_report(results))
        return 0

    if args.command == "fetch":
        engine = FetchBridge(config)
        result = engine.fetch(FetchRequest(url=args.url, platform=args.platform))
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("ok" if result.ok else "error", "-", result.backend,
                  "-", result.error or result.data)
        return 0 if result.ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
