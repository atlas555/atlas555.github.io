---
title: "为什么要演进到湖仓一体（数据湖架构）- 他山会"
date: 2023-05-15
author: "张晓龙"
slug: why-choose-datalake
draft: false
show_toc: true
keywords:
- 数据湖
- 湖仓架构
- LakeHourse
- 网易
- 快手
description : "为什么要演进到湖仓一体（数据湖架构）- 他山会-part one"
categories: bigdata
tags: 
- datalake
---

# 为什么要演进到湖仓一体（数据湖架构）- 他山会 part one

我在规划我们公司由 `离线数仓` 到 `湖仓一体` 演进。通过[他山会]()的方式进行推进。

## 快手为什么选择 hudi？

源于 2023.5 datafun 分享。

快手的数据建设目标是：①标准统一；② 可共享；③ 简单易用；④ 高性能；⑤ 成熟安全可靠。 离线数仓架构采用的是 Lambda 架构。遇到问题：①时效差；② 处理逻辑异构；③ 数据孤岛

数据湖满足数据建设的目标，同时兼具以下特性：① 海量存储；② 支持可扩展的数据类型；③ Schema 演进；④ 支持可扩展的数据源；⑤ 强大的数据管理能力；⑥ 高效数据处理；⑦ 高性能的分析

Hudi 在摄入、处理、存储到查询，基础能力支持地比较完善，能够支持数据湖的快速构建和应用，包括：`更新能力强，支持流批读写，可插拔的 Payload，支持 MOR 表类型，适配多种查询引擎，丰富的数据管理操作`等。

快手基于 Hudi 构建的数据湖架构具有以下优势：

① 数据 CURD。优化生产场景模型，提升了整体`更新场景的时效`；

② 流批读写。实现统一的处理，减少了多链路多引擎的建设成本；

③ 海量数据管理。对所有的入湖数据进行统一管理，数据平台的服务和管理方面能够复用，降低数据的使用成本。

**hudi的基本能力**

- 支持不同类型的写入方式：通过`增量写入和数据合并的两个基本操作，实现快照的生成`
- 可插拔：可支持所需要的更新逻辑，比如定制化更新模式，可以基于此进行扩展应用场景
- 表类型：增量写入和数据合并的操作共同组成快照更新。这两种基本操作的实现决定了表的类型。不同类型的表，作用不同的应用场景
- 元数据统计
- 读取方式：支持 Hadoop 的 inputformat 的方式，兼容常用的查询引擎，比如spark、trino 等

使用 Hudi ，`提效 + 统一`。

**使用 Hudi 快手遇到的问题：**

1. 数据摄入瓶颈
2. 无法使用数据时间进行快照查询
3. Flink on Hudi 的更新瓶颈
4. 多任务合并能力不足（多任务合并宽表）
5. Hudi 生产保障困难

收益

1. 准实时的生成 DWD 层的动态更新数据
2. 将离线链路升级成了准实时的链路，在计算资源上持平，时效上有 50% 以上的提升（处理链路的计算时间缩短，最长时间节省 5 个小时）
3. 将离线快照的更新时效从小时级缩短到了分钟级，整体时效达到十多分钟左右，而且计算资源比以前节省了 15%（在链路计算过程中所占用的临时存储空间和计算资源得到了节省）

## 网易数据湖Iceberg 探索和实践

源于 2020.10 datafun 分享。

**网易数据仓库的痛点**

1. 凌晨一些大的离线任务经常会因为一些原因出现延迟，这种`延迟会导致核心报表的产出时间不稳定`，业务难受
   1. 任务本身要请求的数据量会特别大 -> NameNode的压力是非常大 -> Namenode响应很慢的情况，如果请求响应很慢就会导致任务初始化时间很长
   2. 任务本身的ETL效率是相对低效(数据存储问题，不是 spark 的问题)
   3. 大的离线任务一旦遇到磁盘坏盘或者机器宕机，就需要重试
