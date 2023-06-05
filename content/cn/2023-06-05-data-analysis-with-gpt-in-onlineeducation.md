---
title: "ChatGPT 在线教育业务下数据分析领域的初步应用真实案例"
date: 2023-06-05
author: "张晓龙"
slug: data-analysis-with-gpt
draft: false
show_toc: true
keywords:
- ChatGPT
- 在线教育
- 数据分析
- 真实案例
description : "ChatGPT 在线教育业务下数据分析领域的初步应用真实案例"
categories: 在线教育
tags:
- 在线教育
- chatgpt
- 数据分析
---

我们在公司外出培训的时候（20230523），做了一个 ChatGPT 在数据分析应用的 demo，验证这个方向是否可行。

## 我们的项目方案

用 chatGPT 理解人的需求（语音、文字），生成可执行的 DSL（SQL），执行获取数据然后根据数据特征，选择合适的数据表达方式（图表）进行分析，最后给出一些基础分析和数据洞察。

![AI改造数据分析中的数据准备、增强分析、结论输出以及可视化展示环节](https://media.techwhims.com/techwhims/2023/2023-06-05-10-27-36.png)

## 方案的整体结构

核心是利用 gpt：

（1）解析语句，理解自然语言，然后将这个转换为 DSL或者 SQL

（2）拿到数据后，分析数据 feature，选择最优的数据表达方式

（3）基于经验和输入的内容，做基本分析和数据洞察

### 方案架构

![2023-06-05-10-28-37](https://media.techwhims.com/techwhims/2023/2023-06-05-10-28-37.png)

### 工程架构中的一些关键点

第一是解析语句生成 DSL 或者 SQL 有一个前置条件是有业务信息输入，这里我们设计的是使用数据仓库中的数据模型（metadata 和 model），输入的自然语句结合业务元信息能够很好的生成可执行的 DSL，这个点我们验证是可行同时准确度在一定的业务范围内还是不错的（[chatgpt生成 sql准确性的局限性-- 40% vs human 92.6%？,--> 论文:Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs](https://arxiv.org/abs/2305.03111)）；

第二个调教 chatgpt prompt 如何更好的分析数据特征，选择合适的图标，这里我们发现在选择合适的图标能力不太稳定，也就是同样的数据和输入 prompt，生成的图标表达会变化。

第三个关键是做基础分析和数据洞察，基于数据有基础的分析能力，比如最大最小、同比环比、数据趋势等等，这些是图标数据的解读，偏确定性的东西 chatgpt 能够很好的胜任，但在数据洞察上出现了很大的问题，输出的洞察内容基本是“一本正经的胡说八道”。期待 gpt 可以有高级分析师的能力，但是不达预期。我们初步分析一是输入的业务信息不够，二是调教的 prompt 不好，需要更多的精力投入分析。数据洞察上整体看，chatgpt 的瓶颈还是比较大的。

## 真实案例演示

### 项目 demo 架构采用 flask web + gpt-3.5-turbo + echarts

- flask 做项目演示的web 框架，方便展示，同时 python 代码也可以用 chatgpt 生成
- chatgpt 分析自然语句、生成 SQL（DSL）、生成 echarts 的可视化代码、生成 flask 的核心运行代码、生成数据分析和数据洞察结论
- echart 做图标表达

一些核心、简单的chatgpt 的 prompt 案例：

``` bash

# 1. 输入业务信息、数据模型
    prompt_1 = '''有如下一个clickhouse表，CREATE table xxx.xxx ()...

# 2. 分析数据，生成 echart 代码
    prompt_2 = "以下是一个二维表格,根据这个二维表格的数据量和内容，给出利用分析的echarts图表的option代码,并以json格式输出,不要输出解释文字,也不要有回车"

# 3. 数据分析和洞察
    prompt_3 = "基于上面数据，给一个详尽的分析报告，报告包括结论，分析过程，有前瞻性的洞察观点，字数限制在 100 字内"
```

### 真实效果

![chatgpt在线教育业务下数据分析领域的初步应用真实案例](https://media.techwhims.com/techwhims/2023/d269cd0f-f7c2-4756-b46b-cb5e56f27ab9.png)

关键 log,xxx 为脱敏的内容

``` bash
2023-06-05 11:14:57,530 [WARNING] * Debugger is active!
2023-06-05 11:14:57,538 [INFO] * Debugger PIN: 935-298-896
2023-06-05 11:28:22,919 [INFO] Request Data : 统计学年是2023年春季, 各课程二级部门的可续人次，纯续人次, 并算出续班率。.
2023-06-05 11:28:27,299 [INFO] ChatGPT generate SQL :
SELECT
xxx AS "课程二级部门",
sum(xx) AS "可续人次",
sum(xx) AS "纯续人次",
round(sum(xx) / sum(xx), 4) AS "续班率"
FROM xxx.xxx
WHERE xx = '2023春季'
GROUP BY xxxx
2023-06-05 11:28:28,239 [INFO] ChatGPT auto achieve data from oneservice : [[xxx]].
2023-06-05 11:28:39,405 [INFO] ChatGPT auto choose echart type depend on data feature , genereate echart code:
2023-06-05 11:28:39,406 [INFO] ChatGPT auto transform option object to json object: {
"tooltip": {
"trigger": "item",
"formatter": "{a} {b}: {c} ({d}%)"

},
"legend": {
"orient": "vertical",
"left": "left",
"data": [xxxxx]
},
"series": [
{
"name": "续班率",
"type": "pie",
"radius": ["xxx0%", "xxx0%"],
"avoidLabelOverlap": false,
"label": {
"show": false,
"position": "center"
},
"emphasis": {
"label": {
"show": true,
"fontSize": "30",
"fontWeight": "bold"
}
},
"labelLine": {
"show": false
},
"data": [
{"value": 0.x, "name": "xxx"},
{"value": 0.xx, "name": "xxx"},
{"value": 0.xxx, "name": "xxx"},
{"value": 0.x, "name": "xxx"},
{"value": 0.xx, "name": "xxx"},
{"value": 0.xxx, "name": "xxx"},
{"value": 0.xxx, "name": "xxx"}
]
}
]
}.
2023-06-05 11:28:45,154 [INFO] ChatGPT auto analysis data : 该二维表格展示了不同课程二级部门的可续人次、纯续人次和续班率。从数据中可以得出，xxx的续班率最高，为xxx，而xxx的纯续人次最少，为380.72。xxx的可续人次最多，为xxx，但续班率却比xxxx低，为xxxx。分析数据，可以考虑优化xxxx的课程内容以提高纯续人次，也可借鉴xxxx的做法，提高其他部门的续班率。结合用户反馈和市场需求，未来可将更多资源投入优化xxxxx的课程。
```

### 一些结论

1. 在具体的业务场景，比如在线教育里面数据分析场景，chatgpt 能够做好一些基础分析
2. 业务分析，强依赖业务信息的输入，洞察和决策能力在chatgpt 3.5 版本上瓶颈还是比较大，在 4.0 上待验证
3. 数据分析流程上能够自动化的点，都可以应用 chatgpt 搞定，提升整体效率是肯定的
4. 出于数据安全的考虑，chatgpt 在垂直行业领域上内容的缺失，是在行业应用上的最大卡点
5. chatgpt 的数据分析能力上限，是使用 chatgpt 角色的能力上限，这两者是匹配的

## 数据分析管家的可能性

智能分析管家概念的由来，进一步发挥 chatGPT 的能力

![智能分析管家概念](https://media.techwhims.com/techwhims/2023/2023-06-05-10-34-17.png)

设计的概念原型：

![智能分析管家原型](https://media.techwhims.com/techwhims/2023/2023-06-05-10-37-27.png)

##  chatgpt 在数据分析上的一些不足 & 继续提升的点

ChatGPT 在数据分析中语义理解、生成 SQL 等方面的不足：

- 语法问题：ChatGPT生成的代码可能存在语法错误或不符合语言规范，这可能导致代码无法编译或执行。
- 逻辑问题：ChatGPT生成的代码可能存在逻辑错误或不符合预期的行为，这可能导致程序出现不可预测的结果。
- 性能问题：ChatGPT生成的代码可能没有优化，这可能导致程序的性能较低或运行速度较慢。
- 安全问题：ChatGPT生成的代码可能存在安全漏洞，例如代码注入或跨站点脚本攻击，这可能导致程序遭受攻击或数据泄露。
- 数据量问题：生成代码的质量和准确性取决于训练数据的数量和质量。如果数据量过小或不充分，那么生成的代码可能不够准确或不可用。
- 编码风格问题：ChatGPT生成的代码可能与团队的编码风格不符，这可能导致代码难以维护或团队协作出现问题。
- 可读性问题：ChatGPT生成的代码可能不易于理解或阅读，这可能导致困难或耗时的调试工作。
- 缺乏创造性：ChatGPT的代码生成能力主要基于已有的数据和信息，可能缺乏创造性和新颖性，这可能导致生成代码的重复性和缺乏创新性。
- 提取方法问题：选择合适的提取方法非常重要。如果选择的方法不适合数据的类型或格式，那么提取结果可能不准确或不可靠。
- 缺乏背景知识：数据提取需要一定的背景知识。如果缺乏相关知识，那么提取结果可能不够准确或不足够深入。
- 难以处理非结构化数据：ChatGPT在处理非结构化数据方面可能存在一些困难。非结构化数据通常不易于处理和分析，因为它们缺乏明确的格式和组织方式。

ChatGPT 在具体业务数据分析上的局限性（依赖数据治理、分析思路、业务背景&经验）：

- 数据质量问题：数据分析的准确性和可靠性取决于数据的质量。如果数据存在错误、重复或缺失，那么分析的结果就可能不准确或不可靠。
- 数据样本量问题：数据量不足可能会导致分析的偏差和不准确性。如果样本太小，那么分析的结论可能不具有代表性。
- 数据分布问题：数据分布的形状和类型可能会影响分析的结果。例如，如果数据呈现偏态分布，那么平均值可能并不是很有意义。
- 分析方法问题：选择合适的分析方法非常重要。如果选择的方法不适合数据的类型或分布，那么分析结果可能不准确或不可靠。
- 缺乏背景知识：数据分析需要一定的背景知识，如果缺乏相关知识，那么分析结果可能不够准确或不足够深入。
- 语义和文化差异：ChatGPT是一种基于语言模型的人工智能，但是语言的含义和文化差异可能会影响数据分析的结果。例如，同样的数据在不同的国家和地区可能会有不同的含义和解释。
- 缺乏人类直觉：数据分析需要一定的直觉和经验，这是ChatGPT无法完全替代的。人类能够通过直觉和经验判断是否出现了异常或者是否需要进行更深入的分析，而ChatGPT可能无法做到这一点。

---

**20230605 更新**

> 无独有偶，发现阿里达摩院与新加坡南洋理工大学在这个方向发了论文： [Is GPT-4 a Good Data Analyst?](https://arxiv.org/abs/2305.15038)，探讨了 GPT-4 能否做好数据分析师的工作，论文重点考察了 GPT-4 作为数据分析师的以下几种能力：
> 
> 1. 生成 SQL 和 Python 代码;
> 
> 2. 执行代码获得数据和图表;
> 
> 3. 从数据和外部知识源中分析数据，得出结论。
>
> Abstract：
> 
> "As large language models (LLMs) have demonstrated their powerful capabilities in plenty of domains and tasks, including context understanding, code generation, language generation, data storytelling, etc., many data analysts may raise concerns if their jobs will be replaced by AI. This controversial topic has drawn a lot of attention in public. However, we are still at a stage of divergent opinions without any definitive conclusion. Motivated by this, we raise the research question of "is GPT-4 a good data analyst?" in this work and aim to answer it by conducting head-to-head comparative studies. In detail, we regard GPT-4 as a data analyst to perform end-to-end data analysis with databases from a wide range of domains. We propose a framework to tackle the problems by carefully designing the prompts for GPT-4 to conduct experiments. We also design several task-specific evaluation metrics to systematically compare the performance between several professional human data analysts and GPT-4. Experimental results show that GPT-4 can achieve comparable performance to humans. We also provide in-depth discussions about our results to shed light on further studies before we reach the conclusion that GPT-4 can replace data analysts."
>
> 这周花时间研究下这篇论文