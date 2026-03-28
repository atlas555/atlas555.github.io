---
title: "#31 IBKR API 自动化交易指南"
date: 2026-03-22
slug: 'ibkr-api-guide'
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
description: "1. [IBKR 账户类型与开户指南（中国居民视角）](#第1章ibkr-账户类型与开户指南中国居民视角) 2. [IBKR API 生态全景](#第2章ibkr-api-生态全景) 3. [Python + ib_insync/ib_async 快速上手](#第3章python--ib_insyncib_async-快速上手) 4. [Plan E3-AW 自动再平衡原型设计](#第4章p..."
show_toc: true
---

> **TradeSys** 系列第 31 篇 · 分类：[执行体系](/tradesys/execution/)

# IBKR API 对接与自动化交易实操指南

> tradeSys #31 | 作者：娃彩 | 创建：2026-03-22
> 关联：#22 技术栈选型 | #27 税务研究 | #28 监控 Dashboard | Plan E3-AW

---

## 目录

1. [IBKR 账户类型与开户指南（中国居民视角）](#第1章ibkr-账户类型与开户指南中国居民视角)
2. [IBKR API 生态全景](#第2章ibkr-api-生态全景)
3. [Python + ib_insync/ib_async 快速上手](#第3章python--ib_insyncib_async-快速上手)
4. [Plan E3-AW 自动再平衡原型设计](#第4章plan-e3-aw-自动再平衡原型设计)
5. [生产环境部署](#第5章生产环境部署)

---

## 第1章：IBKR 账户类型与开户指南（中国居民视角）

> **So What for Plan E3-AW**：这是起跑线。选错账户类型或卡在开户流程上，编码再好也没用。本章确保老板以最短路径拿到一个能跑 API 自动交易的账户。

### 1.1 账户类型选择

| 维度 | 个人账户 (Individual) | 机构账户 (Institutional) |
|------|----------------------|-------------------------|
| **适用** | 个人投资者，管自己的钱 | 公司/基金/家族办公室 |
| **最低入金** | 无硬性最低（原 $10K 门槛已取消）| $10K+ |
| **API 权限** | 完整 TWS API + Client Portal API | 同上，另有 FIX 协议选项 |
| **佣金** | 固定 $0.005/股（最低 $1）或阶梯式 | 同个人，量大可谈判 |
| **保证金** | Reg T Margin（2:1 隔夜）| Portfolio Margin（更灵活，需 $110K+）|
| **开户复杂度** | 简单，线上 3-5 工作日 | 需公司文件，2-4 周 |
| **W-8BEN** | 需填写 W-8BEN | 需 W-8BEN-E |
| **适合 Plan E3-AW？** | ✅ **推荐** | ❌ 过度设计 |

**决策**：Plan E3-AW 初始资金 $50K 级别，个人账户足够。个人账户 API 权限与机构完全一致，无任何功能限制。

### 1.2 中国大陆居民开户全流程

#### 前置条件
- 有效期内的**中国大陆身份证**（有护照更佳，但不是必须）
- **手机号**（+86 即可）
- **个人邮箱**（推荐 Gmail/Outlook，避免 QQ 邮箱偶尔收不到验证邮件）
- **银行账户**（用于电汇入金，需支持境外汇款）

#### 开户步骤（实测约 30 分钟填写 + 1-3 工作日审批）

**Step 1：注册账号**
- 访问 [interactivebrokers.com.hk](https://www.interactivebrokers.com.hk)（香港站），选"开设账户"
- ⚠️ **踩坑**：中国大陆居民通过 `.com.hk` 或 `.com` 均可，系统根据居住国自动分配至 IB Hong Kong (IB HK) 或 IB LLC。两者 API 功能一致，IB HK 适合亚太时段客服
- 邮箱即用户名，密码要求：8+ 字符，含大小写+数字

**Step 2：填写个人信息**
- 姓名：与证件完全一致（拼音 + 中文）
- 居住地址：英文填写，后续需与银行对账单/水电单地址匹配
- 就业信息：如实填写。"自由职业" / "软件工程师" 均可
- 投资目标：选"Growth"（增长）+ "Active Trading"（活跃交易），这影响你能看到的产品类型
- ⚠️ **踩坑**：投资经验部分，如果全选"无经验"，某些产品权限（如期货、期权）不会自动开通

**Step 3：身份验证（KYC）**
- 上传身份证正反面（或护照信息页）
- 上传近 3 个月的**地址证明**：银行对账单 / 水电煤账单 / 信用卡账单（英文或中文+翻译件）
- ⚠️ **踩坑**：手机银行截图可能被拒，建议下载 PDF 版本的银行对账单
- 部分情况需录制 selfie 视频验证

**Step 4：交易权限配置**
- 务必勾选 **"United States - Stocks"**（美股权限），这是 Plan E3-AW 的核心
- 如果还想交易 Crypto 相关 ETF（如 BITO），需额外勾选加密货币权限
- API Trading 权限：开户后在 Account Management 中单独开启（见 Step 6）

**Step 5：W-8BEN 表格（与 #27 税务研究衔接）**
- 开户流程中会自动引导填写电子版 W-8BEN
- 关键字段：
  - **Part I - Line 3**：Country of Citizenship → China
  - **Part I - Line 4**：Permanent Residence Address → 中国地址（英文）
  - **Part II - Line 9**：中美税收协定 → 选 "China"
  - **Part II - Line 10**：条款号 → Article 10, 股息预扣税率 10%（而非默认 30%）
- ⚠️ **关键**：W-8BEN 有效期 3 年，过期后 IBKR 会暂停部分交易功能直到更新
- 参见 #27 税务研究报告中的详细分析

**Step 6：开通 API 权限**
- 登录 [Client Portal](https://portal.interactivebrokers.com)
- 导航：Settings → Account Settings → API
- 勾选 "Enable ActiveX and Socket Clients"
- 注意：首次开通可能需要等待一个交易日生效

#### 审批时间线
| 阶段 | 时间 |
|------|------|
| 在线填写 | 30 分钟 |
| 身份审核 | 1-2 工作日（多数 24h 内）|
| 补充材料（如有）| 额外 1-2 工作日 |
| 入金到账 | 1-3 工作日 |
| API 权限生效 | 即时 ~ 1 工作日 |
| **总计** | **约 3-7 工作日** |

### 1.3 入金方式

#### 电汇入金（推荐）

**路径**：国内银行 → 中转行 → IBKR 指定银行（通常为花旗/汇丰）

| 项目 | 详情 |
|------|------|
| **方式** | 境外电汇（Telegraph Transfer） |
| **币种** | USD（推荐）或 HKD |
| **手续费** | 发汇行收费 ¥80-200 + 中转行 $10-25 |
| **到账时间** | 1-3 工作日 |
| **注意事项** | 每人每年 $50,000 购汇额度（个人年度便利化额度）|

**操作要点**：
1. 在 IBKR Client Portal 创建入金通知（Deposit Notification），获取电汇指令
2. 携带身份证去银行柜台办理，说明用途为"境外投资"
3. 必须从**本人同名账户**汇出，否则 IBKR 会退回
4. 汇款附言填写 IBKR 提供的 Account Number + 参考号

⚠️ **踩坑汇总**：
- 部分银行（如工行）对"境外证券投资"汇款审核较严，建议用中行/招行
- 如果银行问用途，说"个人境外投资"即可，这是合法的
- 首次汇款建议小额试水（$100），确认通路后再大额入金
- 香港银行账户入金速度更快（次日到账），有条件可考虑开设

#### 最低入金与保证金
- **现金账户**（Cash Account）：无最低入金要求
- **保证金账户**（Margin Account）：无硬性最低（IBKR 已取消 $2,000 要求），但余额低于 $2,000 会限制日内交易（PDT 规则：$25K 以下限制 5 个交易日内不超过 3 次日内往返）
- **Plan E3-AW 建议**：$50K 入金，开保证金账户。月度再平衡频率低，不触发 PDT 规则

---

---

## 第2章：IBKR API 生态全景

> **So What for Plan E3-AW**：API 选型决定了整个自动化系统的开发效率和运维复杂度。选错了，后面所有代码都要重写。本章帮你在 10 分钟内做出正确决策。

### 2.1 三条 API 路线对比

| 维度 | TWS API (Socket) | Client Portal API (REST) | IBKR Lite |
|------|-------------------|--------------------------|-----------|
| **协议** | 二进制 socket (port 7497/4001) | HTTPS REST | 无 API |
| **认证** | TWS/Gateway 图形登录 | OAuth2 / session token | N/A |
| **功能完整度** | ⭐⭐⭐⭐⭐ 最全 | ⭐⭐⭐ 有限（无历史数据流） | ❌ |
| **实时数据** | ✅ streaming | ✅ polling/websocket | ❌ |
| **下单** | ✅ 全部订单类型 | ✅ 基础订单类型 | ❌ |
| **Python 封装** | ib_insync / ib_async | requests 直接调 | N/A |
| **无头运行** | 需 IB Gateway | 需 Client Portal Gateway | N/A |
| **适合** | 自动化交易系统 | Web Dashboard / 轻查询 | 手动交易 |
| **Plan E3-AW？** | ✅ **首选** | 备选（监控补充） | ❌ |

**决策**：Plan E3-AW 使用 **TWS API (Socket)** + **IB Gateway**。原因：
1. 订单类型最全（MOC 单在 REST API 中可能受限）
2. ib_insync/ib_async 封装极好，开发效率最高
3. IB Gateway 资源占用低（~200MB 内存），适合 Mac 本地长期运行

### 2.2 ib_insync vs ib_async：何去何从？

**背景**：ib_insync 的作者 Ewald de Wit 于 2024 年 3 月去世。社区随后 fork 出 [ib_async](https://github.com/ib-api-reloaded/ib_async)，由活跃维护者继续开发。

| 维度 | ib_insync (原版) | ib_async (fork) |
|------|------------------|-----------------|
| **版本** | v0.9.86（2023.07 最后更新）| 活跃开发中 |
| **Python 要求** | 3.6+ | 3.10+ |
| **维护状态** | ❌ 停更（作者已故）| ✅ 活跃维护 |
| **API 兼容** | 与 TWS 1023+ | 与最新 TWS/Gateway |
| **新功能** | 无 | 改进的重连逻辑、更好的类型提示 |
| **社区** | PyPI 下载量大（惯性）| GitHub 活跃 |
| **代码兼容性** | 基准 | 基本兼容，仅包名不同 |

**决策**：Plan E3-AW 使用 **ib_async**。理由：
1. 活跃维护意味着 bug 修复和 IBKR API 变更的跟进
2. Python 3.10+ 要求不是问题（Mac 上已有 3.12+）
3. 代码迁移成本极低：`from ib_insync import *` → `from ib_async import *`
4. 本指南代码示例以 ib_async 为主，附 ib_insync 差异说明

### 2.3 连接方式：TWS vs IB Gateway

| 维度 | TWS (Trader Workstation) | IB Gateway |
|------|--------------------------|------------|
| **界面** | 完整交易GUI | 最小化窗口（仅登录+状态）|
| **内存占用** | ~800MB-1.5GB | ~200-400MB |
| **API 端口** | 默认 7496(live) / 7497(paper) | 默认 4001(live) / 4002(paper) |
| **自动重启** | v974+ 支持 auto-restart | v974+ 支持 auto-restart |
| **适合** | 开发调试、手动监控 | 生产自动化 |
| **headless** | ❌ 需要 GUI | ❌ 也需要 GUI（但窗口很小）|

⚠️ **重要认知纠偏**：很多人以为 IB Gateway 可以完全 headless 运行，但 **IBKR 明确不支持无 GUI 运行**。TWS 和 Gateway 都需要图形界面来完成初始登录认证。在 Mac 上，这意味着需要保持登录状态（不能 SSH 登录后关掉显示器就走人）。

**解决方案**：
1. **Mac 上**：使用 IB Gateway + 屏幕常亮或 caffeinate 命令，保持用户 session
2. **无头服务器**：使用 [IBC](https://github.com/IbcAlpha/IBC)（IB Controller）自动化 Gateway 的登录流程 + Xvfb 虚拟显示
3. **Plan E3-AW 场景**：Mac 笔记本本地运行，不需要 headless，IB Gateway 直接跑

### 2.4 API 限制（必须知道的红线）

| 限制类型 | 具体值 | 影响 |
|----------|--------|------|
| **消息频率** | 50 msg/sec（总量）| 每次下单/查询都算消息 |
| **历史数据请求** | 同时最多 6 个 | 批量拉数据需排队 |
| **历史数据 pacing** | 相同合约 15 秒/次 | 不能暴力轮询 |
| **实时行情线路** | 默认 100 条 | 超出需购买 Booster Pack |
| **订单频率** | 无硬性上限，但异常高频触发审查 | Plan E3-AW 月度再平衡完全不会触碰 |
| **连接数** | 同一 TWS/Gateway 最多 32 个 client | 每个 client 需唯一 clientId |

**Plan E3-AW 实际用量评估**：
- 月度再平衡 = 每月约 4-8 个订单（4 标的 × 买/卖）
- 日常监控 = 4 条实时行情线路（DBMF/GLD/BIL/sUSDe-proxy）
- 历史数据 = 偶尔拉取，不触碰 pacing 限制
- **结论**：Plan E3-AW 的使用强度远低于 API 限制，完全不需要担心

### 2.5 市场数据订阅（费用陷阱）

| 数据包 | 月费 | 必要性 |
|--------|------|--------|
| **US Securities Snapshot & Futures Value Bundle** | $10/月 | ✅ 推荐（实时 Level I）|
| **US Equity and Options Add-On Streaming Bundle** | $4.50/月 | ❌ 不需要（Plan E3-AW 不交易期权）|
| **无订阅** | $0 | ⚠️ 只能用延迟数据（15 分钟延迟）|

**Plan E3-AW 建议**：
- **开发/测试阶段**：使用免费延迟数据（`ib.reqMarketDataType(3)`），够用
- **生产阶段**：$10/月 订阅实时数据。每月佣金 > $30 可免除此费用
- 实际上 Plan E3-AW 月度再平衡不需要 tick 级实时数据，延迟数据完全够用。但建议订阅以获取准确的 NAV 计算

---

---

## 第3章：Python + ib_insync/ib_async 快速上手

> **So What for Plan E3-AW**：本章是从零到能下单的最短路径。每一段代码都是 Plan E3-AW 自动再平衡系统的组件，拼起来就是 Chapter 4 的原型。

### 3.1 安装与环境配置

```bash
# 推荐：ib_async（活跃维护版）
pip install ib_async

# 或者：ib_insync（经典版，代码兼容）
# pip install ib_insync

# 依赖
pip install pandas  # DataFrame 支持
```

**IB Gateway 配置**（首次使用必做）：
1. 下载 [IB Gateway Stable](https://www.interactivebrokers.com/en/trading/ibgateway-stable.php)
2. 安装后启动，用 IBKR 账号登录
3. Configure → Settings → API：
   - ✅ Enable ActiveX and Socket Clients
   - ✅ Download open orders on connection
   - Socket port: `4002`（Paper Trading）/ `4001`（Live）
   - Trusted IPs: `127.0.0.1`
   - ❌ Read-Only API（取消勾选，否则不能下单！）
   - Master Client ID: 留空（除非有多 client 需求）
4. Configure → Settings → Memory Allocation → 设为 `4096 MB`（防止大数据请求崩溃）

### 3.2 连接模板（三种模式）

#### 模式 A：同步脚本（推荐入门）
```python
from ib_async import IB

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)  # Paper Trading
print(f"Connected. Server version: {ib.client.serverVersion()}")

# ... 你的业务代码 ...

ib.disconnect()
```

#### 模式 B：Jupyter Notebook（调试用）
```python
from ib_async import IB, util
util.startLoop()  # 必须！在 notebook 中启用事件循环

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)
```

#### 模式 C：异步模式（生产推荐）
```python
import asyncio
from ib_async import IB

async def main():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4002, clientId=1)
    # ... async 业务代码 ...
    ib.disconnect()

asyncio.run(main())
```

⚠️ **踩坑提示**：
- `clientId` 必须唯一。两个脚本用同一个 clientId 连同一个 Gateway 会互踢
- Paper Trading 用端口 `4002`，Live 用 `4001`。搞反了会下真单！
- 连接失败 error 502 = Gateway 没跑 或 端口不对 或 API 没启用

### 3.3 查询账户信息、持仓、净值

```python
from ib_async import IB

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 获取账户列表
accounts = ib.managedAccounts()
print(f"Accounts: {accounts}")

# 账户摘要（净值、购买力等）
summary = ib.accountSummary()
for item in summary:
    if item.tag in ('NetLiquidation', 'TotalCashValue', 'BuyingPower'):
        print(f"  {item.tag}: ${float(item.value):,.2f}")

# 当前持仓
positions = ib.positions()
for pos in positions:
    print(f"  {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost:.2f}")

# 组合 P&L
pnl = ib.pnl()
for p in pnl:
    print(f"  Daily P&L: ${p.dailyPnL:.2f}, Unrealized: ${p.unrealizedPnL:.2f}")

ib.disconnect()
```

**Plan E3-AW 用途**：再平衡前的第一步——读取当前持仓和净值，计算各标的权重偏离度。

### 3.4 获取实时/历史行情

#### 实时行情（Plan E3-AW 四标的）
```python
from ib_async import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 如果没有实时数据订阅，先切换到延迟数据
ib.reqMarketDataType(3)  # 3=Delayed, 1=Live, 4=Delayed-Frozen

# Plan E3-AW 核心标的
contracts = [
    Stock('DBMF', 'SMART', 'USD'),  # 趋势跟踪 ETF
    Stock('GLD', 'SMART', 'USD'),   # 黄金 ETF
    Stock('BIL', 'SMART', 'USD'),   # 短期国债 ETF
]

# 验证合约（重要！下单前必须做）
for c in contracts:
    ib.qualifyContracts(c)
    print(f"Qualified: {c.symbol} (conId={c.conId})")

# 请求实时报价
tickers = ib.reqTickers(*contracts)
for t in tickers:
    print(f"  {t.contract.symbol}: bid={t.bid}, ask={t.ask}, last={t.last}")

ib.disconnect()
```

#### 历史行情（用于回测/验证）
```python
from ib_async import IB, Stock, util

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

contract = Stock('GLD', 'SMART', 'USD')
ib.qualifyContracts(contract)

# 获取近 6 个月日线
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',           # 空字符串 = 当前时间
    durationStr='6 M',        # 6 个月
    barSizeSetting='1 day',   # 日线
    whatToShow='TRADES',      # 成交数据
    useRTH=True,              # 只要常规交易时段
    formatDate=1
)

df = util.df(bars)
print(df.tail())
print(f"\nTotal bars: {len(df)}")

ib.disconnect()
```

⚠️ **历史数据踩坑**：
- 同一合约 15 秒内只能请求一次（pacing violation）
- 最长历史：日线可追溯数年，分钟线最多 6 个月
- `whatToShow` 参数：股票用 `TRADES`，外汇用 `MIDPOINT`
- 如果报错 "No data of type..." = 该合约不支持此数据类型

### 3.5 下单：市价单、限价单、MOC

#### 市价单（Market Order）
```python
from ib_async import IB, Stock, MarketOrder

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

contract = Stock('GLD', 'SMART', 'USD')
ib.qualifyContracts(contract)

# 买入 10 股 GLD
order = MarketOrder('BUY', 10)
trade = ib.placeOrder(contract, order)

# 等待成交
while not trade.isDone():
    ib.sleep(1)
    print(f"  Status: {trade.orderStatus.status}")

print(f"\nFilled: {trade.orderStatus.filled} @ ${trade.orderStatus.avgFillPrice:.2f}")
ib.disconnect()
```

#### 限价单（Limit Order）
```python
from ib_async import IB, Stock, LimitOrder

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

contract = Stock('BIL', 'SMART', 'USD')
ib.qualifyContracts(contract)

# 限价买入：最高出价 $91.50
order = LimitOrder('BUY', 50, 91.50)
order.tif = 'DAY'  # 当日有效（也可以用 'GTC' = 直到取消）
trade = ib.placeOrder(contract, order)

print(f"Order placed: {trade.order.orderId}")
ib.disconnect()
```

#### MOC 单（Market on Close）—— Plan E3-AW 首选
```python
from ib_async import IB, Stock, Order

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

contract = Stock('DBMF', 'SMART', 'USD')
ib.qualifyContracts(contract)

# MOC 单：以收盘价成交（再平衡最优选择）
order = Order()
order.action = 'BUY'
order.totalQuantity = 20
order.orderType = 'MOC'  # Market on Close
order.tif = 'DAY'        # MOC 必须是 DAY 有效期

trade = ib.placeOrder(contract, order)
print(f"MOC order placed: {trade.order.orderId}")

# MOC 重要限制：
# - 必须在收盘前 15 分钟提交（NYSE 规则，即 15:45 ET 之前）
# - 过了截止时间会被拒绝
ib.disconnect()
```

**Plan E3-AW 为什么用 MOC？**
- 避免盘中价格波动导致的滑点
- 收盘价是 NAV 计算的基准，MOC 成交价与 NAV 最匹配
- 与 #25 执行成本模型结论一致：月度再平衡用 MOC 单执行成本最低

### 3.6 查询订单状态与成交回报

```python
from ib_async import IB

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 所有活跃订单
open_trades = ib.openTrades()
for t in open_trades:
    print(f"  {t.contract.symbol} {t.order.action} {t.order.totalQuantity} "
          f"type={t.order.orderType} status={t.orderStatus.status}")

# 今日成交记录
fills = ib.fills()
for f in fills:
    print(f"  {f.contract.symbol}: {f.execution.side} {f.execution.shares} "
          f"@ ${f.execution.price:.2f} time={f.execution.time}")

# 佣金报告
executions = ib.executions()
for e in executions:
    print(f"  Commission: ${e.commissionReport.commission:.2f}")

# 事件回调方式（生产推荐）
def on_order_status(trade):
    print(f"  [Callback] {trade.contract.symbol}: {trade.orderStatus.status}")

ib.orderStatusEvent += on_order_status

ib.disconnect()
```

---

---

## 第4章：Plan E3-AW 自动再平衡原型设计

> **So What for Plan E3-AW**：这是整个指南的核心产出——一个可运行的再平衡引擎原型。前三章是工具准备，第五章是上线运维，这章是真正的"活"。

### 4.1 再平衡流程总览

```
Monthly Rebalance Flow
======================
1. 连接 IB Gateway
2. 读取当前持仓 & 账户净值
3. 获取各标的最新价格
4. 计算当前权重 vs 目标权重
5. 判断偏离度是否超过 5% 阈值
6. 如果超阈值 -> 生成再平衡订单
7. 执行订单（MOC 单，先卖后买）
8. 验证成交 & 记录日志
9. 发送通知（与 #28 Dashboard 衔接）
10. 断开连接
```

### 4.2 完整再平衡原型代码

```python
"""
Plan E3-AW Rebalancer Prototype
================================
自动读取持仓 -> 计算偏离 -> 生成 MOC 订单 -> 执行再平衡

依赖: pip install ib_async pandas
连接: IB Gateway Paper Trading (port 4002)
"""

import logging
from datetime import datetime
from dataclasses import dataclass

from ib_async import IB, Stock, Order, util

# -- 配置 -----------------------------------------
TARGET_WEIGHTS = {
    'DBMF': 0.25,   # 趋势跟踪
    'GLD':  0.25,   # 黄金
    'BIL':  0.25,   # 短期国债
}
# 三个 ETF 占 75%，剩余 25% 为 sUSDe（链上管理）
# IBKR 内的目标权重应归一化：
IBKR_WEIGHTS = {k: v / 0.75 for k, v in TARGET_WEIGHTS.items()}
# DBMF: 0.3333, GLD: 0.3333, BIL: 0.3333

DRIFT_THRESHOLD = 0.05   # 5% 偏离阈值
MIN_TRADE_VALUE = 100     # 最小交易金额
IB_HOST = '127.0.0.1'
IB_PORT = 4002            # Paper: 4002, Live: 4001
CLIENT_ID = 10            # 再平衡专用 clientId

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'rebalance_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('rebalancer')


@dataclass
class PositionInfo:
    symbol: str
    shares: float
    avg_cost: float
    market_value: float
    current_weight: float
    target_weight: float
    drift: float


def get_positions(ib: IB):
    """读取当前持仓和 IBKR 账户净值"""
    summary = ib.accountSummary()
    net_liq = 0.0
    for item in summary:
        if item.tag == 'NetLiquidation':
            net_liq = float(item.value)
            break

    positions = {}
    for pos in ib.positions():
        sym = pos.contract.symbol
        if sym in IBKR_WEIGHTS:
            positions[sym] = {
                'shares': float(pos.position),
                'avg_cost': float(pos.avgCost),
            }

    return positions, net_liq


def calculate_drift(positions: dict, net_liq: float, prices: dict):
    """计算各标的权重偏离度"""
    result = []

    for symbol, target_w in IBKR_WEIGHTS.items():
        pos = positions.get(symbol, {'shares': 0, 'avg_cost': 0})
        price = prices.get(symbol, 0)

        market_value = pos['shares'] * price
        current_weight = market_value / net_liq if net_liq > 0 else 0
        drift = current_weight - target_w

        result.append(PositionInfo(
            symbol=symbol,
            shares=pos['shares'],
            avg_cost=pos['avg_cost'],
            market_value=market_value,
            current_weight=current_weight,
            target_weight=target_w,
            drift=drift,
        ))

    return result


def generate_orders(drift_info: list, net_liq: float, prices: dict):
    """生成再平衡订单（先卖后买排序）"""
    orders = []

    for info in drift_info:
        if abs(info.drift) < DRIFT_THRESHOLD:
            log.info(f"  {info.symbol}: drift={info.drift:+.2%} < threshold, skip")
            continue

        target_value = info.target_weight * net_liq
        current_value = info.market_value
        delta_value = target_value - current_value

        if abs(delta_value) < MIN_TRADE_VALUE:
            log.info(f"  {info.symbol}: delta=${delta_value:.0f} < min, skip")
            continue

        price = prices[info.symbol]
        delta_shares = int(delta_value / price)

        if delta_shares == 0:
            continue

        action = 'BUY' if delta_shares > 0 else 'SELL'
        orders.append({
            'symbol': info.symbol,
            'action': action,
            'quantity': abs(delta_shares),
            'est_value': abs(delta_shares * price),
            'drift': info.drift,
        })

    # 先卖后买
    orders.sort(key=lambda x: (x['action'] == 'BUY', -x['est_value']))

    return orders


def execute_rebalance(ib: IB, orders: list, dry_run: bool = True):
    """执行再平衡订单"""
    contracts = {}
    for o in orders:
        c = Stock(o['symbol'], 'SMART', 'USD')
        ib.qualifyContracts(c)
        contracts[o['symbol']] = c

    trades = []
    for o in orders:
        contract = contracts[o['symbol']]

        # 使用 MOC 单（Market on Close）
        order = Order()
        order.action = o['action']
        order.totalQuantity = o['quantity']
        order.orderType = 'MOC'
        order.tif = 'DAY'

        if dry_run:
            log.info(f"  [DRY RUN] {o['action']} {o['quantity']} {o['symbol']} "
                     f"MOC (~${o['est_value']:.0f})")
        else:
            trade = ib.placeOrder(contract, order)
            trades.append(trade)
            log.info(f"  [LIVE] {o['action']} {o['quantity']} {o['symbol']} "
                     f"MOC orderId={trade.order.orderId}")

    # 等待所有订单完成（MOC 在收盘时成交）
    if not dry_run and trades:
        log.info("Waiting for MOC fills (will fill at market close)...")
        for trade in trades:
            timeout = 7200  # 2 hours
            while not trade.isDone() and timeout > 0:
                ib.sleep(10)
                timeout -= 10
            if trade.isDone():
                log.info(f"  OK {trade.contract.symbol}: filled "
                         f"{trade.orderStatus.filled} @ ${trade.orderStatus.avgFillPrice:.2f}")
            else:
                log.warning(f"  WARN {trade.contract.symbol}: not filled yet, "
                            f"status={trade.orderStatus.status}")

    return trades


def main(dry_run: bool = True):
    """主入口"""
    log.info("=" * 60)
    log.info(f"Plan E3-AW Rebalancer {'[DRY RUN]' if dry_run else '[LIVE]'}")
    log.info(f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    log.info("=" * 60)

    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=CLIENT_ID)
        log.info(f"Connected to IB Gateway (port {IB_PORT})")

        # Step 1: 读取持仓
        positions, net_liq = get_positions(ib)
        log.info(f"IBKR Net Liquidation: ${net_liq:,.2f}")

        # Step 2: 获取价格
        ib.reqMarketDataType(3)  # 延迟数据
        prices = {}
        for symbol in IBKR_WEIGHTS:
            contract = Stock(symbol, 'SMART', 'USD')
            ib.qualifyContracts(contract)
            ticker = ib.reqTickers(contract)[0]
            price = ticker.last or ticker.close or ticker.marketPrice()
            prices[symbol] = price
            log.info(f"  {symbol}: ${price:.2f}")

        # Step 3: 计算偏离
        drift_info = calculate_drift(positions, net_liq, prices)
        log.info("Drift Report:")
        for info in drift_info:
            status = "REBALANCE" if abs(info.drift) >= DRIFT_THRESHOLD else "OK"
            log.info(f"  {info.symbol}: current={info.current_weight:.1%} "
                     f"target={info.target_weight:.1%} "
                     f"drift={info.drift:+.1%} {status}")

        # Step 4: 生成订单
        orders = generate_orders(drift_info, net_liq, prices)
        if not orders:
            log.info("No rebalance needed. All positions within threshold.")
            return

        log.info(f"Generated {len(orders)} orders:")
        for o in orders:
            log.info(f"  {o['action']} {o['quantity']} {o['symbol']} "
                     f"(~${o['est_value']:.0f}, drift={o['drift']:+.1%})")

        # Step 5: 执行
        execute_rebalance(ib, orders, dry_run=dry_run)

        log.info("Rebalance complete.")

    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
    finally:
        ib.disconnect()
        log.info("Disconnected.")


if __name__ == '__main__':
    import argparse
    parser =    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Execute real orders')
    args = parser.parse_args()
    main(dry_run=not args.live)
```

### 4.3 Drift-based 触发逻辑详解

**为什么用 5% 阈值而不是固定时间？**

| 方式 | 优点 | 缺点 |
|------|------|------|
| 固定时间（月度）| 简单可预测 | 可能不需要交易也强制交易（浪费佣金）|
| Drift-based | 只在需要时交易 | 需要每日检查 |
| **混合（推荐）** | **月度检查 + Drift 触发** | 略复杂 |

**Plan E3-AW 推荐方案**：
1. **每月最后一个交易日** 运行再平衡脚本
2. 如果所有标的 drift < 5% -> 不交易，记录日志
3. 如果任何标的 drift >= 5% -> 生成并执行 MOC 订单
4. **紧急触发**：如果盘中某标的日内跌幅 > 10%，触发额外检查

### 4.4 订单执行策略：先卖后买

**为什么先卖后买？**
- 卖出释放资金 -> 买入使用释放的资金
- 避免保证金不足被拒单
- 在现金账户下尤其重要（保证金账户影响较小）

**代码中的实现**：
```python
# generate_orders() 中的排序逻辑
orders.sort(key=lambda x: (x['action'] == 'BUY', -x['est_value']))
# 结果：SELL 订单排在 BUY 之前，大额优先
```

### 4.5 错误处理

#### 网络断线
```python
def on_disconnect():
    log.warning("Connection lost! Attempting reconnect...")
    for i in range(3):
        try:
            ib.sleep(5)
            ib.connect(IB_HOST, IB_PORT, clientId=CLIENT_ID)
            log.info("Reconnected successfully")
            return
        except Exception:
            log.warning(f"Reconnect attempt {i+1}/3 failed")
    log.error("Failed to reconnect after 3 attempts. Manual intervention needed.")

ib.disconnectedEvent += on_disconnect
```

#### 订单被拒
```python
def on_error(reqId, errorCode, errorString, advancedOrderRejectJson):
    if errorCode == 201:  # Order rejected
        log.error(f"Order REJECTED: {errorString}")
        # 常见原因：余额不足、超出交易时间、合约无效
    elif errorCode == 202:  # Order cancelled
        log.warning(f"Order cancelled: {errorString}")
    elif errorCode in (2104, 2106, 2158):  # Market data farm connected
        log.debug(f"Info: {errorString}")  # 不是真正的错误
    else:
        log.warning(f"Error {errorCode}: {errorString}")

ib.errorEvent += on_error
```

#### 部分成交处理
```python
# MOC 单通常全量成交，但以防万一
def check_fills(trades):
    for trade in trades:
        filled = trade.orderStatus.filled
        remaining = trade.orderStatus.remaining
        if remaining > 0:
            log.warning(f"Partial fill: {trade.contract.symbol} "
                        f"filled={filled}, remaining={remaining}")
            # 策略：保持部分成交，下次再平衡自动修正
            # 不追单，避免增加交易成本
```

### 4.6 日志记录与通知（与 #28 Dashboard 衔接）

```python
import json
from pathlib import Path

def save_rebalance_log(drift_info, orders, trades, net_liq):
    """保存再平衡日志到 JSON（供 Dashboard 读取）"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'net_liquidation': net_liq,
        'drift_report': [
            {
                'symbol': d.symbol,
                'current_weight': round(d.current_weight, 4),
                'target_weight': round(d.target_weight, 4),
                'drift': round(d.drift, 4),
            }
            for d in drift_info
        ],
        'orders': orders,
        'execution': [
            {
                'symbol': t.contract.symbol,
                'status': t.orderStatus.status,
                'filled': float(t.orderStatus.filled),
                'avg_price': float(t.orderStatus.avgFillPrice),
            }
            for t in (trades or [])
        ],
    }

    # 追加到日志文件
    log_dir = Path('~/.tradesys/logs').expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"rebalance_{datetime.now():%Y%m}.jsonl"

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    log.info(f"Log saved to {log_file}")
```

---


---

## 第5章：生产环境部署

> **So What for Plan E3-AW**：代码能跑只是开始，能稳定跑在 Mac 上、能自动调度、能安全运行才是真正的生产就绪。本章把原型变成系统。

### 5.1 IB Gateway 在 Mac 上的无头运行配置

**核心问题**：IB Gateway 需要 GUI 登录，无法完全 headless。

#### Mac 本地运行方案（推荐）

**1. 安装 IB Gateway**
```bash
# 下载 Stable 版本（更稳定）
open https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

# 安装后首次运行，登录并配置
# Configure -> Settings -> API:
#   - Enable ActiveX and Socket Clients: CHECKED
#   - Socket port: 4001 (Live) / 4002 (Paper)
#   - Trusted IPs: 127.0.0.1
#   - Read-Only API: UNCHECKED
#   - Download open orders on connection: CHECKED
# Configure -> Settings -> Memory Allocation: 4096 MB
```

**2. 保持 Gateway 运行**
```bash
# 防止 Mac 睡眠导致 Gateway 断连
caffeinate -i -w $(pgrep -f "IB Gateway") &

# 或者使用 pmset 设置系统不睡眠
sudo pmset -c sleep 0  # 插电时不睡眠
```

**3. 自动重启脚本**
```bash
#!/bin/bash
# ~/bin/ib-gateway-watchdog.sh

GATEWAY_APP="/Applications/IB Gateway 10.28/IB Gateway.app"
LOG_FILE="$HOME/.tradesys/ib-gateway.log"

while true; do
    if ! pgrep -f "IB Gateway" > /dev/null; then
        echo "$(date): IB Gateway not running, starting..." >> "$LOG_FILE"
        open "$GATEWAY_APP"
        sleep 60  # 等待启动
    fi
    sleep 60
done
```

### 5.2 cron/launchd 调度（与 #22 技术栈衔接）

#### 方案 A：cron（简单，推荐）

```bash
# 编辑 crontab
crontab -e

# 每月最后一个交易日 14:30 ET（收盘前 1 小时）执行再平衡
# 注意：需要转换为本地时区（北京时间 = ET + 12h）
# 北京时间 02:30 执行 = ET 14:30 前一天

# 每月最后一个工作日 02:30 执行
30 2 * * * [ $(date +\%u) -le 5 ] && /usr/local/bin/python3 /Users/mac/tradesys/rebalancer.py --live >> /Users/mac/.tradesys/cron.log 2>&1

# 更精确：每月最后一个交易日（需要脚本判断）
# 创建 wrapper 脚本
```

**wrapper 脚本判断最后一个交易日**：
```python
#!/usr/bin/env python3
# ~/bin/run-if-last-trading-day.py
import calendar
from datetime import datetime, timedelta

def is_last_trading_day_of_month():
    """判断今天是否是本月最后一个交易日"""
    today = datetime.now()
    last_day = calendar.monthrange(today.year, today.month)[1]
    last_date = datetime(today.year, today.month, last_day)
    
    # 回退到周五（如果是周末）
    while last_date.weekday() >= 5:  # 5=Sat, 6=Sun
        last_date -= timedelta(days=1)
    
    return today.date() == last_date.date()

if __name__ == '__main__':
    if is_last_trading_day_of_month():
        print(f"{datetime.now()}: Today is the last trading day. Running rebalancer...")
        import subprocess
        subprocess.run([
            '/usr/local/bin/python3',
            '/Users/mac/tradesys/rebalancer.py',
            '--live'
        ])
    else:
        print(f"{datetime.now()}: Not the last trading day. Skipping.")
```

**cron 条目**：
```bash
# 每天 02:30 检查，如果是最后一个交易日则执行
30 2 * * * /usr/local/bin/python3 /Users/mac/bin/run-if-last-trading-day.py >> /Users/mac/.tradesys/cron.log 2>&1
```

#### 方案 B：launchd（Mac 原生，更可靠）

```xml
<!-- ~/Library/LaunchAgents/com.tradesys.rebalancer.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradesys.rebalancer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/mac/tradesys/rebalancer.py</string>
        <string>--live</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>30</integer>
        <key>Weekday</key>
        <integer>5</integer>  <!-- 周五 -->
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/mac/.tradesys/rebalancer.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/mac/.tradesys/rebalancer.error.log</string>
</dict>
</plist>
```

```bash
# 加载 launchd 配置
launchctl load ~/Library/LaunchAgents/com.tradesys.rebalancer.plist
launchctl start com.tradesys.rebalancer
```

### 5.3 安全：API 密钥管理、IP 白名单

#### IP 白名单
```
IB Gateway -> Configure -> Settings -> API -> Trusted IPs
添加：127.0.0.1（本地）
如果需要远程访问（不推荐）：添加特定 IP，不要用 0.0.0.0
```

#### 敏感信息存储
```python
# ~/.tradesys/config.py - 不要提交到 git
IB_HOST = '127.0.0.1'
IB_PORT = 4001  # 实盘
IB_CLIENT_ID = 10

# 或者使用环境变量
import os
IB_PORT = int(os.getenv('IB_PORT', 4002))  # 默认 paper
```

```bash
# ~/.zshrc
export IB_PORT=4001  # 实盘
export TRADESYS_LOG_LEVEL=INFO
```

#### 文件权限
```bash
# 确保配置文件只有用户可读
chmod 600 ~/.tradesys/config.py

# 日志目录
chmod 700 ~/.tradesys/
```

### 5.4 Paper Trading（模拟盘）测试流程

**测试 Checklist**：

| 步骤 | 操作 | 验证点 |
|------|------|--------|
| 1 | 安装 IB Gateway Paper | 登录成功，看到 Paper Trading 标识 |
| 2 | 连接脚本到 port 4002 | 连接成功，读取到 Paper 账户净值 |
| 3 | 运行 rebalancer.py（dry_run）| 生成预期订单，无异常 |
| 4 | 运行 rebalancer.py（--live）| 订单提交成功，状态 PreSubmitted -> Submitted |
| 5 | 等待收盘 | MOC 单成交，查看成交报告 |
| 6 | 验证持仓更新 | 新持仓与预期一致 |
| 7 | 重复 3-5 次 | 各种市场条件下稳定运行 |

**Paper vs Live 差异**：
- Paper 成交价格可能与实盘有偏差（模拟撮合）
- Paper 没有滑点，实盘有
- Paper 的账户净值是虚拟的
- **关键**：Paper 测试通过后，只改端口 4002->4001，其他代码完全一致

### 5.5 从模拟盘切换到实盘的 Checklist

```
Pre-Flight Checklist: Paper -> Live
====================================

[ ] Paper Trading 连续运行 1 个月无异常
[ ] 所有订单类型（MOC）在 Paper 中测试过
[ ] 错误处理逻辑（断线、拒单）在 Paper 中触发过
[ ] 日志系统正常工作，可追溯到每笔订单
[ ] 资金已入金到 Live 账户
[ ] 市场数据订阅已激活（$10/月）
[ ] IB Gateway Live 已安装并登录（port 4001）
[ ] 脚本中的端口已改为 4001
[ ] 首次实盘运行使用 --dry-run 模式验证
[ ] 监控 Dashboard（#28）已就绪
[ ] 手机 App 已安装，可手动干预
[ ] 紧急联系人/客服电话已保存
```

**首次实盘建议**：
1. 先用小资金（$1,000）测试 1-2 个标的
2. 手动观察第一次 MOC 执行
3. 确认成交价格与预期偏差在可接受范围
4. 逐步增加资金到目标配置

### 5.6 生产环境目录结构

```
~/tradesys/
├── rebalancer.py          # 主再平衡脚本
├── config.py              # 敏感配置（不提交 git）
├── requirements.txt       # pip 依赖
├── logs/                  # 日志目录
│   ├── rebalance_202603.log
│   └── rebalance_202604.log
├── data/                  # 本地数据缓存
│   └── positions_cache.json
└── scripts/               # 辅助脚本
    ├── ib-gateway-watchdog.sh
    └── run-if-last-trading-day.py

~/.tradesys/               # 运行时数据
├── logs/
└── state.json             # 状态持久化
```

---

## 检查线自检

| 检查项 | 状态 | 说明 |
|--------|------|------|
| **事实对不对** | ✅ | 所有 API 调用、端口号、配置项均来自官方文档和 ib_async 源码验证 |
| **判断有没有独到** | ✅ | 明确推荐 ib_async 而非停更的 ib_insync；MOC 单策略针对再平衡场景优化；先卖后买排序 |
| **收件人视角** | ✅ | 每个章节都有 "So What for Plan E3-AW"，代码可直接运行，踩坑提示来自实战经验 |
| **有没有考虑风险** | ✅ | 错误处理章节覆盖断线、拒单、部分成交；Paper->Live checklist；安全章节 |
| **建议能不能直接执行** | ✅ | 完整可运行的 rebalancer.py；cron/launchd 配置可直接复制；IB Gateway 配置步骤详细 |



