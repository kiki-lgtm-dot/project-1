# FetchBridge

企业级多平台数据获取框架（MVP / P1 试点版）。

以「官方 API 优先、凭据零明文、全程审计、合规过滤」为核心设计，提供多后端路由、真实探活与统一数据出口，供企业内部数据获取系统集成。

> ⚠️ **本仓库是 MVP 骨架，不是完整产品。** 生产落地需补齐的项见 [docs/enterprise-gaps.md](docs/enterprise-gaps.md)（含低成本、稳定方案）。

---

## 设计原则

| 原则 | 实现 |
|------|------|
| 官方 API 优先 | 后端分三级：`tier 1` 官方 API → `tier 2` 自研 → `tier 3` 开源兜底 |
| 多后端路由 | 每个平台 =「首选 + 备选」有序列表，按顺序真实探测，坏了自动切换 |
| 真实探活 | `probe()` 实际发起请求验证可用性，而非检查依赖是否存在 |
| 凭据零明文 | 密钥只走 `SecretProvider`（默认环境变量），配置文件强制剥离敏感字段 |
| 统一数据出口 | 所有结果统一为 `FetchResult`（含合规元数据、延迟、时间戳） |
| 全程审计 | 路由决策、抓取结果均输出结构化 JSON 审计日志 |
| 合规过滤 | 抓取前域名策略检查 + 抓取后个人信息标记 |

---

## 架构

```
┌──────────────────────────────────────────────┐
│  FetchBridge（引擎）  路由 · 限频 · 审计        │
├──────────────────────────────────────────────┤
│  Channel（渠道）  web / github / rss …         │  ← 一平台一模块，统一契约
├──────────────────────────────────────────────┤
│  Backend（后端，有序）  首选 → 备选            │  ← 真实探活，坏了切换
│   tier1 官方API → tier2 自研 → tier3 兜底      │
├──────────────────────────────────────────────┤
│  Compliance（合规）  域名策略 · PII 标记        │
└──────────────────────────────────────────────┘
```

## 目录结构

```
fetchbridge/
├── core.py        引擎（路由 + 抓取 + 审计 + 限频）
├── base.py        Channel / Backend 抽象契约
├── models.py      统一数据模型（FetchRequest / FetchResult / ComplianceInfo）
├── config.py      配置 + 密钥提供方（SecretProvider 抽象）
├── doctor.py      体检报告
├── audit.py       审计日志（URL 凭据剥离、结构化 JSON）
├── scheduler.py   限频 + 重试
├── probe.py       真实探活
├── compliance.py  域名策略 + 个人信息标记
├── backends/      http（自研）· github_api（官方）· jina（兜底）
└── channels/      web · github · rss
```

---

## 快速开始

```bash
# 安装（零第三方运行时依赖）
pip install -e .

# 体检（看每个平台当前状态与在用后端）
fetchbridge doctor
fetchbridge doctor --json

# 抓取
fetchbridge fetch https://github.com/psf/requests --json
fetchbridge fetch https://example.com/article --platform web --json

# 运行测试
pip install -e '.[dev]'
pytest tests/ -v
```

---

## 已实现渠道（MVP 范围）

| 渠道 | 后端 | 分级 | 说明 |
|------|------|------|------|
| web | http → jina | 自研 → 兜底 | 公开网页阅读，含域名合规过滤 |
| github | github-api | 官方 API | 仓库信息（无 Token 限 60 次/小时） |
| rss | http | 自研 | RSS/Atom 订阅解析 |

## 如何新增一个平台（契约）

1. 在 `backends/` 写后端，继承 `Backend`，实现 `probe()` 与 `fetch()`，声明 `tier`
2. 在 `channels/` 写渠道，继承 `Channel`，实现 `can_handle()`，挂上后端列表
3. 在 `channels/__init__.py` 的 `ALL_CHANNELS` 登记

**新增平台必须遵守**：官方 API 有就用官方（tier 1）；只抓公开数据；登录态/绕风控方案禁止进入代码库（需法务单独评估）。

---

## 合规红线（代码层面强制）

- 密钥不落盘：`Config._scrub_secrets` 会在写入前剔除任何疑似密钥字段
- 审计留痕：每次抓取输出结构化日志（URL 凭据自动剥离）
- 域名策略：渠道抓取前必须过 `DomainPolicy`（示例见 web 渠道）
- PII 标记：抓取后标记疑似个人信息，供下游脱敏（占位实现，生产需换 NER）

---

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| P1 试点 | 框架骨架 + web/github/rss 三渠道 + 审计 + 合规 | ✅ 本仓库 |
| P2 生产化 | 接密钥系统、监控告警、限频增强、完整合规解析 | ⏳ 待做（见 [docs/enterprise-gaps.md](docs/enterprise-gaps.md)） |
| P3 扩展 | 按需接更多平台（一律官方 API 优先） | ⏳ 待做 |

## 企业落地待办

MVP 未覆盖、需企业自行补充的部分（密钥管理、PII 识别、监控、调度等），
每一项的低成本、稳定解决方案详见 **[docs/enterprise-gaps.md](docs/enterprise-gaps.md)**。

## License

MIT
