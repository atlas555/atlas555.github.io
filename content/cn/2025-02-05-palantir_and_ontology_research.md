---
title: "Palantir公司和其产品Ontology的初步调研"
date: 2025-02-05
author: "张晓龙"
slug: palantir-ontology-ai-decision-system-research
draft: false
show_toc: true
keywords:
- Palantir
- Ontology
- AI决策系统
- 数据科学
- 人工智能平台
- AIP
- 企业数据分析
- 人机协作
- 商业智能
- LLM应用
- 决策模拟
- 数据建模
description: "深入解析Palantir公司及其核心产品Ontology，探讨其如何利用AI和数据科学实现智能决策支持。详细介绍了其数据模型、逻辑架构和行动框架，以及在企业决策中的创新应用，特别是其独特的人机协作模式和决策模拟能力。"
categories: ai
tags:
- Palantir
- Ontology
- 人工智能
- 数据科学
- AI决策系统
---
-- 2025.2.6 ： start，提取关键的概念

最近关注大模型 AI 的应用，发现了一个非常有意思的公司，Palantir公司。特意看了下官方的文档，做一下关键的内容总结。 -- 2025.2.6

## Palantir公司

Palantir公司是一家专注于数据科学和人工智能的公司，创始人将公司以《指环王》中的“真知晶球（Palantir）”命名，契合了公司的目标：利用人工智能和机器学习技术来整合不同类型的数据，并挖掘各种数据背后的深层价值，洞悉各个数据所代表的主体之间的联系，同时增加组织内部的协同性。

> Our software powers real-time, AI-driven decisions in critical government and commercial enterprises in the West, from the factory floors to the front lines.

Palantir提供的软件平台能够把各种数据组成以不同类型划分的数据集，然后通过高速的算法来理清数据集背后所代表的的含义，从而找出人脑需要大量时间和精力才能理清（或理不清）的深层逻辑，从而大幅提高分析者的分析能力，提升决策者的决策信心。

## Palantir 平台 、Ontology、 决策组件
Palantir AIP 在全球最关键的商业和政府环境中为实时、人工智能驱动的决策提供支持。Palantir AIP 将生成式 AI 与运营联系起来。

Palantir AI mesh 提供了全方位的 AI 驱动产品，**从 LLM 驱动的 Web 应用程序到使用视觉语言模型的移动应用程序，再到嵌入本地化 AI 的边缘应用程序**。我们将这整套功能、功能和工具称为 Palantir 平台。

![](https://media.techwhims.com/techwhims/2025-02-06-070459.png?x-oss-process=style/origin)

其中比较关键的是 `The Ontology` !  

公司业务都会面临如何实时实时执行最佳决策的挑战，Ontology 这个产品可以自动将相关数据，逻辑和动作组件集成到计算环境中，支持传统的 BI 和分析工作流、**通过AI团队来迅速开发运营应用程序**。

可以这么说， Ontology 是支持决策的一个系统。

> "We don’t simplify the solution so that it will scale. We automate the complexity so our solution can accelerate while maintaining the flexibility our customers demand."

Palantir 将“决策“做了一个拆解，拆解为 数据、逻辑、行为

> Every decision can be broken down into data, logic, and actions.

![](https://media.techwhims.com/techwhims/2025-02-06-091007.png?x-oss-process=style/origin)

- data： 为这个决策，关于运营的哪些相关事实或真相构成了此决策的背景信息
- logic：业务规则如何充当此决策的指引，在不同假设下，特定结果的概率是多少？我们在以前类似的情况下做了什么，结果如何？我们的预测和优化模型有哪些输入？
- actions：这个决策在组织或者业务中的影响是什么，是否可以减少预期结果中的步骤动作等等

在 Palantir 平台中，所有这些组件都在促进 **AI 协作模式**。 

> tips: 数据和 AI 的事情不只是产研的事情，更是业务多个角色协作的事情。


### Data Model
Ontology 将数据整合为 **对象和链接**， 我觉得是一种比较好的抽象，方便后面的人机协作概念上的简化。

1、这里支持的数据范围很广，支持各种数据类型以及许多扩展的原语。比如语义搜索非结构化数据、媒体数据（图像、语音、视频）、value types。

2、Data model 数据模型还支持开箱即用，用于探索结构化、非结构化、地理空间、时间、模拟和其他数据模式。这些基本工具通过 AIP 助手得到增强，从而显著缩短了在平台中探索和分析数据的价值实现时间。

3、能够创建 API 网关和各种 SDK，方便整个数据总线的构建

![](https://media.techwhims.com/techwhims/2025-02-06-073355.png?x-oss-process=style/origin)

将所有数据汇总起来只是第一步，数据之间互通、并且以很好的结构组织起来，是非常大的挑战。这里 **Palantir 平台提供一个可扩展的多模式数据连接和集成框架，可与企业数据系统无缝集成**。

这里Pipeline Builder 将 LLM data transformation 整合到一站式工具包内，这样能够使用最新的大型语言模型来驱动基于管道的转换，例如分类、情感分析、摘要、实体提取或翻译。

这里为了加速 AI 工程，AIP Assist 访问知识库文档和 代码库来加速辅助。

至此，数据准备已经 ok。 数据转化、提取、关联都已经构建完成，为下一步的 logic 提供数据基础。

### Logic 

什么是 logic，Palantir 是通过以下的方式定义和执行：model、business logic、templated analyses and reports （模型、业务流程、模版分析和 BI 报告）

![](https://media.techwhims.com/techwhims/2025-02-06-073355.png?x-oss-process=style/origin)

- Model  ： Generative AI, LLMs, forecasts, optimizers, etc
- Business Logic：Business rules, process mapping, semantic search
- Templated Analyses and Reports：Object views, analysis templates, generated reports

这三个逻辑方面——模型、业务逻辑以及模板化分析和报告——结合起来，提供了一套工具，用户可以从中选择组合，为决策者提供关键时刻所需的所有背景信息。

### Actions

> For any decision to have an impact, the decision must propagate into the world. 

![](https://media.techwhims.com/techwhims/2025-02-06-085501.png?x-oss-process=style/origin)

在大多数模式中，AI 代理并非直接进行更改，而是通过与集成到 Workshop 中的 AIP 逻辑函数的同步集成，或通过 自动化 或流水线构建器中的 使用大语言模型节点进行异步集成来创建建议。然后，该建议可以呈现给操作员进行改进、反馈和最终决策。除了**加强“人机协同”范式**外，这种基于建议的模式还生成有价值的元数据，从而实现一个积极的循环，使代理能够通过持续反馈学习和发展。


最后，

**ontology整合所有相关数据后搭建出公司运作的一个模型，这个模型提供了一个可以让所有下游工作流的决策者或员工，比如leader、一线业务人员等等都参与进来的共用操作系统。**

另外比较有特色的是，**提供模型的模拟功能**，在每一个小决策和大决策之前，决策者都能够通过模型模拟来“预测”自己决策带来变动和影响。每个模拟还可以叠加，比如下游的一个业务一线人员先模拟一次，然后中游的两个下游分析师再分别模拟一次，最后上游的两个产品经理再在两个先前的模拟结果上继续模拟出4个结果，最后将结果做比对。

（完）