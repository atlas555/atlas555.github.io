---
title: "数据湖仓一体架构简图"
date: 2023-04-06T04:30:25+08:00
author: "张晓龙"
slug: datalake-inf
draft: false
toc: false
keywords:
- 数据湖
- 湖仓架构
- LakeHourse
description : "介绍数据湖技术分享，湖仓分体和胡仓一体"
categories: 大数据
tags: 
- datalake
---

记录于 2023.4.6，源于数据湖技术分享。

现在一般有两个方向，湖仓分体是过渡，胡仓一体是最终结果。

我司目前在湖仓分体的方向上演进。即以 hive 为主的 data warehouse 结合 iceberg。

![湖仓架构](https://media.techwhims.com/techwhims/16807704720969.jpg?image/auto-orient,1/watermark,text_dGVjaHdoaW1z,type_ZHJvaWRzYW5zZmFsbGJhY2s,color_c1bfc8,size_20,shadow_55,g_se,t_60,x_10,y_10)
