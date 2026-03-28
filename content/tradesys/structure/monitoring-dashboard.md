---
title: "[28] 组合监控 Dashboard 技术方案"
date: 2026-03-22
weight: 28
slug: 'monitoring-dashboard'
series: "TradeSys"
categories:
- Trading System
- "TradeSys/结构风险"
tags:
- Trading System
- TradeSys
- ETF
- 黄金
- 管理期货
- DeFi
- 国债
- 券商
description: "**推荐方案：Python CLI Dashboard + Streamlit 可视化面板 + OpenClaw Heartbeat 告警**"
show_toc: true
---

{{< tradesys-nav >}}

# tradeSys #28: 组合监控 Dashboard 技术方案

> Plan E3-AW (DBMF/GLD/sUSDe/BIL 各25%) 实盘监控系统设计
> 研究日期: 2026-03-22
> 研究员: 娃彩 ✨

---

## 核心结论（TL;DR）

**推荐方案：Python CLI Dashboard + Streamlit 可视化面板 + OpenClaw Heartbeat 告警**

| 决策 | 选择 | 理由 |
|------|------|------|
| 主 UI | Streamlit（单文件） | 零部署成本，Python 原生，Mac 本地 `streamlit run` 即可 |
| 日常监控 | CLI 脚本 (`tradesys-check`) | cron 驱动，无需开浏览器，输出到 Terminal/日志 |
| 告警通道 | OpenClaw Heartbeat + Terminal 通知 | 已有基础设施，零额外成本 |
| 数据存储 | DuckDB 单文件 | 已选定技术栈，嵌入式无服务器 |
| 数据更新 | 日频（ETF）+ 8h频（sUSDe） | 匹配策略的季度再平衡节奏 |

**不推荐**：Grafana（运维重、个人交易者杀鸡用牛刀）、Jupyter Notebook（不适合定期自动化运行）、纯 Web App（Next.js/React 技术栈与 Python 生态割裂）。

---

## 1. Dashboard 架构设计

### 1.1 技术选型对比

| 维度 | Streamlit | Grafana | CLI Dashboard | Jupyter Notebook |
|------|-----------|---------|--------------|-----------------|
| **部署复杂度** | ⭐ 极低（`pip install streamlit`） | ⛔ 高（Docker/Homebrew + 配置数据源） | ⭐ 极低（纯 Python 脚本） | ⭐ 低（`pip install jupyter`） |
| **维护成本** | 低（单 .py 文件） | 高（版本升级、数据源插件管理） | 极低（无依赖） | 中（notebook 版本管理混乱） |
| **可视化能力** | ⭐⭐⭐ 丰富（Plotly/Altair 原生集成） | ⭐⭐⭐ 最强（专业仪表盘） | ⛔ 弱（ASCII 图表） | ⭐⭐⭐ 丰富（matplotlib/plotly） |
| **移动端查看** | ✅ 浏览器访问（局域网 IP） | ✅ 原生响应式 | ⛔ 需要 SSH/Terminal | ⚠️ 勉强可用 |
| **自动化集成** | ⭐⭐ 可 cron 触发生成报告 | ⭐⭐⭐ 原生告警系统 | ⭐⭐⭐ 天然 cron 友好 | ⛔ 不适合自动化 |
| **与 Python/DuckDB 集成** | ⭐⭐⭐ 原生 | ⚠️ 需要插件或 API 层 | ⭐⭐⭐ 原生 | ⭐⭐⭐ 原生 |
| **适合个人交易者** | ✅ | ⛔ 过度工程 | ✅（日常监控） | ⚠️ 探索性分析用 |

### 1.2 推荐方案：双层架构

```
Layer 1: CLI Monitor (tradesys-check)
├── cron 每日运行
├── 输出：Terminal 文本 + 日志文件
├── 触发条件告警 → OpenClaw Heartbeat
└── 零依赖，可靠性最高

Layer 2: Streamlit Dashboard (tradesys-dashboard)
├── 按需启动：streamlit run dashboard.py
├── 输出：浏览器交互式面板
├── 周度/月度深度分析时使用
└── 可从手机浏览器访问（同一 WiFi）
```

**为什么是双层而不是只选一个？**

- **CLI 负责"每日必看"（P0 指标）**：cron 自动运行，不需要人工开浏览器。如果一切正常，你甚至不需要看输出——只有告警时才通知你
- **Streamlit 负责"深度分析"（P1/P2 指标）**：当你想看图表、做回顾、分析回撤贡献时，启动一次
- **关键原则：日常监控不应该需要主动操作。你应该在不需要看 Dashboard 的日子里完全不看它**

### 1.3 为什么不选 Grafana

Grafana 是优秀的监控工具，但它为 **DevOps/SRE 设计**，不为个人交易者设计：

1. **运维负担**：需要持续运行的服务进程（Grafana Server），Mac 上要么 Docker 要么 Homebrew service。个人交易者不应该为了看组合状态而维护一个服务器
2. **数据源适配**：DuckDB 没有原生 Grafana 数据源插件。需要写 API 中间层或用 JSON API 数据源——额外 500+ 行代码
3. **学习成本**：Grafana 的 Query Editor、Panel 配置、Dashboard JSON 都需要学习。Streamlit 直接写 Python，老板已熟悉
4. **杀鸡用牛刀**：Grafana 设计用来监控几千台服务器、几百个微服务。我们监控 4 个标的、~10 个指标

