---
title: "数据湖仓一体架构简图"
date: 2023-04-06T04:30:25+08:00
author: "张晓龙"
slug: datalake-inf
draft: false
show_toc: false
categories: bigdata
description: "介绍数据湖仓一体化架构的演进方向，对比湖仓分体与湖仓一体两种方案。当前主流实践以 Hive 数据仓库结合 Apache Iceberg 构建湖仓分体架构，并逐步向湖仓一体演进，附架构示意图。"
tags:
- 数据湖
- 数据仓库
- Lakehouse
- Iceberg
- 大数据架构
keywords:
- 数据湖仓一体
- Lakehouse架构
- 湖仓分体
- Apache Iceberg
- Hive数据仓库
- 数据湖架构
- 大数据平台
- 数据架构演进
---
记录于 2023.4.6，源于数据湖技术分享。

现在一般有两个方向，湖仓分体是过渡，胡仓一体是最终结果。

我司目前在湖仓分体的方向上演进。即以 hive 为主的 data warehouse 结合 iceberg。

![湖仓架构](https://media.techwhims.com/techwhims/16807704720969.jpg?image/auto-orient,1/watermark,text_dGVjaHdoaW1z,type_ZHJvaWRzYW5zZmFsbGJhY2s,color_c1bfc8,size_20,shadow_55,g_se,t_60,x_10,y_10)
