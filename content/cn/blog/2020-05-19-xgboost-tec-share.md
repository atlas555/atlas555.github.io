---
title: "技术分享之xgboost"
date: 2020-05-19T17:20:20+08:00
author: "张晓龙"
slug: ml-xgboost
draft: false
keywords: 
- xgboost
- ML
description: "技术分享之xgboost"
toc: false
categories: AI
tags: 
- ML
---

本文是团队内部本人的一个技术分享：xgboost介绍及简单分析

## 背景介绍

xgboost的全称是eXtreme Gradient Boosting。正如其名，它是Gradient Boosting Machine的一个c++实现，作者为正在华盛顿大学研究机器学习的大牛[陈天奇](http://homes.cs.washington.edu/~tqchen/)，作者所在公司在线上有xgboost的应用，所以对其简单做一个分享。

XGBoost is an optimized distributed gradient boosting library designed to be highly _**efficient**_, _**flexible**_ and _**portable**_. It implements machine learning algorithms under the [Gradient Boosting](https://en.wikipedia.org/wiki/Gradient_boosting) framework. XGBoost provides a parallel tree boosting (also known as GBDT, GBM) that solve many data science problems in a fast and accurate way. The same code runs on major distributed environment (Hadoop, SGE, MPI) and can solve problems beyond billions of examples.

## 我的PPT分享

{{< googleppt src="https://media.techwhims.com/mweb/xgboost/bfstack_xgboost.pdf" >}} 

### ppt内容：
目录

1.XGBOOST是什么？

2.XGBOOST训练的是什么？

3.XGBOOST怎么训练？

4.XGBoost、Light GBM和CatBoost

eXtreme Gradient Boosting

XGBoost is an optimized distributed gradient boosting library  designed to be highly efficient, flexible and portable.

XGBoost  provides a parallel tree boosting (also known as GBDT, GBM)

The same code runs on major distributed environment (Hadoop, SGE, MPI) and can solve problems beyond billions of examples.

回顾下知识点

Object  Function

Bias Variance Trade-off

Boosting

Gradient  Boost

目标函数

Bias Variance Trade-off

Boosting方法

 Boosting这其实思想相当的简单，大概是，对一份数据，建立M个模型（比如分类），一般这种模型比较简单，称为弱分类器(weak learner)每次分类都将上一次分错的数据权重提高一点再进行分类，这样最终得到的分类器在测试数据与训练数据上都可以得到比较好的成绩。

Gradient  boost

Gradient Boost是一个框架,里面可以套入很多不同的算法

核心：每一次的计算都是为了减少上一次的残差,为了消除残差,可以在残差减少的梯度方向建立一个新的模型

eXtreme Gradient Boosting

XGBoost is an optimized distributed gradient boosting library  designed to be highly efficient, flexible and portable.

XGBoost  provides a parallel tree boosting (also known as GBDT, GBM)

The same code runs on major distributed environment (Hadoop, SGE, MPI) and can solve problems beyond billions of examples.

XGBOOST训练什么

XGBOOST训练的是什么模型？

回归树Regression Tree (CART)

Regression Tree (CART)

Regression Tree Ensemble

Learning a tree on single variable

怎样训练XGBOOST？

Taylor Expansion Approximation of Loss

Refine the definition of tree

Define Complexity of a Tree

Greedy Learning of the Tree

Boosted Tree Algorithm

XGBoost、Light GBM和CatBoost

CatBoost vs. Light GBM vs.XGBoost：[  https://towardsdatascience.com/catboost-vs-light-gbm-vs-xgboost-5f93620723db  ]

2014 年 3 月，XGBOOST 最早作为研究项目，由陈天奇提出

2017 年 1 月，微软发布首个稳定版 LightGBM

2017 年 4 月，俄罗斯顶尖技术公司 Yandex  开源 CatBoost

算法结构差异

LightGBM  使用的是全新的技术：基于梯度的单边采样（GOSS）

XGBoost  则通过预分类算法和直方图算法来确定最优分割

算法对分类变量的处理

如何理解参数

这些模型都需要调节大量参数

算法的表现

算法对分类变量的处理

CatBoost  可赋予分类变量指标，通过独热最大量得到独热编码形式的结果（独热最大量：在所有特征上，对小于等于某个给定参数值的不同的数使用独热编码）

LighGBM  通过使用特征名称的输入来处理属性数据；它没有对数据进行独热编码，因此速度比独热编码快得多

XGBoost  本身无法处理分类变量，而是像随机森林一样，只接受数值数据（因此在将分类数据传入 XGBoost  之前，必须通过各种编码方式：例如标记编码、均值编码或独热编码对数据进行处理）