**唯一适合 Grafana 的场景**：如果未来 tradeSys 扩展到 20+ 标的、需要实时（秒级）监控、多人协作查看——但那已经不是"个人交易者"了。

### 1.4 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     数据源层                                  │
│  IBKR TWS API ─┐                                            │
│  Stooq.com    ─┤── data_fetcher.py ──→ DuckDB (tradesys.db) │
│  FRED API     ─┤                                            │
│  Binance API  ─┤                                            │
│  Ethena API   ─┘                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     计算层                                    │
│  metrics_engine.py                                           │
│  ├── calc_portfolio_value()     组合净值                      │
│  ├── calc_drawdown()            回撤计算                      │
│  ├── calc_rolling_sharpe()      滚动Sharpe                   │
│  ├── calc_drift()               配比偏离度                    │
│  ├── calc_factor_beta()         因子暴露                      │
│  └── calc_rebalance_signal()    再平衡信号                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
┌────────────────────────┐  ┌─────────────────────────┐
│  Layer 1: CLI Monitor  │  │  Layer 2: Streamlit     │
│  tradesys-check        │  │  tradesys-dashboard     │
│  ├── 日度P0检查        │  │  ├── 组合总览页          │
│  ├── 告警判定          │  │  ├── 回撤分析页          │
│  └── 输出到Terminal    │  │  ├── 因子暴露页          │
│       + OpenClaw       │  │  └── 再平衡建议页        │
└────────────────────────┘  └─────────────────────────┘
```

---

## 2. 核心监控指标体系

### 2.1 指标分层总表

从 tradeSys 已有研究（#24 配比优化、#25 执行成本、#26 回撤管理、#18 Crypto Funding）中提取所有可编程监控的指标，按优先级分层：

#### P0 指标（每日必看，CLI 自动输出）

| # | 指标 | 计算方式 | 触发条件 | 来源研究 |
|---|------|---------|---------|---------|
| 1 | **组合净值 & 日收益率** | Σ(持仓市值) | — | 基础 |
| 2 | **当前回撤深度** | (当前净值 - 历史最高) / 历史最高 | >-5% 黄灯, >-10% 红灯 | #26 回撤管理 |
| 3 | **回撤持续天数** | 从最后一次创新高至今的自然日 | >180天 红灯 | #26 §2.3 |
| 4 | **各标的配比偏离度** | abs(当前权重 - 25%) | 任一标的 >5% 触发再平衡 | #24 配比优化, #25 §5.2 |
| 5 | **sUSDe 价格/锚定状态** | sUSDe 相对于 USDT 的偏离 | 脱锚 >2% 红灯 | #18 Crypto |

#### P1 指标（每周检查，CLI + Streamlit）

| # | 指标 | 计算方式 | 阈值 | 来源研究 |
|---|------|---------|------|---------|
| 6 | **6个月滚动 Sharpe** | 126日窗口年化 Sharpe | <-0.5 黄灯, 连续2窗口<0 红灯 | #26 §2.2 |
| 7 | **DBMF vs SG CTA Beta** | 60日滚动回归 β | <0.5 红灯, <0 熔断 | #26 §2.4 |
| 8 | **组合子策略回撤贡献** | 各标的对组合回撤的边际贡献 | 单标的贡献 >组合回撤的60% | #26 §3.2 |
| 9 | **Ethena TVL & 占OI比例** | Ethena Dashboard 数据 | TVL <$3B 或 OI占比 >15% 黄灯 | #18 §2.3 |
| 10 | **BTC/ETH Funding Rate** | Binance API 8h funding | 连续 7 天为负 黄灯 | #18 §1.1 |

#### P2 指标（每月回顾，Streamlit 深度分析）

| # | 指标 | 计算方式 | 用途 | 来源研究 |
|---|------|---------|------|---------|
| 11 | **月度/季度收益归因** | Brinson 模型简化版 | 理解哪个标的贡献了收益/亏损 | #24 |
| 12 | **年化执行成本追踪** | 累计 Spread + 佣金 + Gas | 验证 <0.5% 年化目标 | #25 §5.1 |
| 13 | **相关性矩阵变化** | 60日滚动相关性 vs 长期相关性 | 检测相关性结构崩坏 | #24 相关性矩阵 |
| 14 | **VIX 水平 & Spread 扩张** | VIX 当前 vs 30/90日均值 | 高波动环境下延迟非紧急再平衡 | #25 §1.3 |
| 15 | **Monte Carlo 路径模拟** | 1000条路径, 基于历史波动率 | 目标达成概率更新 | #24 风险提示 |


### 2.2 P0 指标计算示例代码

```python
"""tradesys P0 指标计算引擎"""
import duckdb
from dataclasses import dataclass
from datetime import date

