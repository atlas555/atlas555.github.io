---
title: "Log Structured Merge Tree"
date: 2023-04-06T14:30:25+08:00
author: "张晓龙"
slug: algorithm-log-structured-merge-tree
draft: false
toc: false
keywords:
- LSM
- SSTable
description : "介绍LSM 结构树，compact 策略等"
categories: 大数据
tags: 
- algorithm
---

记录于 2023.4.6，源于 hbase 原理的学习。

## LSM 的核心思想

![LSM核心思想](https://media.techwhims.com/techwhims/16807705192490.jpg?image/auto-orient,1/watermark,text_dGVjaHdoaW1z,type_ZHJvaWRzYW5zZmFsbGJhY2s,color_c1bfc8,size_20,shadow_55,g_se,t_60,x_10,y_10)

LSM树有以下三个重要组成部分：

1. MemTable

    MemTable是在内存中的数据结构，用于保存最近更新的数据，会按照Key有序地组织这些数据，LSM树对于具体如何组织有序地组织数据并没有明确的数据结构定义，例如Hbase使跳跃表来保证内存中key的有序。

    因为数据暂时保存在内存中，内存并不是可靠存储，如果断电会丢失数据，因此通常会通过WAL(Write-ahead logging，预写式日志)的方式来保证数据的可靠性。

2. Immutable MemTable

    当 MemTable达到一定大小后，会转化成Immutable MemTable。Immutable MemTable是将转MemTable变为SSTable的一种中间状态。写操作由新的MemTable处理，在转存过程中不阻塞数据更新操作。

3. SSTable(Sorted String Table)

    有序键值对集合，是LSM树组在磁盘中的数据结构。为了加快SSTable的读取，可以通过建立key的索引以及布隆过滤器来加快key的查找。
    ![有序键值对集合](https://media.techwhims.com/2023-04-06-070759.jpg)

## LSM树的Compact策略

主要介绍两种基本策略：size-tiered和leveled。

重要的概念

- 读放大:读取数据时实际读取的数据量大于真正的数据量。例如在LSM树中需要先在MemTable查看当前key是否存在，不存在继续从SSTable中寻找。
- 写放大:写入数据时实际写入的数据量大于真正的数据量。例如在LSM树中写入时可能触发Compact操作，导致实际写入的数据量远大于该key的数据量。
- 空间放大:数据实际占用的磁盘空间比数据的真正大小更多。上面提到的冗余存储，对于一个key来说，只有最新的那条记录是有效的，而之前的记录都是可以被清理回收的。

### size-tiered 策略

size-tiered策略保证每层SSTable的大小相近，同时限制每一层SSTable的数量。如上图，每层限制SSTable为N，当每层SSTable达到N后，则触发Compact操作合并这些SSTable，并将合并后的结果写入到下一层成为一个更大的sstable。
![size-tiered](https://media.techwhims.com/2023-04-06-071031.jpg)

由此可以看出，当层数达到一定数量时，最底层的单个SSTable的大小会变得非常大。并且size-tiered策略会导致空间放大比较严重。即使对于同一层的SSTable，每个key的记录是可能存在多份的，只有当该层的SSTable执行compact操作才会消除这些key的冗余记录。

### leveled策略

leveled策略也是采用分层的思想，每一层限制总文件的大小。
![分层的思想](https://media.techwhims.com/2023-04-06-071056.jpg)

但是跟size-tiered策略不同的是，leveled会将每一层切分成多个大小相近的SSTable。这些SSTable是这一层是全局有序的，意味着一个key在每一层至多只有1条记录，不存在冗余记录。
![SSTable全局有序](https://media.techwhims.com/2023-04-06-071114.jpg)

leveled策略相较于size-tiered策略来说，每层内key是不会重复的，即使是最坏的情况，除开最底层外，其余层都是重复key，按照相邻层大小比例为10来算，冗余占比也很小。因此空间放大问题得到缓解。但是写放大问题会更加突出