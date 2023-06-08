---
title: "学习chatGPT的前世今生总结：发展历史、趋势、局限、可能的应用场景"
date: 2023-06-05
author: "张晓龙"
slug: chatgpt-history-and-application
draft: false
show_toc: true
keywords:
- ChatGPT
- GPT-5
- gpt应用场景
description : "学习chatGPT的前世今生总结：发展历史、趋势、局限、可能的应用场景"
categories: AI
tags:
- chatgpt
---

现在 GPT 的热度依然在，最近我在做 GPT 的应用落地，所以看看它的发展历史，可能得应用场景得分享。你用它，需要知道它是个什么。

预训练语言模型 – GPT1，名字来源于论文“[Improving Language Understanding by Generative PreTraining, OpenAI, Jun, 2018](https://www.cs.ubc.ca/~amuham01/LING530/papers/radford2018improving.pdf)”。

![预训练语言模型 – GPT1](https://media.techwhims.com/techwhims/2023/2023-06-05-16-10-34.png)

chatgpt 家族的对比

![ChatGPT](https://media.techwhims.com/techwhims/2023/2023-06-05-16-31-23.png)

接下来大模型的发展

![2023-2024 optimal language model size highlights](https://media.techwhims.com/techwhims/2023/2023-06-05-16-35-19.png)

![a simplified version of this full GPT-4 vs human viz](https://media.techwhims.com/techwhims/2023/2023-06-05-16-40-30.png)【[source](https://s10251.pcdn.co/pdf/2023-Alan-D-Thompson-GPT-4-Tests-Simple-Rev-0.pdf)】

![GPT-4 vs human](https://media.techwhims.com/techwhims/2023/2023-06-05-16-45-25.png)

![dataset](https://media.techwhims.com/techwhims/2023/2023-06-05-16-39-54.png)

Timeline to GPT-5
![Timeline to GPT-5](https://media.techwhims.com/techwhims/2023/2023-06-05-16-42-51.png)

ChatGPT有什么用？

1. 教育场景
   1. 改论文、写代码、做作业、查资料   -> 会出错！
2. 军事国防领域
![2023-06-05-16-47-59](https://media.techwhims.com/techwhims/2023/2023-06-05-16-47-59.png)

3. 医疗保健
4. 互联网和 IT 领域
   1. bing/bard/文心一言
   2. 代码生成
   3. pdf 分析
   4. 漏洞发现
5. 文娱方面
6. 商业营销：客户服务、推荐系统、商品描述、广告推荐
7. 法律、金融、工商业、文件材料

> “If you want to know what will happen in the next 5 years you don’t look at the mainstream, you look at the fringe”
> —-- Steve Jobs, 1994

相关材料

1. [https://lifearchitect.ai/gpt-5](https://lifearchitect.ai/gpt-5/#)
2. [ChatGPT的前世今生·李丕绩](https://lipiji.com/slides/ChatGPT_ppf.pdf)

---
2023.6.6 更新添加 >>> 来源于【OpenAI 闭门讨论会 V3【GPT-4】纪要·拾象科技】


GPT4 的市场预期 和 新想法：

- 类比 iPhone，Code、系统、基础工具能力层面都是能做，但是做不了 Facebook 网络，Uber 打车/管车，airbnb 等重业务，所以创业要考虑垂直领域。
- 加了图像能力之后， GPT4 拥有视觉信息，一定程度上可以更像人；可以考虑 更复杂的事情，比如控制机器人，实现类似 adept 的自动机制。

GPT4 和对手的对比

- 从 POE 可以体验，Anthropic 的 claude+ 和 GPT4 并没有差很远，只是 Anthropic 从不宣传。
- 目前 GPT-4 的变强的能力很多都能预期到。算力拉满后，多模态的涌现能力会 加强，GPT-4 的 vision + Language 会有预料之外的涌现能力，之后加上 video 会有更多

GPT4 改变什么，如何做应用

- 当模型在某方面的能力超过人类最强，游戏规则会改变。
- OpenAI 模型本身变强，一定会有很多已有的 APP 受到影响。

从 GPT-3 到 GPT-4 能力的暴涨，从算法、算力、数据三要素来 分析

- 底层还是基于 transformer， 而 transformer 已经是 2017 年发布的论文。数据是大 量互联网爬虫， Chrome 占了一大半数据， 维基百科、 reddit 等数据也一直都 在。
- 效果的上升应该是算力的提升带来的：单卡算力提升受摩 尔定律限制，每一两年提升两三倍。这次算力的暴涨来自于大规模分布式训练， 用一台机器和一万台机器，算力暴涨 1 万倍，这是目前是人类最大的分布式计 算集群。
- 这次之所以能做更大规模的分布式训练，得益于高速互联的网络，现在的核心 网能到 800G。 但是网络传输的上升如果到了上限，分布式规模就上不去，总算 力就上不去。

如何定义界限？人的界限在哪？大模型未来的发展会不会超过了人的能力

- GPT-4 主要解锁了三个能力，第一个多模态，第二个是提高 prompt 数量，第三 个 hard task 有更多突破，
- GPT 解锁的是跟人对话的能力，如果能无限的 prompt，模仿人 的记忆，理论上可以把对话无限的拉长，真正地去模拟人的一些思考或者情感。 受限的话，它会把前面的内容忘记掉。

OpenAI 继续变强之后，哪些大概率受到冲击，哪些会有一些壁垒

- 可能会彻底改变工作生产模式。 OpenAI 去考 GRE、 大学课程，都能考到前 5%， 也能画 PPT。 很可能之后在组织内部，应届大学生只要 20 美金/月、并且供应 是无限的，因为 GPT4 已经超越了很多接受大学四年本科通识教育的大学生的 水平了。

GPT-4 的考试能力这么厉害，是什么东西解锁的？

- 把 video、图像的数据给进去，通过多模态的方式迁移过来了。 
- 可能用之前的 training data， 以及 reinforcement learning 的时候的标注。
- 来源于专业考试的训练数据：

如何定义 GPT 的能力边界

- 越无限游戏的越不好解决。无限游戏的核心是不断拓宽边界、制定新的规则
  - 有限游戏：以取胜为目的，拥有明确的开端、终结和界限，在开赛前，参与者需要 对游戏规则和获胜条件达成一致，规则在游戏进行当中不可改变；
  - 无限游戏：以延续游戏为目的，因此无限游戏没有明确的开端、终结和界限。为了 让游戏延续，规则可以在游戏进行中改变。
- ChatGPT 理性思考能力很强，但涉及到感性、人情世故、办公室政治斗争等方 面是不行的。这是因为 objective 中第三点提到的 harmless。 因为需要符合一个 普世的价值观。对于自然科学，只要背后有规律，神经网络学起来比较容易。 但社会科学，像勾心斗角，就像股票，背后的规律非常复杂，而且很难学。不过社会科学可能不是 OpenAI 及大多数公司关心的点。
- 把某个问题的科研边界向前推进可能是模型短时间内无法做到的。
- GPT 其实还可以避免了人的冲动，是非常理性的，社交水平还可以。
- 因此未来发展 很关键的一点是，如何用更少数据去训练模型。
- 在 GPT 给出不符合要求的回答后，告诉他不对，不断加强反馈，很大 程度能在不改变模型的前提下解决 hallucination 问题。

- GPT 能取代技术、蓝领、机械性的逻辑工作。但自我认知、共情力是未来在招 人的时候是非常重要的，机器无法取代。
- GPT 会改变现在的金字塔形状的组织架构，组织的边界在快速扩大，变为网络 化。传统的雇佣模式也在发生变化， AI 更像是公司中层。

如果短期来看，AI 产品能做好，其特点可以总结为以下几点

- 不改变原来的使用习惯，这代表了它的替换成本比较低。
- 确实能够解决一个比较痛点的问题。或者说不太痛点的问题，但是有多个类似 小场景的叠加来提供比较大的增量价值。
- 定位一定是做 0 到及格线成绩的事情。是一个助手辅助的定位，而不是全面替 代。

垂类应用的机会：

- 垂类应用中，像客服、写作、儿童陪伴、心理咨询、员工服务这些垂类应用是 值得看好的，是因为这件事情本身就是重复机械的知识推理，用 GPT 可以实现 直接覆盖。
- 像 SEO 内容写作，儿童陪伴，则是需要一个长久持续性的过程，也需要有不断 的新内容去产生，因此 GPT 也可以适用于这方面。提到心理咨询，现在数据 标注的公司会接收到很多心理咨询类文本的标注需求，可能代表这个市场是会 优先被孵化出来的。
- 输入法作为掌握握所有内容输入的入口，可能会有一些比较大的变化。国外一家输入法公司， 将其产品接入 AIGC 的能力，根据用户以往打出来的字进行自动高级联想。
- 应用的数量和质量都会井喷，人人都可以做 App，但 middle layer 的价值会 变大

垂直应用的问题

- 可用到可卖存在巨大的鸿沟。现在许多产品都是 MVP，能够非常快速的完成 0 到 60 分的事情。但是如何从 60 分变到 90 分，没有很好的方法，即便是 Midjourney， 对于一张图的阐述，实现到 70 分很快，但是 70 分到 90 分的调优 方法，用户是完全不知道的，一些客服工具，也是类似。