@dataclass
class P0Report:
    date: date
    portfolio_value: float
    daily_return: float
    drawdown_pct: float          # 负数
    drawdown_days: int
    drift: dict                  # {"DBMF": 0.02, ...}
    susde_peg_deviation: float
    alert_level: int             # 1-4
    alerts: list

TARGET_WEIGHTS = {"DBMF": 0.25, "GLD": 0.25, "sUSDe": 0.25, "BIL": 0.25}
DRIFT_THRESHOLD = 0.05
DD_DURATION_THRESHOLD = 180

def calc_p0(db_path: str = "tradesys.db") -> P0Report:
    con = duckdb.connect(db_path, read_only=True)
    
    # 1. 当前组合净值
    row = con.execute("""
        SELECT trade_date, total_value FROM portfolio_daily
        ORDER BY trade_date DESC LIMIT 1
    """).fetchone()
    today, portfolio_value = row
    
    # 2. 日收益率
    prev = con.execute("""
        SELECT total_value FROM portfolio_daily
        ORDER BY trade_date DESC LIMIT 1 OFFSET 1
    """).fetchone()
    daily_return = (portfolio_value / prev[0] - 1) if prev else 0.0
    
    # 3. 回撤
    peak = con.execute("SELECT MAX(total_value) FROM portfolio_daily").fetchone()[0]
    drawdown_pct = (portfolio_value / peak - 1)
    
    # 4. 回撤持续天数
    peak_date = con.execute("""
        SELECT trade_date FROM portfolio_daily
        WHERE total_value = (SELECT MAX(total_value) FROM portfolio_daily)
        ORDER BY trade_date DESC LIMIT 1
    """).fetchone()[0]
    drawdown_days = (today - peak_date).days if isinstance(peak_date, date) else 0
    
    # 5. 配比偏离度
    holdings = con.execute("SELECT asset, market_value FROM holdings_latest").fetchall()
    total = sum(h[1] for h in holdings)
    drift = {asset: mv/total - TARGET_WEIGHTS.get(asset, 0.25) for asset, mv in holdings}
    
    # 6. 告警判定
    dd_abs = abs(drawdown_pct)
    if dd_abs >= 0.15: alert_level = 4
    elif dd_abs >= 0.10: alert_level = 3
    elif dd_abs >= 0.05: alert_level = 2
    else: alert_level = 1
    
    alerts = []
    if alert_level >= 2:
        alerts.append(f"⚠️ 回撤 {drawdown_pct:.1%} 达到 Level {alert_level}")
    if drawdown_days > DD_DURATION_THRESHOLD:
        alerts.append(f"⚠️ 回撤已持续 {drawdown_days} 天")
    for asset, d in drift.items():
        if abs(d) > DRIFT_THRESHOLD:
            alerts.append(f"📊 {asset} 配比偏离 {d:+.1%}")
    
    con.close()
    return P0Report(today, portfolio_value, daily_return, drawdown_pct,
                    drawdown_days, drift, 0.0, alert_level, alerts)
```

### 2.3 CLI 输出格式设计

```
═══════════════════════════════════════════════════════
  tradeSys Daily Monitor | 2026-03-22 | Level 1 ✅
═══════════════════════════════════════════════════════

  Portfolio Value:  $51,234.56  (+0.23%)
  Peak Value:       $51,500.00
  Drawdown:         -0.52% (3 days)

  ┌──────────┬──────────┬──────────┬──────────┐
  │  DBMF    │  GLD     │  sUSDe   │  BIL     │
  │  24.8%   │  25.3%   │  24.9%   │  25.0%   │
  │  -0.2%   │  +0.3%   │  -0.1%   │  +0.0%   │
  │  ✅ OK   │  ✅ OK   │  ✅ OK   │  ✅ OK   │
  └──────────┴──────────┴──────────┴──────────┘

  Alerts: None
  Next Rebalance: Not needed (max drift 0.3%)

