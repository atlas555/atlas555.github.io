---
title: "推荐算法之ROC、PR曲线介绍 - Resys Roc Pr Curved Shape"
date: 2022-05-20T17:17:04+08:00
author: "张晓龙"
slug: resys
draft: false
keywords: 
- resys
- 推荐系统
- ROC
description: "介绍推荐算法中使用 ROC 评估，并且介绍 roc 曲线" 
toc: false
tag: resys
---

先分享一个学习中的case：很早之前我在评估推荐算法的时候使用的是准确率，然后在分享时被别人各种吐槽不专业。后来学习的多了，发现准确率只是评估方法中一种，且对于样本极大不均衡分类问题没多大意义。所有后续快速学习其他方式。

下面我们首先来看下，什么是ROC曲线。

# ROC曲线
Receiver operating characteristics (ROC)曲线一开始是用在医疗判断上的，后来才应用到机器学习和数据挖掘上。ROC曲线一般用在分类器分类效果评估上，而且可以可视化算法的分类效果。

我们以二分类问题来学习ROC，假设用{p,n}来表示样本正例和负例的标签，并且使用分类模型来对样本进行预测，一些预测模型会输出预测分类概率，通过设置不同的分类阈值来对样本分类。我们通过{Y,N}来表示预测结果中的预测正例和负例，则有下面这张概念性的好图，即混淆矩阵，
![confusion matrix](http://bed-image.oss-cn-beijing.aliyuncs.com/mweb/roc_pr/confusion_matrix.jpg)
途中可以看到，如果样本正例被判断为正例，则为TP，否则为FN；同样的样本负例被判断为正例，则为FP，否则为TN。剩下的几个概念都是围绕这四个象限的值推算出来的。本文主要是围绕fp rate和tp rate关系来讲，其他像F值等后续在分享。

![](https://bed-image.oss-cn-beijing.aliyuncs.com/mweb/roc_pr/fp.jpg)
![](https://bed-image.oss-cn-beijing.aliyuncs.com/mweb/roc_pr/sp.jpg)
首先 **true positive rate**，同时也被称为熟悉的命中率或者召回率，这个在搜索排序评估中应用很多，**fase positive rate**称为误报率，即负例样本被判断为正例样本。

## ROC曲线图
ROC曲线图是一个二维图，横坐标是fp rate，纵坐标为tp rate，曲线图描述的是收益和损失之间的tradeoff。我们具体看下示例图，
![](http://bed-image.oss-cn-beijing.aliyuncs.com/mweb/roc_pr/roc.jpg)
图中有5个点A、B、C、D、E，代表在不同fp rate比率下tp的值，即（fp rate,tp rate）坐标。图中有几个特殊的点，就是：

	（0，0）：算法策略从没有区分一个正例，同时也没有错分类的错误
	（0，1）：代表完美的分类算法，图中的D坐标就是例子。
	（1，1）：同（0，0）相反，给一个例子判断正例和非正例的概率是一样的，可以看成是随机预测。
（0，0）和（1，1）都是极端的例子，这两个点之间的连线就比较有意思了，这条直线表示随机策略的输出，比如C点（0.7，0.7）表示正例被判断正确是0.7，负例被判断为正例的概率也是0.7。很容易理解越靠近左上角的点表明正例判断正确的概率大，判断正例的概率小，分类算法比较好。越靠近有上角的点表明对正例判断比较准确，但是会存在把负例判断成正例的可能性越大。所以我们一般更加关注靠近**左上角的区域**。

每一个点代表分类器在**某一个阈值**的下分类的效果，首先需要理解其中的阈值，比如阈值设置为0.5，则预测概率大于0.5的为正例，否则反之。

下面举个栗子，有20个正负样本，假设根据贝叶斯分类器做预测，
| 栗子编号 | 正负样本 | 概率评分 |
|---|---|---|
| 1 | p | 0.9 |
| 2 | p | 0.8 |
| 3 | n | 0.7 |
| 4 | p | 0.6 |
| 5 | p | 0.55 |
| 6 | p | 0.54 |
| 7 | n | 0.53 |
| 8 | n | 0.52 |
| 9 | p | 0.51 |
| 10 | n | 0.505 |
| 11 | p | 0.4 |
| 12 | n | 0.39 |
| 13 | p | 0.38 |
| 14 | n | 0.37 |
| 15 | n | 0.36 |
| 16 | n | 0.35 |
| 17 | p | 0.34 |
| 18 | n | 0.33 |
| 19 | p | 0.30 |
| 20 | n | 0.1 |
我们根据这些点绘制一张ROC的点图，从高到低，依次将“Score”值作为阈值threshold，当测试样本属于正样本的概率大于或等于这个threshold时，我们认为它为正样本，否则为负样本，则可以绘制下图，
![](http://image.bfstack.com/mweb/roc_pr/sample.jpg)
如果将这些(FP rate,TP rete)对连接起来，就得到了ROC曲线。当threshold取值越多，ROC曲线越平滑。

## 计算ROC曲线
通过上面的例子，我们知道怎么计算离散点的ROC线，但是平时看到的都是连续平滑曲线，那怎么通过算法实现呢？下面的是一个高效生成ROC曲线的方式，
![](http://image.bfstack.com/mweb/roc_pr/alg.jpg)
算法输出的是一个一个label，那label连起来就是我们看到的ROC曲线？NO，NO，NO，如果你连起来看发现是个不规则的曲线（不是凸包曲线），ROC的计算还是有其他的优化操作，后续我有时间在讲讲。

## AUC计算
评估一个分类算法的好像，可以看ROC曲线，但是给你两个曲线，你怎么比较两个分类算法的好坏呢？
比如下图的例子，
![](http://bed-image.oss-cn-beijing.aliyuncs.com/mweb/roc_pr/auc_ca.jpg)
你能看出来哪个是最优的么？A、B、C？所以这里引入了AUC值，即计算ROC曲线下面积。

由于ROC曲线面积下面积范围是0-1，且随机算法的AUC为0.5，所以一般AUC算法评估的范围是：0.5-1，较好的区分算法的平均性能。如果要问为啥AUC能比较分类算法的好坏，深入研究的话请翻阅具体文献。

强调一下，我这里举得例子都是基于二分累算法的例子，多分类的ROC和AUC需要在此基础上做扩充。

总之，ROC曲线是一个非常有用的评估分类算法性能的工具。基于混淆矩阵，提供了若干个评价指标，相比接下来的PR曲线，有更多的优势。当然，在生产环境中使用时，是结合多个评价工具的，比如ROC、PR、CrossValidation等等。

# PR曲线
基于混淆矩阵，PR(precision recall)曲线表现的是**precision和recall**之间的关系，如图所示：


# ROC和PR的关系


## 如何选择？

https://www.quora.com/What-is-the-difference-between-a-ROC-curve-and-a-precision-recall-curve-When-should-I-use-each
