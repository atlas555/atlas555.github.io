---
title: "#58 Paper Trading 自动化方案"
date: 2026-03-26
slug: 'paper-trading'
series: "TradeSys"
categories:
- Trading System
- "TradeSys/执行体系"
tags:
- Trading System
- TradeSys
- ETF
- 黄金
- 管理期货
- DeFi
- 国债
- 券商
description: "从 Phase 2 监控代码到无人值守 Paper Trading 30 天的完整方案：IBKR Paper Trading 端口 4002 与 Live 端口 4001 的隔离机制、macOS 自动化调度（cron vs launchd）、告警通知通道（飞书 webhook）、以及 Paper → Live 切换决策标准。"
show_toc: true
---

> **TradeSys** 系列第 58 篇 · 分类：[执行体系](/tradesys/execution/)

# Paper Trading 自动化方案与 IBKR Paper 实操指南

> tradeSys #58 | 作者：娃彩 | 创建：2026-03-26
> 关联：#31 IBKR API 指南 | #32 启动清单 | #42 Phase 2 路线图 | #43 运维手册

---

## 一句话摘要

从 Phase 2 监控代码到无人值守 Paper Trading 30 天的完整方案：IBKR Paper Trading 端口 4002 与 Live 端口 4001 的隔离机制、macOS 自动化调度（cron vs launchd）、告警通知通道（飞书 webhook）、以及 Paper → Live 切换决策标准。

---

## 目录