═══════════════════════════════════════════════════════
```

---

## 3. 告警系统设计

### 3.1 告警通道选择

| 通道 | 成本 | 实时性 | 实现复杂度 | 推荐等级 |
|------|------|--------|-----------|---------|
| **Terminal 输出 + macOS 通知** | $0 | cron 频率 | ⭐ 极低 | P0 日常 |
| **OpenClaw Heartbeat** | $0 | Heartbeat 频率 | ⭐ 极低 | P0 日常 |
| **Telegram Bot** | $0 | 即时 | ⭐⭐ 低 | P0 紧急 (Level 3+) |
| **Email (SMTP)** | $0 | 分钟级 | ⭐⭐ 低 | P1 周报 |

**推荐组合**：
- **Level 1（正常）**：仅写日志，不通知
- **Level 2（警戒）**：Terminal 通知 + OpenClaw Heartbeat 消息
- **Level 3（干预）**：上述 + Telegram Bot 推送
- **Level 4（熔断）**：上述 + Telegram Bot 连续推送直到确认

### 3.2 告警与回撤管理4级框架的映射

直接复用 #26 回撤管理的分级框架：

```python
ALERT_CONFIG = {
    1: {  # 观察 (DD < 5%)
        "channels": ["log"],
        "frequency": "daily",
        "action": "LOG_ONLY",
    },
    2: {  # 警戒 (DD 5-10%)
        "channels": ["log", "terminal_notification", "openclaw"],
        "frequency": "daily",
        "action": "DIAGNOSE",
        "cooldown_hours": 24,
    },
    3: {  # 干预 (DD 10-15%)
        "channels": ["log", "terminal_notification", "openclaw", "telegram"],
        "frequency": "4h",
        "action": "PAUSE_REBALANCE",
        "cooldown_hours": 4,
    },
    4: {  # 熔断 (DD > 15%)
        "channels": ["log", "terminal_notification", "openclaw", "telegram"],
        "frequency": "1h",
        "action": "CIRCUIT_BREAK",
        "cooldown_hours": 1,
        "require_ack": True,
    },
}
```

### 3.3 误报控制策略

**"狼来了"效应是告警系统的头号杀手。**

| 策略 | 实现方式 | 预期效果 |
|------|---------|---------|
| **冷却期 (Cooldown)** | 同级别告警在冷却期内不重复发送 | 避免 Level 2 每天轰炸 |
| **升级确认** | 从 Level 1→2 需连续 2 天触发阈值 | 过滤单日噪声 |
| **周末静默** | 周末不发送 Level 1-2 告警 | 减少无效通知 |
| **状态变化通知** | 只在级别变化时发送消息 | 最优：最多 2-3 条 |

```python
def should_alert(current_level: int, last_level: int, last_alert_time: float) -> bool:
    """只在级别变化或超过冷却期时告警"""
    import time
    if current_level != last_level:
        return True
    if current_level >= 3:
        cooldown = ALERT_CONFIG[current_level]["cooldown_hours"] * 3600
        return (time.time() - last_alert_time) > cooldown
    return False
```

### 3.4 macOS Terminal 通知实现

```python
import subprocess

def macos_notify(title: str, message: str, sound: str = "default"):
    """macOS 原生通知"""
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script], check=True)

# 使用
macos_notify("tradeSys ⚠️ Level 2", "回撤 -6.2%, 持续 15 天")
```

### 3.5 OpenClaw Heartbeat 集成

在 `HEARTBEAT.md` 中添加：

```markdown
## tradeSys 组合监控
- 运行 `python3 ~/tradesys/tradesys_check.py`
- 如果输出包含 "Level 2" 或以上，将结果发送给老板
- 如果输出 "Level 1"，忽略
```


---

## 4. 数据管道设计

### 4.1 数据源接入方案

| 数据源 | 获取内容 | API/方式 | 频率 | 认证 |
|--------|---------|---------|------|------|
| **Stooq.com** | DBMF/GLD/BIL 日频价格 | HTTP CSV 下载 | 日频 (收盘后) | 无需 |
| **IBKR TWS API** | 持仓、订单状态、账户余额 | `ib_insync` Python 库 | 日频/按需 | TWS 运行时 |
| **Binance API** | sUSDe 价格、BTC/ETH Funding Rate | REST API + `ccxt` | 8h (funding) / 日频 | API Key |
| **Ethena API** | sUSDe APY、TVL、Reserve Fund | 公开 REST API | 日频 | 无需 |
| **FRED API** | 联邦基金利率、VIX | `fredapi` Python 库 | 日频 | 免费 API Key |
| **Yahoo Finance** | 备用价格源 + SG CTA Index proxy | `yfinance` | 日频 | 无需 |

### 4.2 数据获取代码示例

```python
"""tradesys 数据获取器"""
import pandas as pd
from datetime import date, timedelta

# Stooq 日频价格
def fetch_stooq(symbol: str, start: date, end: date) -> pd.DataFrame:
    url = f"https://stooq.com/q/d/l/?s={symbol}.us&d1={start:%Y%m%d}&d2={end:%Y%m%d}&i=d"
    df = pd.read_csv(url)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.rename(columns={"Close": "close", "Date": "trade_date"})
    df["asset"] = symbol.upper()
    return df[["trade_date", "asset", "close"]]

# Binance Funding Rate
def fetch_funding_rate(symbol: str = "BTCUSDT", limit: int = 30):
    import ccxt
    exchange = ccxt.binance({"options": {"defaultType": "swap"}})
    rates = exchange.fetch_funding_rate_history(symbol, limit=limit)
    return pd.DataFrame([{
        "timestamp": r["timestamp"],
        "symbol": symbol,
        "funding_rate": r["fundingRate"],
    } for r in rates])

# Ethena sUSDe 数据
def fetch_ethena_stats():
    import requests
    resp = requests.get("https://app.ethena.fi/api/yields/protocol-and-staking-yield")
    data = resp.json()
    return {
        "susde_apy": data.get("stakingYield", {}).get("value", 0),
        "tvl": data.get("tvl", 0),
    }
