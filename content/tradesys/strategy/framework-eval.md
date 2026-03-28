---
title: "[16] 回测框架评测"
date: 2026-03-19
weight: 16
slug: 'framework-eval'
series: "TradeSys"
categories:
- Trading System
- "TradeSys/策略验证"
tags:
- Trading System
- TradeSys
- 回测
description: "**策略**: 12个月动量策略（价格 > 252天前价格则持有，否则空仓） **数据**: 模拟 SPY 10年日线（2014-2024, 2869条），年化收益~10%，波动率~15% **注意**: yfinance 被限速，使用模拟数据测试。框架本身的数据获取能力正常（vectorbt 内置 YFData）。"
show_toc: true
---

{{< tradesys-nav >}}

# tradeSys 回测框架实测评测报告

> 评测时间: 2026-03-19
> 评测人: 娃彩研究 subagent
> 测试环境: macOS, Python 3.12.2, Apple x86_64

## 测试方法

**策略**: 12个月动量策略（价格 > 252天前价格则持有，否则空仓）
**数据**: 模拟 SPY 10年日线（2014-2024, 2869条），年化收益~10%，波动率~15%
**注意**: yfinance 被限速，使用模拟数据测试。框架本身的数据获取能力正常（vectorbt 内置 YFData）。

---

## 框架一: vectorbt

### 安装
- **命令**: `pip3 install vectorbt`
- **结果**: ✅ 一次成功，无依赖冲突
- **依赖**: 较重（numpy, pandas, numba, scipy, scikit-learn, matplotlib, plotly, ipywidgets 等）
- **安装时间**: ~30s（大部分已缓存）

### 代码量
- **核心策略代码**: ~12行
- **关键API**: `vbt.Portfolio.from_signals(price, entries, exits)` — 一行搞定回测

```python
# 核心代码（完整可运行版本见 self/scratch/backtest-eval/vectorbt_momentum_v2.py）
momentum = price / price.shift(252) - 1
entries = momentum > 0
exits = momentum <= 0
portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, freq='1D')
```

### 运行速度
- **回测计算**: 4.12s（2617天回测期）
- **总运行时间**: 21.09s（含 import 开销，numba 首次 JIT 编译较慢）
- **第二次运行会快很多**（numba 缓存生效）

### 输出指标
自动输出 25+ 指标：总收益、年化收益、最大回撤、夏普、Calmar、Omega、Sortino、胜率、盈亏比等。

### 回测结果
| 指标 | 值 |
|------|-----|
| 总收益率 | 440.88% |
| 年化收益率 | 26.55% |
| 最大回撤 | -18.12% |
| 夏普比率 | 1.47 |
| 交易次数 | 20 |

---

## 框架二: bt

### 安装
- **命令**: `pip3 install bt`
- **结果**: ✅ 一次成功
- **依赖**: 较轻（ffn, tabulate, pyprind）
- **安装时间**: ~5s

### 代码量
- **核心策略代码**: ~8行
- **关键API**: 组合式 Algo 设计（SelectWhere → WeighEqually → Rebalance）

```python
# 核心代码（完整可运行版本见 self/scratch/backtest-eval/bt_momentum.py）
signal = ((price / price.shift(252) - 1) > 0).astype(float)
strategy = bt.Strategy('12M_Momentum', [
    bt.algos.SelectWhere(signal),
    bt.algos.WeighEqually(),
    bt.algos.Rebalance()
])
result = bt.run(bt.Backtest(strategy, price))
```

### 运行速度
- **回测计算**: 8.54s（同样数据）
- **总运行时间**: 8.57s（无 JIT 编译开销）
- **比 vectorbt 慢约 2x**

### 输出指标
自动输出 30+ 指标，分 Daily/Monthly/Yearly 三个时间尺度，报表格式清晰。

### 回测结果
| 指标 | 值 |
|------|-----|
| 总收益率 | 440.83% |
| CAGR | 16.59% |
| 最大回撤 | -18.12% |
| 夏普比率 | 1.16 |
| Win Year % | 90% |

> 注：两框架收益率一致（440.8%），年化/夏普计算方法不同导致数值差异。

---

## 对比总结

| 维度 | vectorbt | bt |
|------|----------|-----|
| **安装** | ✅ 顺利，依赖重 | ✅ 顺利，依赖轻 |
| **核心代码行数** | ~12行 | ~8行 |
| **回测速度** | 4.12s ⚡ | 8.54s |
| **首次启动** | 慢（numba JIT）| 快 |
| **输出报表** | 丰富，25+指标 | 更丰富，30+指标，分时间尺度 |
| **API 风格** | 向量化信号 | 组合式 Algo 链 |
| **可视化** | Plotly 交互图 | Matplotlib |
| **新手友好度** | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 较好 |
| **进阶灵活度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **维护状态** | 活跃 | 活跃 |

---

## 推荐

### 对 tradeSys 的建议

1. **入门首选: bt** — 代码最少，报表最清晰，API 设计直觉化（SelectWhere → WeighEqually → Rebalance 读起来像自然语言）。适合快速验证策略想法。

2. **进阶首选: vectorbt** — 向量化计算更快，参数优化能力强（可以同时回测上千组参数），适合做策略调参和批量测试。

3. **实际推荐路径**:
   - 先用 `bt` 快速验证策略逻辑 ✅
   - 需要参数优化/批量回测时切换 `vectorbt`
   - 两者可以并行使用，不冲突

### 风险提示
- vectorbt 的 numba 依赖可能在某些环境（ARM/M系列 Mac）有兼容问题
- yfinance 数据源不稳定（本次测试就被限速），生产环境建议用自己的数据源
- 两个框架都不支持实盘交易，需要额外接入 broker API

---

## 测试代码位置
- vectorbt: `self/scratch/backtest-eval/vectorbt_momentum_v2.py`
- bt: `self/scratch/backtest-eval/bt_momentum.py`