2. `不可靠的更新操作`（insert overwrite的操作,会先把相应分区的数据删除，再把生成的文件加载到分区中去,移除文件的时候，很多正在读取这些文件的任务就会发生异常）
3. 表Schema变更低效（加字段、改分区 et）
4. 数据可靠性缺乏保障（分区信息存储DFS和Metastore，更新操作有可能出现不一致）
5. 基于Lambda架构建设的实时数仓存在较多的问题
   1. 多条链路多份数据，结果可能对不上、Kafka无法存储海量数据， 无法基于当前的OLAP分析引擎高效查询Kafka中的数据、Lambda维护成本高
6. 基于Lambda架构数据更新不友好
   1. 一种是CDC ( Change Data Capture )，将binlog中的更新删除同步到HDFS上
   2. 延迟数据带来的聚合后结果的更新

基于痛点，对比数据湖产品。

- DELTA LAKE，在17年的时候DataBricks就做了DELTA LAKE的商业版。主要想解决的也是基于Lambda架构带来的存储问题，它的初衷是希望通过一种存储来把Lambda架构做成kappa架构。
- Hudi ( Uber开源 ) 可以支持快速的更新以及增量的拉取操作。这是它最大的卖点之一。
- Iceberg的初衷是想做标准的Table Format以及高效的ETL。

![阿里Flink团体针对数据湖方案的一些调研对比](https://media.techwhims.com/techwhims/2023/2023-05-15-15-53-20.png)

Metastore 和 Iceberg在表格式的4个方面对比：① 在schema层面上没有任何区别；② partition实现完全不同（metastore 中partition字段本质上是一个目录结构，iceberg中partition字段就是表中的一个字段）；③ 表统计信息实现粒度不同（Metastore中一张表的统计信息是表/分区级别粒度的统计信息，Iceberg中统计信息精确到文件粒度）；④ 读写API实现不同

**Iceberg相对于Metastore的优势**

- 新partition模式：避免了查询时n次调用namenode的list方法，降低namenode压力，提升查询性能
- 新metadata模式：文件级别列统计信息可以用来根据where字段进行文件过滤，很多场景下可以大大减少扫描文件数，提升查询性能
- 新API模式：存储批流一体
  1. 流式写入-增量拉取（基于Iceberg统一存储模式可以同时满足业务批量读取以及增量订阅需求）
  2. 支持批流同时读写同一张表，统一表schema，任务执行过程中不会出现FileNotFoundException

Iceberg 核心提升在
![Iceberg 核心提升在](https://media.techwhims.com/techwhims/2023/2023-05-15-16-05-59.png)

落地 Icerberg ，取得的收益：任务初始化从 40min -> 8min，大大提升ETL任务执行的效率。得益于新Partition模式下不再需要请求NameNode分区信息，同时得益于文件级别统计信息模式下可以过滤很多不满足条件的数据文件

## 爱奇艺：在 Iceberg落地性能优化与实践

源于 2023 datafun 分享。

![数据开发现状](https://media.techwhims.com/techwhims/2023/2023-05-15-16-50-45.png)

Arctic 是一个开放式架构下的湖仓管理系统，在开放的数据湖格式之上，Arctic 提供更多面向流和更新场景的优化，以及一套可插拔的数据自优化机制和管理服务。

![湖仓管理系统-Arctic](https://media.techwhims.com/techwhims/2023/2023-05-15-16-49-03.png)

## huawei 基于Lakehouse架构实现湖内建仓实践经验

源于 2023 datafun 分享。

<gallery>![数据湖在数据处理的几种用法](https://media.techwhims.com/techwhims/2023/2023-05-15-16-28-35.png)![Lakehouse架构使得实时计算进入流批一体阶段](https://media.techwhims.com/techwhims/2023/2023-05-15-16-30-21.png)![现有存量的批量数据和任务转换为实时](https://media.techwhims.com/techwhims/2023/2023-05-15-16-31-40.png)</gallery>

----

2023.5.15 记录。