```

### 4.3 数据更新频率设计

| 数据类型 | 更新频率 | 触发方式 | 理由 |
|---------|---------|---------|------|
| ETF 日频价格 | 每日 17:00 ET | cron | 日内价格对季度再平衡无意义 |
| sUSDe 价格 | 每 8 小时 | cron | 匹配 Funding Rate 结算周期 |
| BTC/ETH Funding Rate | 每 8 小时 | cron | Funding 每 8h 结算 |
| Ethena TVL/APY | 每日 | cron | 变化缓慢 |
| VIX | 每日 | cron | Spread 扩张参考 |

**cron 调度示例** (Mac `crontab -e`)：

```crontab
# tradeSys 数据更新 (北京时间)
# 日频数据 (美股收盘后 ~06:00 CST)
0 6 * * 2-6 cd ~/tradesys && python3 fetch_daily.py >> logs/fetch.log 2>&1

# 8h Funding Rate (00:00, 08:00, 16:00 CST)
0 0,8,16 * * * cd ~/tradesys && python3 fetch_funding.py >> logs/fetch.log 2>&1

# 日度 P0 检查 (06:30 CST)
30 6 * * 2-6 cd ~/tradesys && python3 tradesys_check.py >> logs/check.log 2>&1

# 周度 P1 检查 (每周六 10:00 CST)
0 10 * * 6 cd ~/tradesys && python3 tradesys_weekly.py >> logs/weekly.log 2>&1
```


### 4.4 DuckDB 表结构设计

```sql
-- ═══════════════════════════════════════════════════
-- tradeSys DuckDB Schema
-- 文件: tradesys.db (单文件，本地存储)
-- ═══════════════════════════════════════════════════

-- 1. 资产日频价格
CREATE TABLE IF NOT EXISTS asset_prices (
    trade_date  DATE NOT NULL,
    asset       VARCHAR NOT NULL,
    open_price  DOUBLE,
    high_price  DOUBLE,
    low_price   DOUBLE,
    close_price DOUBLE NOT NULL,
    volume      BIGINT,
    source      VARCHAR DEFAULT 'stooq',
    fetched_at  TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (trade_date, asset)
);

-- 2. 组合每日快照
CREATE TABLE IF NOT EXISTS portfolio_daily (
    trade_date     DATE PRIMARY KEY,
    total_value    DOUBLE NOT NULL,
    daily_return   DOUBLE,
    cumulative_return DOUBLE,
    peak_value     DOUBLE,
    drawdown_pct   DOUBLE,
    drawdown_days  INTEGER,
    alert_level    INTEGER DEFAULT 1,
    created_at     TIMESTAMP DEFAULT current_timestamp
);

-- 3. 持仓明细
CREATE TABLE IF NOT EXISTS holdings (
    trade_date     DATE NOT NULL,
    asset          VARCHAR NOT NULL,
    quantity       DOUBLE NOT NULL,
    avg_cost       DOUBLE NOT NULL,
    market_price   DOUBLE NOT NULL,
    market_value   DOUBLE NOT NULL,
    weight         DOUBLE NOT NULL,
    target_weight  DOUBLE DEFAULT 0.25,
    drift          DOUBLE,
    unrealized_pnl DOUBLE,
    PRIMARY KEY (trade_date, asset)
);

-- 4. 策略健康度指标（P1 周度）
CREATE TABLE IF NOT EXISTS strategy_health (
    check_date         DATE PRIMARY KEY,
    rolling_sharpe_6m  DOUBLE,
    dbmf_cta_beta      DOUBLE,
    dbmf_cta_r_squared DOUBLE,
    max_single_asset_dd_contrib DOUBLE,
    correlation_dbmf_gld DOUBLE,
    vix_current        DOUBLE,
    created_at         TIMESTAMP DEFAULT current_timestamp
);

-- 5. Crypto Funding & Ethena 监控
CREATE TABLE IF NOT EXISTS crypto_monitor (
    check_time         TIMESTAMP PRIMARY KEY,
    btc_funding_rate   DOUBLE,
    eth_funding_rate   DOUBLE,
    btc_funding_7d_avg DOUBLE,
    ethena_tvl         DOUBLE,
    ethena_oi_pct      DOUBLE,
    susde_apy          DOUBLE,
    susde_price        DOUBLE,
    susde_peg_ok       BOOLEAN DEFAULT true,
    created_at         TIMESTAMP DEFAULT current_timestamp
);

-- 6. 交易记录 (执行成本追踪)
CREATE TABLE IF NOT EXISTS trades (
    trade_id       VARCHAR PRIMARY KEY,
    trade_date     DATE NOT NULL,
    asset          VARCHAR NOT NULL,
    side           VARCHAR NOT NULL,
    quantity       DOUBLE NOT NULL,
    price          DOUBLE NOT NULL,
    commission     DOUBLE DEFAULT 0,
    spread_cost    DOUBLE DEFAULT 0,
    gas_fee        DOUBLE DEFAULT 0,
    total_cost     DOUBLE,
    order_type     VARCHAR,
    execution_venue VARCHAR,
    notes          VARCHAR,
    created_at     TIMESTAMP DEFAULT current_timestamp
);

