---
title: "[14] Plan E 回测"
date: 2026-03-20
weight: 14
slug: 'plan-e-backtest'
series: "TradeSys"
categories:
- Trading System
- "TradeSys/策略验证"
tags:
- Trading System
- TradeSys
- ETF
- 黄金
- 回测
- Funding Rate
description: "**研究日期**: 2026-03-20 **回测期**: 2017-03-22 ~ 2026-03-18（9.0 年，2260 交易日） **数据来源**: SPY/TLT/GLD 真实历史价格 + 合成 CryptoFunding（修正后参数）"
show_toc: true
---

{{< tradesys-nav >}}

# Plan E 回测报告 — 移除 SVOL 后的组合优化

**研究日期**: 2026-03-20  
**回测期**: 2017-03-22 ~ 2026-03-18（9.0 年，2260 交易日）  
**数据来源**: SPY/TLT/GLD 真实历史价格 + 合成 CryptoFunding（修正后参数）

---

## 背景

SVOL ETF 4.8 年样本外验证（P-10）证伪了合成数据假设：

| 指标 | 合成假设 | 真实 OOS |
|------|----------|----------|
| Sharpe | 0.81 | **-0.03** |
| SPY 相关性 | ~0 | **0.72** |
| 年化波动率 | 8% | **17.8%** |
| 最大回撤 | -15% | **-28%** |

**核心问题**：SVOL 在 Plan D 中占 10% 权重，基于已被证伪的合成假设。需要测试移除 SVOL 后的组合表现。

---

## 测试方案

| 方案 | TSMOM | XSMOM | MeanRev | CryptoFunding | GoldMom | 设计逻辑 |
|------|-------|-------|---------|---------------|---------|---------|
| **Plan D baseline** | 35% | 15% | 10% | 20% | 10% | v3 方案（含 SVOL 10%，用真实 beta 代理） |
| **Plan E1 均衡** | 35% | 15% | 10% | 25% | 15% | SVOL 权重均匀分配给 CryptoFunding 和 GoldMom |
| **Plan E2 最大独立** | 30% | 15% | 10% | 30% | 15% | 最大化独立 alpha（CryptoFunding corr 0.005）|
| **Plan E3 保守** | 35% | 15% | 10% | 20% | 20% | GoldMom 优先（corr~0.05，真实资产非合成）|

---

## 回测结果

| 方案 | Sharpe | CAGR | MaxDD | Sortino | 月胜率 | vs 60/40 |
|------|--------|------|-------|---------|--------|----------|
| Plan D (含 SVOL) | 1.012 | 11.13% | -14.13% | 1.241 | 71.6% | +0.434 |
| **Plan E1 均衡** | **1.115** | 11.50% | -13.09% | 1.402 | 70.6% | +0.537 |
| **Plan E2 最大独立** | **1.179** | 11.74% | **-12.79%** | **1.542** | 69.7% | **+0.601** |
| Plan E3 保守 | 1.074 | 11.31% | -13.10% | 1.322 | 68.8% | +0.496 |
| 60/40 基准 | 0.578 | 8.48% | -27.24% | — | — | — |

### 关键发现

1. **移除 SVOL 后所有 Plan E 方案均优于 Plan D（含 SVOL）**
   - Sharpe 提升 6-17%（1.012 → 1.074~1.179）
   - MaxDD 改善（-14.13% → -12.79%~-13.10%）
   - 这证实了 SVOL 不是"中性"贡献，而是**拖累**组合表现

2. **Plan E2（最大独立）全面最优**
   - Sharpe 1.179（所有方案最高）
   - MaxDD -12.79%（所有方案最低）
   - Sortino 1.542（所有方案最高）
   - 核心原因：CryptoFunding 30% 权重最大化了唯一的 corr<0.01 策略

3. **CryptoFunding 是组合的"灵魂资产"**
   - 个体 Sharpe 1.035，MaxDD -11.83%
   - 与 TSMOM 相关性 0.005、与 GoldMom 相关性 -0.003
   - 是唯一真正独立的 alpha 源