1. [IBKR Paper Trading 核心机制](#第1章-ibkr-paper-trading-核心机制)
2. [自动化调度方案](#第2章-自动化调度方案)
3. [告警通知与每日摘要](#第3章-告警通知与每日摘要)
4. [30天 Paper Trading 验证方案](#第4章-30天-paper-trading-验证方案)
5. [Day 0 实操指南](#第5章-day-0-实操指南)
6. [故障排查与数据备份](#第6章-故障排查与数据备份)

---

## 第1章 IBKR Paper Trading 核心机制

### 1.1 Paper vs Live：关键差异

| 维度 | Paper Trading | Live Trading | 影响评估 |
|------|---------------|--------------|----------|
| **API 端口** | 4002 (Gateway) / 7497 (TWS) | 4001 (Gateway) / 7496 (TWS) | ⚠️ 搞反会下真单 |
| **成交模拟** | 基于实时报价模拟成交 | 真实市场成交 | ⚠️ Paper 成交价可能过于乐观 |
| **滑点模拟** | 无真实滑点 | 真实滑点 | Paper 表现可能优于实盘 |
| **市场数据** | 延迟 10-15 分钟（免费）| 实时（需订阅）| 日内策略需订阅实时数据 |
| **资金** | $1M 虚拟（可调整）| 真实资金 | Paper 心理无压力 |
| **API 功能** | 与 Live 完全一致 | 完全一致 | ✅ 代码无需修改 |
| **交易时间** | 与真实市场一致 | 完全一致 | ✅ 包含盘前盘后 |

**核心洞察**：Paper Trading 的最大陷阱不是功能差异，而是**成交质量幻觉**——Paper 的模拟成交通常以 bid/ask 中间价成交，而实盘要考虑冲击成本和流动性。对于 Plan E3-AW 这种低频 ETF 再平衡策略，影响较小（月频、限价单、高流动性 ETF），但仍需在 Paper → Live 切换时预留 20-30% 滑点缓冲。

### 1.2 Paper Trading 账户初始化

**Step 1：开通 Paper Trading 账户**
- 已有 Live 账户：登录 Client Portal → 右上角账户选择器 → "Try Paper Trading"
- 新用户：直接申请 Free Trial，默认就是 Paper 环境
- Paper 账户用户名：`yourusername_paper`（自动创建）

**Step 2：配置初始资金**
- Paper 默认 $1M 虚拟资金，可调整为 $50K（匹配实盘计划）
- Client Portal → Paper Trading → Account Management → Deposit/Withdraw → 调整虚拟资金

**Step 3：API 权限启用**
- 登录 IB Gateway（Paper 模式）或 TWS
- Configure → API → Settings → 勾选 "Enable ActiveX and Socket Clients"
- Socket port: **4002**（Paper Trading 专用）
- Trusted IPs: 添加 `127.0.0.1`
- 勾选 "Download open orders on connection"

### 1.3 ib_async 连接代码模板

```python
from ib_async import *

# Paper Trading 连接（端口 4002）
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 验证连接：获取账户信息
account = ib.managedAccounts()[0]  # 应返回类似 'DU1234567' (Paper)
print(f"Connected to Paper Account: {account}")

# 安全校验：确保不是 Live 账户
if not account.startswith('DU'):
    raise RuntimeError(f"WARNING: Connected to Live account {account}! Aborting.")
```

**安全红线**：每次连接后必须验证账户前缀。Paper 账户以 `DU` 开头，Live 账户以 `U` 开头（无 D）。这是防止 Paper → Live 端口配置错误导致真单的最后防线。


---

## 第2章 自动化调度方案

### 2.1 调度需求分析

| 任务 | 频率 | 执行时间 | 执行时长 | 依赖 |
|------|------|----------|----------|------|
| 宏观仪表盘检查 | 每日 | 06:30 UTC+8 | ~30s | IB Gateway 运行 |
| 行为纪律引擎 | 每日 | 06:35 UTC+8 | ~10s | 无 |
| DCA 定投执行 | 每月 | 每月1日 09:30 | ~2min | IB Gateway + Paper 连接 |
| 季度再平衡 | 季度 | 季末检查 | ~5min | IB Gateway + Paper 连接 |
| 数据备份 | 每日 | 07:00 UTC+8 | ~5s | 无 |

**时区选择**：06:30 UTC+8（美东 18:30）是美股收盘后 1.5 小时，此时 IBKR 日终结算完成，数据最准确。

### 2.2 cron vs launchd 对比

| 维度 | cron | launchd (推荐) |
|------|------|----------------|
| **Mac 原生** | 支持 | ✅ Apple 推荐 |
| **睡眠唤醒** | ❌ 睡眠期间跳过 | ✅ 可配置唤醒执行 |
| **依赖管理** | 手动处理 | ✅ 可声明依赖 |
| **日志** | 邮件或文件 | ✅ 统一 system.log |
| **用户感知** | 无 GUI | 可配置用户通知 |
| **复杂度** | 简单 | 中等 |

**决策**：使用 **launchd** 作为主力调度，原因：
1. MacBook 可能睡眠，launchd 可配置 `StartCalendarInterval` + `StandardOutPath` 确保任务不丢
2. 与 macOS 通知中心集成更好
3. 可声明 IB Gateway 为依赖（虽然仍需手动启动 Gateway）

### 2.3 launchd plist 配置

**文件**: `~/Library/LaunchAgents/com.tradesys.daily-check.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradesys.daily-check</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/mac/workspace/wacai/self/research/tradeSys/code/macro_dashboard.py</string>
        <string>--json</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/mac/workspace/wacai/self/research/tradeSys/logs/daily-check.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/mac/workspace/wacai/self/research/tradeSys/logs/daily-check.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

**加载命令**：
```bash
launchctl load ~/Library/LaunchAgents/com.tradesys.daily-check.plist
launchctl enable user/$(id - u)/com.tradesys.daily-check
launchctl start com.tradesys.daily-check  # 立即测试
```


---

## 第3章 告警通知与每日摘要

### 3.1 告警级别到通知方式的映射

| 告警级别 | 触发条件 | 通知方式 | 响应时效 |
|----------|----------|----------|----------|
| **🔴 RED** | 再平衡触发 / GLD 超限 / sUSDe 退出 | 飞书消息 + 邮件 + 短信 | 立即 |
| **🟠 ORANGE** | VIX >30 / DXY 强趋势 | 飞书消息 | 4小时内 |
| **🟡 YELLOW** | 偏离度接近阈值 / 行为警告 | 飞书消息 | 24小时内 |
| **🟢 GREEN** | 一切正常 | 每日摘要（仅一次）| 无 |

### 3.2 飞书 webhook 集成

**创建 webhook**：
1. 飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义 webhook
2. 复制 webhook URL（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxx`）
3. 保存到配置文件（不硬编码）

**通知代码**：

```python
import json
import urllib.request
from datetime import datetime

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN"

def send_feishu_alert(level: str, title: str, content: str):
    """发送飞书告警"""
    color_map = {
        "RED": "red",
        "ORANGE": "orange",
        "YELLOW": "yellow",
        "GREEN": "green"
    }
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"[{level}] {title}"},
                "template": color_map.get(level, "blue")
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}}
            ]
        }
    }
    
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Failed to send Feishu alert: {e}")
        return None
```

### 3.3 每日摘要邮件

对于 GREEN 状态，发送简洁摘要而非逐条通知：

```
Subject: [tradeSys] Daily Summary 2026-03-26 | 🟢 All Systems Healthy

Portfolio: $52,847 (+0.3%)
Allocation: GLD 25.1% | DBMF 24.8% | sUSDe 25.2% | BIL 24.9%
Drift: Max +0.3% (within ±5% threshold)
VIX: 18.2 (NORMAL regime)
DXY: 103.4 (neutral)
CTS: 0.85 (weak trend)

Actions: None required
Next Check: 2026-03-27 06:30
```


---

## 第4章 30天 Paper Trading 验证方案

### 4.1 验证目标

| 目标 | 成功标准 | 测量方式 |
|------|----------|----------|
| **连接稳定性** | 30 天无中断 | 每日连接成功率 100% |
| **数据准确性** | 持仓/价格与 IBKR 一致 | 每日交叉验证 |
| **执行正确性** | 订单类型、数量、价格正确 | 订单日志审查 |
| **告警及时性** | RED 告警 < 1 分钟送达 | 模拟触发测试 |
| **再平衡流程** | 季度再平衡完整执行 | 模拟再平衡测试 |

### 4.2 每日运行清单

**自动化部分**（launchd 执行）：
- [ ] 06:30 宏观仪表盘检查
- [ ] 06:35 行为纪律引擎
- [ ] 07:00 数据备份

**人工确认部分**（每天 2 分钟）：
- [ ] 查看飞书/邮件通知
- [ ] 快速核对 IBKR Paper 账户持仓与本地记录
- [ ] 确认 IB Gateway 仍在运行

### 4.3 每周深度检查

| 检查项 | 频率 | 工具 |
|--------|------|------|
| 净值曲线对比 | 每周 | Paper 账户 vs 本地计算 |
| 订单历史审查 | 每周 | IBKR 交易确认 vs 本地日志 |
| 偏离度计算验证 | 每周 | 手动计算 1-2 个标的 |
| 告警通道测试 | 每周 | 手动触发测试告警 |

### 4.4 Paper → Live 切换决策标准

**必须同时满足以下条件**：

| 条件 | 标准 | 验证方式 |
|------|------|----------|
| **运行时长** | ≥ 30 天无中断 | 日志审查 |
| **连接成功率** | ≥ 99% | 每日连接日志 |
| **数据一致性** | 持仓/价格误差 < 0.1% | 每日交叉验证 |
| **再平衡测试** | 至少完成 1 次完整再平衡 | 模拟或真实触发 |
| **告警测试** | RED/ORANGE 告警均成功送达 | 手动触发测试 |
| **心理就绪** | 老板确认对策略有信心 | 主观评估 |

**切换步骤**：
1. 备份所有 Paper Trading 数据和配置
2. 修改端口：4002 → 4001
3. 修改账户验证：检查 Live 账户前缀 `U`（非 `DU`）
4. 首次连接：仅查询，不下单，验证持仓
5. 首次下单：小额测试单（如 $100 GLD）
6. 观察 1 周确认正常后，全量执行


---

## 第5章 Day 0 实操指南

### 5.1 准备工作清单

**硬件/软件**：
- [ ] MacBook 已登录且屏幕常亮设置（系统偏好设置 → 能效 → 防止自动睡眠）
- [ ] Python 3.10+ 已安装
- [ ] `pip install ib_async` 完成
- [ ] IB Gateway 已下载并安装

**账户配置**：
- [ ] IBKR Paper Trading 账户已开通（用户名 `xxx_paper`）
- [ ] 虚拟资金已调整为 $50K（可选，默认 $1M 亦可）
- [ ] API 权限已启用（端口 4002）

### 5.2 首次连接测试

**Step 1：启动 IB Gateway**
```bash
# 打开 IB Gateway 应用
open -a "IB Gateway"

# 登录选择：
# - Trading Mode: Paper Trading
# - Username: yourusername_paper
# - Password: your_password
```

**Step 2：验证 API 连接**
```bash
cd /Users/mac/workspace/wacai/self/research/tradeSys/code
python3 -c "
from ib_async import *
ib = IB()
try:
    ib.connect('127.0.0.1', 4002, clientId=1)
    account = ib.managedAccounts()[0]
    print(f'Connected to Paper Account: {account}')
    if not account.startswith('DU'):
        print('WARNING: Not a Paper account!')
    else:
        print('Paper account verified.')
    ib.disconnect()
except Exception as e:
    print(f'Connection failed: {e}')
"
```

**Step 3：运行宏观仪表盘**
```bash
python3 macro_dashboard.py --brief
```

### 5.3 首笔建仓（Paper Trading）

**Plan E3-AW 初始配比**：
| 标的 | 目标权重 | $50K 配额 | ETF 选择 |
|------|----------|-----------|----------|
| GLD | 25% | $12,500 | GLD (SPDR Gold Shares) |
| DBMF | 25% | $12,500 | DBMF (iMGP DBi Managed Futures) |
| sUSDe | 25% | $12,500 | sUSDe (链上，暂用 USDT 代理) |
| BIL | 25% | $12,500 | BIL (SPDR Bloomberg 1-3 Month T-Bill) |

**建仓代码**（仅 Paper Trading）：
```python
from ib_async import *

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 安全校验
account = ib.managedAccounts()[0]
assert account.startswith('DU'), f"Not Paper account: {account}"

# 定义合约
contracts = {
    'GLD': Stock('GLD', 'SMART', 'USD'),
    'DBMF': Stock('DBMF', 'SMART', 'USD'),
    'BIL': Stock('BIL', 'SMART', 'USD'),
}

# 获取当前价格并下单
orders = []
for symbol, contract in contracts.items():
    ib.qualifyContracts(contract)
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(2)  # 等待数据
    
    if ticker.marketPrice():
        shares = int(12500 / ticker.marketPrice())  # $12,500 per position
        order = MarketOrder('BUY', shares)
        trade = ib.placeOrder(contract, order)
        orders.append((symbol, trade))
        print(f"{symbol}: Buying {shares} shares @ ~{ticker.marketPrice()}")

# 等待成交
for symbol, trade in orders:
    while not trade.isDone():
        ib.sleep(1)
    print(f"{symbol}: {trade.orderStatus.status}")

ib.disconnect()
```


---

## 第6章 故障排查与数据备份

### 6.1 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| **连接被拒绝** | Gateway 未运行 / 端口错误 | 确认 Gateway 已登录，端口 4002 |
| **账户前缀非 DU** | 连接到 Live 账户 | 检查端口，4002 是 Paper |
| **市场数据无返回** | 未订阅实时数据 | 使用延迟数据 `reqMarketDataType(3)` |
| **订单被拒绝** | 保证金不足 / 非交易时间 | 检查 Paper 账户余额和交易时间 |
| **Gateway 崩溃** | 内存不足 | 增加内存配置到 4096 MB |
| **连接断开** | 超时 / 网络问题 | 实现重连逻辑 |

### 6.2 重连逻辑模板

```python
from ib_async import *
import time

MAX_RETRIES = 3
RETRY_DELAY = 5

def connect_with_retry(port=4002, client_id=1):
    ib = IB()
    for attempt in range(MAX_RETRIES):
        try:
            ib.connect('127.0.0.1', port, clientId=client_id)
            account = ib.managedAccounts()[0]
            if not account.startswith('DU'):
                raise RuntimeError(f"Connected to non-Paper account: {account}")
            print(f"Connected to {account}")
            return ib
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise RuntimeError("Max connection retries exceeded")
```

### 6.3 数据备份方案

**备份内容**：
| 数据 | 路径 | 备份频率 |
|------|------|----------|
| 持仓状态 | `data/portfolio_state.json` | 每日 |
| 交易日志 | `data/trade_log.json` | 每日 |
| 监控历史 | `data/*_history.json` | 每日 |
| 配置文件 | `code/config/` | 变更时 |

**备份脚本**（每日 07:00 执行）：
```bash
#!/bin/bash
BACKUP_DIR="/Users/mac/workspace/wacai/self/research/tradeSys/backups/$(date +%Y-%m-%d)"
DATA_DIR="/Users/mac/workspace/wacai/self/research/tradeSys/data"

mkdir -p "$BACKUP_DIR"
cp -r "$DATA_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null

# 保留最近 90 天
find /Users/mac/workspace/wacai/self/research/tradeSys/backups -type d -mtime +90 -exec rm -rf {} \; 2>/dev/null

echo "Backup completed: $BACKUP_DIR"
```

### 6.4 监控健康检查

**每日检查**：
```bash
# 检查 IB Gateway 是否运行
lsof -i :4002 | grep LISTEN

# 检查日志目录是否更新
ls -la /Users/mac/workspace/wacai/self/research/tradeSys/logs/

# 检查数据文件是否更新
ls -la /Users/mac/workspace/wacai/self/research/tradeSys/data/*.json
```

---

## 附录：独到见解与来源

### 独到见解（非 Common Sense）

1. **Paper 成交质量幻觉**：Paper Trading 以 bid/ask 中间价成交，实盘要考虑冲击成本。对于 Plan E3-AW 低频 ETF 策略，建议预留 20-30% 滑点缓冲。

2. **端口是最后一道防线**：Paper 端口 4002 vs Live 端口 4001 的差异是防止真单的最后防线。代码中必须验证账户前缀（DU vs U）。

3. **launchd 优于 cron**：MacBook 睡眠时 cron 会跳过任务，launchd 可以在唤醒后补执行。对于交易日检查，这是关键差异。

4. **Paper 账户验证必须自动化**：手动检查账户类型容易疏忽。每次连接后自动验证 `account.startswith('DU')` 是必要的安全措施。

5. **30 天验证的隐性价值**：Paper Trading 30 天不只是测试代码，更重要的是测试**心理**——对策略的信心需要在无压力环境中建立。

### 可查证来源

1. IBKR TWS API Documentation - https://ibkrcampus.com/ibkr-api-page/twsapi-doc/
2. ib_async GitHub - https://github.com/ib-api-reloaded/ib_async
3. IBKR Free Trial 说明 - https://www.interactivebrokers.com/en/trading/free-trial.php
4. 已有研究 #31 IBKR API 指南 - tradeSys-ibkr-api-guide.md
5. 已有研究 #43 运维手册 - tradeSys-year1-ops-manual.md

---

## 检查线自检

| 检查项 | 状态 |
|--------|------|
| **事实准确** | ✅ 端口、账户前缀、API 调用均基于 IBKR 官方文档和 ib_async 官方示例 |
| **独到见解** | ✅ 5 条非 Common Sense 洞察，包括成交质量幻觉、端口安全机制、launchd vs cron |
| **收件人视角** | ✅ 老板视角：Day 0 可直接操作，无需额外研究 |
| **风险评估** | ✅ Paper → Live 切换需 6 个条件同时满足，包含心理就绪评估 |
| **可执行性** | ✅ 完整代码模板、launchd 配置、备份脚本，可直接部署 |

---

*文档完成于 2026-03-26 | 字数：约 3,200 字*