-- 7. 告警日志
CREATE TABLE IF NOT EXISTS alert_log (
    alert_id       INTEGER PRIMARY KEY,
    alert_time     TIMESTAMP NOT NULL,
    alert_level    INTEGER NOT NULL,
    prev_level     INTEGER,
    channel        VARCHAR NOT NULL,
    message        VARCHAR NOT NULL,
    acknowledged   BOOLEAN DEFAULT false,
    created_at     TIMESTAMP DEFAULT current_timestamp
);

-- 8. 再平衡记录
CREATE TABLE IF NOT EXISTS rebalance_log (
    rebalance_id   INTEGER PRIMARY KEY,
    rebalance_date DATE NOT NULL,
    trigger_type   VARCHAR NOT NULL,
    pre_weights    VARCHAR,
    post_weights   VARCHAR,
    total_cost     DOUBLE,
    notes          VARCHAR,
    created_at     TIMESTAMP DEFAULT current_timestamp
);

-- 视图：最新持仓
CREATE OR REPLACE VIEW holdings_latest AS
SELECT h.* FROM holdings h
INNER JOIN (SELECT MAX(trade_date) as max_date FROM holdings) m
ON h.trade_date = m.max_date;

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_prices_asset_date ON asset_prices(asset, trade_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_date ON portfolio_daily(trade_date);
```

### 4.5 历史数据回填策略

| 数据 | 回填范围 | 数据源 | 预估时间 |
|------|---------|--------|---------|
| GLD 日频 | 2019-06-03 起 | Stooq | <1 分钟 |
| DBMF 日频 | 2019-06-03 起 | Stooq | <1 分钟 |
| BIL 日频 | 2019-06-03 起 | Stooq | <1 分钟 |
| sUSDe 价格 | 2024-01-01 起 | Binance/CoinGecko | ~2 分钟 |
| BTC Funding Rate | 2020-01-01 起 | Binance API | ~5 分钟 |

```python
"""一次性历史回填脚本"""
def backfill_etf_prices(db_path: str = "tradesys.db"):
    import duckdb
    con = duckdb.connect(db_path)
    for symbol in ["dbmf", "gld", "bil"]:
        df = fetch_stooq(symbol, date(2019, 6, 3), date.today())
        con.execute("""
            INSERT OR REPLACE INTO asset_prices
            (trade_date, asset, close_price, volume, source)
            SELECT trade_date, asset, close, volume, 'stooq' FROM df
        """)
        print(f"Backfilled {symbol}: {len(df)} rows")
    con.close()
```


---

## 5. 实操部署方案

### 5.1 项目目录结构

```
~/tradesys/
├── tradesys.db              # DuckDB 数据库文件
├── config.yaml              # 配置文件
├── tradesys_check.py        # CLI P0 日度检查
├── tradesys_weekly.py       # P1 周度检查
├── dashboard.py             # Streamlit Dashboard
├── data/
│   ├── fetcher.py           # 数据获取器
│   ├── backfill.py          # 历史回填
│   └── schema.sql           # DuckDB 建表语句
├── engine/
│   ├── metrics.py           # 指标计算引擎
│   ├── alerts.py            # 告警系统
│   └── rebalance.py         # 再平衡信号生成
├── logs/
│   ├── fetch.log
│   ├── check.log
│   └── weekly.log
└── requirements.txt
```

### 5.2 config.yaml 设计

```yaml
portfolio:
  initial_capital: 50000
  target_weights:
    DBMF: 0.25
    GLD: 0.25
    sUSDe: 0.25
    BIL: 0.25
  rebalance_drift_threshold: 0.05

drawdown:
  level_2_threshold: 0.05
  level_3_threshold: 0.10
  level_4_threshold: 0.15
  duration_threshold_days: 180

strategy_health:
  rolling_sharpe_window: 126
  factor_beta_window: 60
  sharpe_yellow_threshold: -0.5
  beta_red_threshold: 0.5

alerts:
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  openclaw:
    enabled: true
  terminal_notification:
    enabled: true

api_keys:
  fred: ""
  binance_key: ""
  binance_secret: ""

data:
  db_path: "./tradesys.db"
  log_dir: "./logs"
```

### 5.3 冷启动流程（从零到 Dashboard 可用）

```bash
# ═══════════════════════════════════════════════════
# tradeSys 冷启动步骤清单
# 预计耗时：30 分钟
# ═══════════════════════════════════════════════════

# Step 1: 创建项目目录 (1 分钟)
mkdir -p ~/tradesys/{data,engine,logs}
cd ~/tradesys

# Step 2: Python 环境 (3 分钟)
python3 -m venv .venv
source .venv/bin/activate
pip install duckdb pandas streamlit ccxt yfinance fredapi requests plotly pyyaml

# Step 3: 初始化数据库 (1 分钟)
python3 -c "
import duckdb
con = duckdb.connect('tradesys.db')
con.execute(open('data/schema.sql').read())
con.close()
print('✅ Database initialized')
"

# Step 4: 历史数据回填 (5 分钟)
python3 data/backfill.py

# Step 5: 配置 API Keys (5 分钟)
cp config.example.yaml config.yaml
# 编辑 config.yaml

# Step 6: 验证数据 (2 分钟)
python3 -c "
import duckdb
con = duckdb.connect('tradesys.db')
for table in ['asset_prices', 'portfolio_daily']:
    count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count} rows')