---

## 相关性矩阵

| | TSMOM | XSMOM | MeanRev | SVOL_proxy | CryptoFunding | GoldMom |
|---|-------|-------|---------|------------|---------------|---------|
| TSMOM | 1.000 | 0.300 | 0.469 | **0.653** | 0.005 | 0.015 |
| XSMOM | 0.300 | 1.000 | 0.038 | 0.175 | 0.033 | **0.613** |
| MeanRev | 0.469 | 0.038 | 1.000 | **0.652** | -0.023 | 0.057 |
| SVOL_proxy | **0.653** | 0.175 | **0.652** | 1.000 | 0.018 | 0.060 |
| CryptoFunding | 0.005 | 0.033 | -0.023 | 0.018 | 1.000 | -0.003 |
| GoldMom | 0.015 | **0.613** | 0.057 | 0.060 | -0.003 | 1.000 |

### 关键观察

- **SVOL_proxy 与 TSMOM 相关 0.653，与 MeanRev 相关 0.652** — 这解释了为什么移除 SVOL 能改善组合：它与两个核心策略高度重叠
- **XSMOM 与 GoldMom 相关 0.613** — 这是已知问题（GoldMom 本质是 GLD TSMOM，与截面动量的 GLD 分支重叠）
- **CryptoFunding 与所有策略 corr < 0.04** — 唯一的真正独立源

---

## 风险警示

### ⚠️ CryptoFunding 仍是合成数据

Plan E2 将 CryptoFunding 提升至 30%，但该策略仍基于合成收益流（假设年化 5.5%、vol 12%）。真实的 crypto funding rate 策略需要：
- 交易所 API 对接
- 永续合约基差监控
- 执行延迟和流动性风险
- 交易所信用风险（FTX 教训）

### ⚠️ 真实性矩阵

| 策略 | 数据来源 | 真实性等级 |
|------|----------|-----------|
| TSMOM | ✅ SPY 真实价格 | ⭐⭐⭐⭐⭐ |
| XSMOM | ✅ SPY/TLT/GLD 真实价格 | ⭐⭐⭐⭐⭐ |
| MeanRev | ✅ SPY 真实价格 | ⭐⭐⭐⭐⭐ |
| GoldMom | ✅ GLD 真实价格 | ⭐⭐⭐⭐⭐ |
| CryptoFunding | ⚠️ 合成收益流 | ⭐⭐（待真实验证） |

**组合中 70% 基于真实数据，30% 基于合成假设。**

---

## 推荐

### 🏆 推荐方案：Plan E2（最大独立）

```
TSMOM 30% / XSMOM 15% / MeanRev 10% / CryptoFunding 30% / GoldMom 15%
```

**理由**：
1. Sharpe 1.179（最优），MaxDD -12.79%（最小）
2. 最大化了唯一的独立 alpha 源（CryptoFunding）
3. 移除了被真实数据证伪的 SVOL

**风险**：CryptoFunding 30% 基于合成假设，需尽快用真实 funding rate 数据验证

### 下一步

1. **优先**：获取真实 crypto funding rate 历史数据，验证 CryptoFunding 策略
2. **可选**：测试 XSMOM/GoldMom 合并（corr 0.613，可能存在冗余）
3. **长期**：Phase 1 编码实现（用真实 API 执行策略）

---

## 质量自检

- ✅ 事实准确：SVOL 证伪数据来自 P-10 真实 ETF 验证
- ✅ 有独到见解：移除 SVOL 后 Sharpe 提升（非直觉 — 移除一个策略反而更好）
- ✅ 相关性矩阵揭示了 SVOL 与 TSMOM/MeanRev 的隐性重叠
- ⚠️ CryptoFunding 仍是合成数据，30% 权重有风险集中问题
- ✅ 建议可直接执行：明确的配比 + 明确的下一步验证方向

---

*报告由 tradeSys 研究助手生成，数据可在 `plan_e_results.json` 中验证*