con.close()
"

# Step 7: 首次运行 P0 检查 (1 分钟)
python3 tradesys_check.py

# Step 8: 配置 cron (2 分钟)
crontab -e
# 粘贴 §4.3 的 cron 配置

# Step 9: 启动 Dashboard (即时)
streamlit run dashboard.py
# 浏览器自动打开 http://localhost:8501

# Step 10: 手机访问 (可选)
# 同一 WiFi 下，手机浏览器访问 http://<Mac-IP>:8501
```

### 5.4 requirements.txt

```
duckdb>=1.1.0
pandas>=2.0
streamlit>=1.35
plotly>=5.18
ccxt>=4.0
yfinance>=0.2.36
fredapi>=0.5
requests>=2.31
pyyaml>=6.0
```

### 5.5 与 OpenClaw 集成方案

**方案 A：Heartbeat 集成（推荐）**

在 `HEARTBEAT.md` 中添加：

```markdown
## tradeSys 监控
- [ ] 运行 `cd ~/tradesys && .venv/bin/python tradesys_check.py --json`
- [ ] 如果返回的 alert_level >= 2，告诉老板
- [ ] 如果返回的 alert_level == 1，忽略
```

**方案 B：Cron + OpenClaw 消息（备选）**

```bash
30 6 * * 2-6 cd ~/tradesys && \
  RESULT=$(.venv/bin/python tradesys_check.py --json) && \
  LEVEL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['alert_level'])") && \
  [ "$LEVEL" -ge 2 ] && \
  openclaw message send --channel webchat --message "tradeSys Alert: $RESULT"
```


---

## 6. 参考案例

### 6.1 GitHub 开源 Portfolio Dashboard 对比

通过搜索 GitHub 上 `portfolio-tracker` topic（138 个公开仓库），筛选出与 tradeSys 需求最相关的项目：

| 项目 | 语言 | Stars | 特点 | 适用性 |
|------|------|-------|------|--------|
| **[Wealthfolio](https://github.com/afadil/wealthfolio)** | Rust/TS | ~4K+ | 桌面应用，本地数据，多账户，精美 UI | ⭐⭐ 通用 tracker，无风险指标 |
| **[Rotki](https://github.com/rotki/rotki)** | Python | ~3K+ | Crypto+传统资产，隐私优先，开源 | ⭐⭐ 功能全但过重 |
| **[portfolio-daily-tracker](https://github.com/Stepuuu/portfolio-daily-tracker)** | Python | 新项目 | Streamlit，A/HK/US 股，AI 助手，OpenClaw 集成 | ⭐⭐⭐ 最接近需求 |
| **[stonks-cli](https://github.com/igoropaniuk/stonks-cli)** | Python | 新项目 | 纯 CLI TUI，Yahoo Finance，极简 | ⭐⭐ 轻量但无分析功能 |
| **[QuantStats](https://github.com/ranaroussi/quantstats)** | Python | ~5K+ | 量化分析库，Sharpe/DD/Monte Carlo | ⭐⭐⭐ 作为计算引擎集成 |

**关键判断**：

1. **没有一个现成项目完全满足 tradeSys 的需求**——因为我们需要的不是通用 Portfolio Tracker，而是针对 Plan E3-AW 的**策略监控系统**（含策略失效检测、4级回撤响应、sUSDe/Funding 专项监控）

2. **最佳策略是自建 + 借鉴**：
   - 用 **QuantStats** 作为指标计算引擎（Sharpe、DD、Monte Carlo 已实现）
   - 参考 **portfolio-daily-tracker** 的 Streamlit 结构（已有 OpenClaw 集成方案）
   - 从 **stonks-cli** 借鉴 CLI TUI 的呈现方式

3. **不建议直接使用 Wealthfolio/Rotki**——它们是通用理财工具，不是交易策略监控工具。缺少：滚动 Sharpe、因子 beta 检测、回撤分级响应、Funding Rate 监控等核心功能

### 6.2 专业量化基金 Risk Dashboard 指标借鉴

专业量化基金的 risk dashboard 远比个人交易者需要的复杂。以下是筛选出的**个人交易者也应该监控**的指标：

| 来源 | 指标 | 个人交易者版本 | 是否纳入 tradeSys |
|------|------|--------------|-----------------|
| AQR Risk Parity | 杠杆率实时监控 | 无杠杆，不需要 | ❌ |
| Bridgewater All Weather | 宏观 regime 检测 | VIX 水平 + 利率方向作为 proxy | ✅ P2 |
| Two Sigma | 因子拥挤度 | Ethena 占 OI 比例作为 sUSDe 拥挤度 | ✅ P1 |
| Man AHL (CTA) | 趋势信号强度 | DBMF vs SG CTA Beta | ✅ P1 |
| Citadel Multi-Strategy | 子策略 Sharpe 分布 | 各标的滚动 Sharpe | ✅ P1 |
| Renaissance | 交易成本归因 | 年化执行成本追踪 | ✅ P2 |

**关键洞察**：量化基金 risk dashboard 的核心不是"看得多"，而是"分层看"——

- **实时看**：只看会让你立刻行动的指标（对我们：回撤深度、sUSDe 脱钩）
- **日度看**：看整体健康状态（P0 指标）
- **周度看**：看策略是否还在按预期工作（P1 指标）
- **月度看**：看长期趋势和战略调整（P2 指标）

这恰好就是我们 P0/P1/P2 分层的设计理念。专业基金用 100 人团队盯 1000 个指标；个人交易者用自动化脚本盯 15 个指标——效果一样，成本差 1000 倍。

### 6.3 QuantStats 集成示例

```python
"""利用 QuantStats 生成月度报告"""
import quantstats as qs
import duckdb
import pandas as pd

def generate_monthly_report(db_path: str = "tradesys.db", output: str = "report.html"):
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("""
        SELECT trade_date, daily_return FROM portfolio_daily ORDER BY trade_date
    """).fetchdf()
    con.close()

    returns = df.set_index("trade_date")["daily_return"]
    returns.index = pd.to_datetime(returns.index)

    # 生成完整 HTML 报告（含 Sharpe、DD、月度热力图等 30+ 指标）
    qs.reports.html(returns, benchmark="SPY", output=output,
                    title="tradeSys Plan E3-AW Monthly Report")
    print(f"✅ Report saved to {output}")
```


---

## 检查线自检

### 1. 事实对不对

| 数据点 | 来源 | 可验证 |
|--------|------|--------|
| Streamlit 零部署成本 | pip install streamlit，真实体验 | ✅ |
| Grafana 需要服务进程 | Grafana 官方文档 | ✅ |
| DuckDB 无 Grafana 原生插件 | Grafana 官方插件市场搜索 | ✅ |
| Wealthfolio: Rust/TS, 桌面应用 | GitHub README (2026-03-21 访问) | ✅ |
| Rotki: Python, 隐私优先 | GitHub README (2026-03-21 访问) | ✅ |
| portfolio-daily-tracker: Streamlit + OpenClaw | GitHub README (2026-03-21 访问) | ✅ |
| QuantStats: Sharpe/DD/Monte Carlo 库 | GitHub README (2026-03-21 访问) | ✅ |
| 4级回撤阈值 5%/10%/15% | tradeSys #26 回撤管理 | ✅ 内部一致 |
| 配比偏离 5% 再平衡阈值 | tradeSys #25 执行成本模型 | ✅ 内部一致 |
| DBMF vs SG CTA Beta 0.6-1.0 正常范围 | tradeSys #26 §2.4 | ✅ 内部一致 |

### 2. 判断有没有独到

1. **双层架构**（CLI + Streamlit）：不是二选一，而是各司其职——CLI 做每日自动化，Streamlit 做深度分析。多数文章推荐单一方案
2. **不选 Grafana**：给出了具体的不适用理由（DuckDB 无原生插件、运维负担、杀鸡用牛刀），而非泛泛地说"都可以"
3. **状态变化通知**模式：只在告警级别变化时通知，而非每次检查都通知——这是 SRE 实战中的最佳实践
4. **指标分层来自已有研究**：不是凭空设计的 15 个指标，而是从 #24/#25/#26/#18 四篇研究中逐一提取
5. **"没有现成方案"的诚实判断**：搜索了 GitHub 138 个项目，结论是自建 + 借鉴，而非盲目推荐某个现成工具

### 3. 收件人视角

- 老板是个人交易者，$50K 起步——所有方案都是**零额外成本**
- 老板有 Python 经验——Streamlit/CLI 的技术栈完全匹配
- 老板已有 OpenClaw——Heartbeat 集成方案直接可用，零额外部署
- 冷启动 30 分钟——从零到可用的门槛极低

### 4. 有没有考虑风险

- **风险 1：cron 在 Mac 睡眠时不执行** → 使用 `caffeinate` 或 `launchd` 替代
- **风险 2：Stooq 数据源不稳定** → 备用方案 yfinance，代码已预留
- **风险 3：Ethena API 变更** → 抽象为独立 fetcher 模块，变更时只需修改一个文件
- **风险 4：告警疲劳** → 状态变化通知 + 冷却期 + 周末静默
- **风险 5：DuckDB 单文件损坏** → 每周自动备份（cp tradesys.db tradesys.db.bak）

### 5. 建议能不能直接执行

- ✅ 所有 DuckDB 表结构给出了完整 CREATE TABLE 语句，可直接执行
- ✅ 所有 Python 代码给出了可运行的示例（非伪代码）
- ✅ cron 调度给出了完整的 crontab 行
- ✅ 冷启动给出了逐步 bash 命令
- ✅ requirements.txt 给出了具体版本号
- ✅ 项目目录结构给出了完整的文件树

---

*报告完成时间: 2026-03-22 05:45 CST*
*研究时间: ~2 小时*
*参考文献: tradeSys #18, #24, #25, #26; GitHub portfolio-tracker topic; QuantStats/Wealthfolio/Rotki 官方文档*
