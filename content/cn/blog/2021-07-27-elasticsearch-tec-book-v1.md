---
title: "Elasticsearch5+ 技术手册文章记录"
date: 2021-07-27T16:59:48+08:00
author: "张晓龙"
slug: elasticsearch
draft: false
keywords: 
- elasticsearch
- search
description: "介绍 elasticsearch 技术手册的文章。" 
toc: true
tag: elasticsearch
---
# elasticsearch技术手册 v1.01

## 1. 基础
本手册内容是基于`elasticsearch5+`版本。准确的说是5.0.1版本。
### 1.概念
集群（cluster）、节点（node）、索引（index）、分片（shards）、副本（replicas）；
term、tf-idf、boost等
### 2. Elasticsearch features

1. [Based in lucene, write in java]()
2. [Realtime analytics]()
3. [Full Text search engine]()
4. [Distributed, easy to scale]()
5. [High availability]()
6. [Document oriented(json)]()
7. [Schema free]()
8. [Restful API, json over http]()
9. [Open source:Apache License 6.0 (ES:5.x)]()
10. [Plugins & Community support]()

### 3. elasticsearch do what on lucene?
Elasticsearch 构建在lucene之上，提供json方式的rest api进行交互；

1. Elasticsearch在lucene之上提供一个完整的分布式系统；
2. Elasticsearch提供了一个分布式的抽象的数据结构；
3. 提供了一些特性，例如线程池、队列、node/cluster监控api、数据监控api、以及集群管理等等；

## 2. 生产环境
### 1. 监控（Monitoring）
对于已经初步部署完成的elasticsearch集群来说，接下来的集群监控就变的更重要了。集群的重要参数，比如集群状态，分片状态等是集群健康的体现。elasticsearch提供了很对的现成api供我们管理和监控cluster。
其中，(1)marvel是一个很容易监控elasticsearch的工具。它可以整合大量的统计数据通过kibana。
(2) cluster health
### 2. 生产环境部署（Production Deploying）
生产环境的部署有很多考究的地方，接下来我从以下三个方面来说。
#### 运维部署考虑（硬件以及部署策略）
（1）memory，elasticsearch是比较吃内存的，尤其像排序、聚合操作，所以保证足够的heap内存是重要的。如果对内存不够的话，会交换到系统的缓存，由于lucene的数据结构是disk-based的格式，这势必会影响搜索的性能；一般建议使用16g-64gRAM的机器。如果大于64g，则会出现[另外的一些问题](https://www.elastic.co/guide/en/elasticsearch/guide/current/heap-sizing.html)
（2）cpus,和内存相比，搜索对cpu的要求不是特别高，一般使用多核cpu就行，比如2-8核的；
（3）disk，硬盘的性能对搜索集群非常重要，磁盘的性能直接影响索引的构建和读写操作，很多时候是搜索的一个瓶颈。ssd硬盘是目前最好的方式，但是由于其价钱看看阿里云，是同样的`喜人`，所以看业务需要，力所能及吧，我们目前使用的是高性能磁盘（high-performance server disks, 15k RPM drives），可以满足业务需求。
（4）network，一个快速稳定的网络环境对分布式系统非常的重要，低延迟、高带宽有利于节点间的交互以及分片的拷贝和恢复
（5）其他，尽量避免使用小配置机器组合一个超大的集群，这样管理起来就是一个大坑
#### 优化配置参数
(1)Java Virtual Machine
(2)Transport Client Versus Node Client
vs:
Transport Client 可以解耦你的应用和搜索服务，应用可以很快的创建和销毁连接；
Node Client 可以和搜索服务保持一个持久连接，可以查看搜索的结构信息；
(3)Important Configuration Changes
elasticsearch配置文件有非常好的默认设置，都是在实际的工作环境中实践过的。当遇到性能问题的时候，更多的是需要考虑数据存储布局和添加更多的node（elasticsearch文档中特意说明了配置文件的重要性，不让随便更改，大多数情况下是正确的）。

- name

```
1. Assign Names
cluster.name: elasticsearch_production
node.name: elasticsearch_005_data

2. Paths
path.data: /path/to/data1,/path/to/data2

# Path to log files:
path.logs: /path/to/logs

# Path to where plugins are installed:
path.plugins: /path/to/plugins

```

- minimum_master_nodes，这个参数是在配置文件中比较重要的一个，如果配置不对的话，会发生split brains（俗称“脑裂”），就是说会存在多个master节点，继而可能发生丢失data现象。这个参数的计算公式：(number of master-eligible nodes / 2) + 1，举例说明：

	- 假如你有10个node（可存储数据，可成为master），则设置为6；
	- 假如你有三个可选为master的节点，100+个数据节点，则设置为2；
	- 假如你有2个常规节点，这个值设置为2，但是如果丢失一个则会造成集群不可用，如果设置为1，则不能保证脑裂的不存在，最好的方法是保证最小的节点数为3.

```
discovery.zen.minimum_master_nodes: 2
```
因为elasticsearch是自适应的，节点随时添加或者下线，不过还好，有api我们可以实时调整这个参数，

```
PUT /_cluster/settings
{
    "persistent" : {
        "discovery.zen.minimum_master_nodes" : 2
    }
}
```

- Recovery Settings
恢复策略对elasticsearch是必不可少的，举例来说，假如现在集群（10 nodes）集体下线进行维修升级，当重新启动的时候，先启动了5 nodes，此时集群发现有5个node启动了，会执行shard的备份和交换，直到达到分片平衡，此时如果另外5 nodes加入到集群中，会发生什么呢？cluster会继续rebalance，新加入的节点发现数据集群中已经有了，首先删除本地数据，通知集群发动rebalance，平衡各个shards，这整个过程中shard会发生copy、sweap、delete等操作，耗费好多资源和时间，对一个大集群来说，耗费的更多，不可忍受。所以，elasticsearch有三个参数可以配置这些。

```
gateway.recover_after_nodes: 8   // 集群中恢复的节点数，就是说当改集群启动了8个几点，才尽兴rebalance

// 这两项说明，本集群有10的node，当10个nodes都启动或者启动了8个node且超过5分钟后就会发起rebalance
gateway.expected_nodes: 10
gateway.recover_after_time: 5m
```
这些策略只和`整个cluster重启`时生效。

- Prefer Unicast over Multicast
elasticsearch建议使用单播的方式，虽然依然提供了多播的方式，但存在找不到master等尴尬的问题，不建议使用。

```
discovery.zen.ping.unicast.hosts: ["host1", "host2:port"]
```
（4）不要轻易修改的参数

1. Garbage Collector
elasticsearch中默认采用Concurrent-Mark and Sweep (CMS)的gc回收器；

2. Threadpools
elasticsearch中设置线程池非常合理的，如果没有特别情况下不要修改这个值

```
Search gets a larger threadpool, and is configured to int((# of cores * 3) / 2) + 1
```
(5)Heap: Sizing and Swapping
(6)File Descriptors and MMap
elasticsearch混合使用nioFS和MMapFS。

### 3. 插件
1. 使用[head](https://github.com/mobz/elasticsearch-head)插件来查看索引数据
2. 使用[kopf](https://github.com/lmenezes/elasticsearch-kopf)来备份集群节点
3. 使用[bigdesk](https://github.com/lukas-vlcek/bigdesk)查看集群性能
4. [elasticsearch-sql](https://github.com/NLPchina/elasticsearch-sql) 通过sql进行聚合检索, 可以将sql语句翻译成ES的JSON检索语句
5. 中文分词（ik、pinying）
6. [Curator](https://www.elastic.co/guide/en/elasticsearch/client/curator/current/about.html)

## 3. 参数配置
暂空（后补）

### java优化配置
(1)Heap不要超过系统可用内存的一半，并且不要超过32GB。

(2) cluster集群jvm调优
当时我们配置ES的JVM(Xms=Xmx=8G)的垃圾回收器主要是CMS,具体配置如下:

```
# reduce the per-thread stack size
JAVA_OPTS="$JAVA_OPTS -Xss256k"

JAVA_OPTS="$JAVA_OPTS -XX:+UseParNewGC"
JAVA_OPTS="$JAVA_OPTS -XX:+UseConcMarkSweepGC"

JAVA_OPTS="$JAVA_OPTS -XX:CMSInitiatingOccupancyFraction=75"
JAVA_OPTS="$JAVA_OPTS -XX:+UseCMSInitiatingOccupancyOnly"
```
这块在官方说明中，特意强调了不建议替换java垃圾回收器，[官方并不推荐使用G1](https://www.elastic.co/guide/en/elasticsearch/guide/current/_don_8217_t_touch_these_settings.html#_garbage_collector)。

[其他博文](https://www.geekhub.cn/a/1256.html)中有试过使用其他垃圾回收器。他的G1的具体配置如下:

```
JAVA_OPTS="$JAVA_OPTS -XX:+UseG1GC "
#init_globals()末尾打印日志
JAVA_OPTS="$JAVA_OPTS -XX:+PrintFlagsFinal "
#打印gc引用
JAVA_OPTS="$JAVA_OPTS -XX:+PrintReferenceGC "
#输出虚拟机中GC的详细情况.
JAVA_OPTS="$JAVA_OPTS -verbose:gc "
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCDetails "
#Enables printing of time stamps at every GC. By default, this option is disabled.
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCTimeStamps "
#Enables printing of information about adaptive generation sizing. By default, this option is disabled.
JAVA_OPTS="$JAVA_OPTS -XX:+PrintAdaptiveSizePolicy "
# unlocks diagnostic JVM options
JAVA_OPTS="$JAVA_OPTS -XX:+UnlockDiagnosticVMOptions "
#to measure where the time is spent
JAVA_OPTS="$JAVA_OPTS -XX:+G1SummarizeConcMark "
#设置触发标记周期的 Java 堆占用率阈值。默认占用率是整个 Java 堆的 45%。
#JAVA_OPTS="$JAVA_OPTS -XX:InitiatingHeapOccupancyPercent=45 "
```

(3) elastic 开启jmx 监控
有时候监控是必不可少的，所以在有条件的时候可以加上jmx监控

```
/usr/local/elastic/bin/elasticsearch.in.sh
JMX_PORT=9305
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.port=$JMX_PORT"
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.ssl=false"
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.authenticate=false"
JAVA_OPTS="$JAVA_OPTS -Djava.rmi.server.hostname=xx.xx.xx..xx"
```

### elasticsearch.yml
这个是最重要的配置，只有在你明白之后在修改，之后我在单独写一篇文章介绍目前elasticsearch默认参数是如何影响系统的。

目前配置包括以下几个部分：
（1）cluster
（2）节点node
（3）log／data路径
（4）内存
（5）网络
（5）发现Discovery
（6）Gateway
（7）其他变量

```
# ======================== Elasticsearch Configuration =========================
#
# NOTE: Elasticsearch comes with reasonable defaults for most settings.
#       Before you set out to tweak and tune the configuration, make sure you
#       understand what are you trying to accomplish and the consequences.
#
# The primary way of configuring a node is via this file. This template lists
# the most important settings you may want to configure for a production cluster.
#
# Please see the documentation for further information on configuration options:
# <https://www.elastic.co/guide/en/elasticsearch/reference/5.0/settings.html>
#
# ---------------------------------- Cluster -----------------------------------
#
# Use a descriptive name for your cluster:
#
cluster.name: elastic-pro
#
# ------------------------------------ Node ------------------------------------
#
# Use a descriptive name for the node:
#
node.name: node-0
#
# Add custom attributes to the node:
#
node.attr.rack: r1
#
# ----------------------------------- Paths ------------------------------------
#
# Path to directory where to store the data (separate multiple locations by comma):
#
path.data: /apps/home/worker/zhangxiaolong/data/index0
#
# Path to log files:
#
path.logs: /apps/home/worker/zhangxiaolong/data/log0
#
# ----------------------------------- Memory -----------------------------------
#
# Lock the memory on startup:
#
bootstrap.memory_lock: true
#
# Make sure that the heap size is set to about half the memory available
# on the system and that the owner of the process is allowed to use this
# limit.
#
# Elasticsearch performs poorly when the system is swapping the memory.
#
# ---------------------------------- Network -----------------------------------
#
# Set the bind address to a specific IP (IPv4 or IPv6):
#
network.host: 172.16.7.1
#
# Set a custom port for HTTP:
#
http.port: 9201
#
# For more information, see the documentation at:
# <https://www.elastic.co/guide/en/elasticsearch/reference/5.0/modules-network.html>
#
# --------------------------------- Discovery ----------------------------------
#
# Pass an initial list of hosts to perform discovery when new node is started:
#The default list of hosts is ["127.0.0.1", "[::1]"]
#
discovery.zen.ping.unicast.hosts: ["172.16.7.1:9300"]
#
# Prevent the "split brain" by configuring the majority of nodes (total number of nodes / 2 + 1):
#
discovery.zen.minimum_master_nodes: 2
#
# For more information, see the documentation at:
# <https://www.elastic.co/guide/en/elasticsearch/reference/5.0/modules-discovery-zen.html>
#
# ---------------------------------- Gateway -----------------------------------
#
# Block initial recovery after a full cluster restart until N nodes are started:
#
gateway.recover_after_nodes: 2
#
# For more information, see the documentation at:
# <https://www.elastic.co/guide/en/elasticsearch/reference/5.0/modules-gateway.html>
#
# ---------------------------------- Various -----------------------------------
#
# Require explicit names when deleting indices:
#
#action.destructive_requires_name: true
```

### 其他
（1）线程池设置成内核数，比如八核机器就设置成8，很多阻塞的操作都是Lucene来操作的，比如硬盘读写。搜索的线程设置可以设置成内核数的三倍
（2）内存交换
这个对于性能影响是致命的，可以使用命令sudo swapoff -a来暂时关闭，永久关闭需要编辑文件/etc/fstab，也可以在配置文件中添加配置bootstrap.mlockall: true，这样jvm可以锁定这些内存，避免被交换到物理存储介质
（3）其他

- 如果你不需要近实时功能，则设置index的刷新时间；
- 如果在进行一个大bulk导入，可以优先考虑设置副本数为0；
- 如果在index中的doc你没有一个自然增长的id，可以使用Elasticsearch’s 的自动id做标示，如果有自己的id，尽量设计对lucene友好的id；

## 4. Rolling Restarts & 备份数据 & 备份恢复
### Rolling Restarts
一般下线一个node（升级、维修等），elasticsearch会进行rebalance操作，如果你是真正的下线一个node，这个操作是十分正确的，但是你知道这台node会之后重新加入到cluster中，则rebalance操作不恰当了，当shard比较大或者多的时候会严重耗费系统资源。

那我们正确的操作是什么？

``` shell
1. 查看集群设置
curl -XGET http://10.10.160.129:9200/_cluster/settings

2. 如果可能的话，停止正在索引的数据；

3. 停止分片同步，阻止elasticsearch进行rebalance操作
PUT /_cluster/settings
{
    "transient" : {
        "cluster.routing.allocation.enable" : "none"
    }
}

4.关闭单个node

5.维护或者升级节点node

6.重启node，确认加入cluster

7.重新打开分片同步
PUT /_cluster/settings
{
    "transient" : {
        "cluster.routing.allocation.enable" : "all"
    }
}

8.针对需要的node重复执行3-7操作

9.到这里就重新恢复了cluster；
```

### 备份数据

``` shell
1. 先导入一些数据进行备份
curl -XPOST 'http://192.168.56.11:9200/bank/account/_bulk?pretty' --data-binary @accounts.json
curl -XPOST 'http://192.168.56.11:9200/shakespeare/_bulk?pretty' --data-binary @shakespeare.json
curl -XPOST 'http://192.168.56.11:9200/_bulk?pretty' --data-binary @logs.jsonl

2. 使用API创建一个镜像仓库
curl -XPOST http://192.168.56.11:9200/_snapshot/my_backup -d '
{
    "type": "fs",
    "settings": {
        "location": "/data/mount"
        "compress":  true
    }
}'
## 解释：
镜像仓库的名称：my_backup
镜像仓库的类型：fs。还支持curl，hdfs等。
镜像仓库的位置：/data/mount 。这个位置必须在配置文件中定义。
是否启用压缩：compres：true 表示启用压缩。

3. 备份前检查配置
必须确定备份使用的目录在配置文件中声明了，否则会爆如下错误
{
  "error": {
    "root_cause": [
      {
        "type": "repository_exception",
        "reason": "[test-bakcup] failed to create repository"
      }
    ],
    "type": "repository_exception",
    "reason": "[test-bakcup] failed to create repository",
    "caused_by": {
      "type": "creation_exception",
      "reason": "Guice creation errors:\n\n1) Error injecting constructor, RepositoryException[[test-bakcup] location [/data/mount] doesn't match any of the locations specified by path.repo because this setting is empty]\n  at org.elasticsearch.repositories.fs.FsRepository.<init>(Unknown Source)\n  while locating org.elasticsearch.repositories.fs.FsRepository\n  while locating org.elasticsearch.repositories.Repository\n\n1 error",
      "caused_by": {
        "type": "repository_exception",
        "reason": "[test-bakcup] location [/data/mount] doesn't match any of the locations specified by path.repo because this setting is empty"
      }
    }
  },
  "status": 500
}

4. 开始创建一个快照
##在后头创建一个快照
curl -XPUT  http://192.168.56.20:9200/_snapshot/my_backup/snapshot_1
##也可以在前台运行。
curl -XPUT  http://192.168.56.11:9200/_snapshot/my_backup/snapshot_1?wait_for_completion=true
##上面的参数会在my_backup仓库里创建一个snapshot_1 的快照。

5. 可以选择相应的索引进行备份
curl -XPUT  http://192.168.56.20:9200/_snapshot/my_backup/snapshot_2 -d '
{
    "indices": "bank,logstash-2015.05.18"
}'
## 解释：
创建一个snapshot_2的快照，只备份bank,logstash-2015.05.18这两个索引。

6. 查看备份状态
整个备份过程中，可以通过如下命令查看备份进度

curl -XGET http://192.168.0.1:9200/_snapshot/my_backup/snapshot_20150812/_status
主要由如下几种状态：
a. INITIALIZING 集群状态检查，检查当前集群是否可以做快照，通常这个过程会非常快
b. STARTED 正在转移数据到仓库
c. FINALIZING 数据转移完成，正在转移元信息
d. DONE　完成
e. FAILED 备份失败

7. 取消备份
curl -XDELETE http://192.168.0.1:9200/_snapshot/my_backup/snapshot_20150812

8. 获取所有快照信息。
curl -XGET http://192.168.56.20:9200/_snapshot/my_backup/_all |python -mjson.tool
##解释
查看my_backup仓库下的所有快照。

9. 手动删除快照
curl -XDELETE http://192.168.56.20:9200/_snapshot/my_backup/snapshot_2
## 解释
删除my_backup仓库下的snapshot_2的快照。

```

### 备份恢复

``` json
1. 恢复备份
curl -XPOST http://192.168.0.1:9200/_snapshot/my_backup/snapshot_20150812/_restore
同备份一样，也可以设置wait_for_completion=true等待恢复结果

curl -XPOST http://192.168.0.1:9200/_snapshot/my_backup/snapshot_20150812/_restore?wait_for_completion=true
默认情况下，是恢复所有的索引，我们也可以设置一些参数来指定恢复的索引，以及重命令恢复的索引，这样可以避免覆盖原有的数据.

curl -XPOST http://192.168.0.1:9200/_snapshot/my_backup/snapshot_20150812/_restore
{
    "indices": "index_1",
    "rename_pattern": "index_(.+)",
    "rename_replacement": "restored_index_$1"
}
上面的indices, 表示只恢复索引’index_1’
rename_pattern: 表示重命名索引以’index_’开头的索引.
rename_replacement: 表示将所有的索引重命名为’restored_index_xxx’.如index_1会被重命名为restored_index_1.

2. 查看所有索引的恢复进度
curl -XGET http://192.168.0.1:9200/_recovery/

3. 查看索引restored_index_1的恢复进度
curl -XGET http://192.168.0.1:9200/_recovery/restored_index_1

4. 取消恢复
只需要删除索引，即可取消恢复
curl -XDELETE http://192.168.0.1:9200/restored_index_1
```

## 5. 性能优化
在讲性能优化之前，首先要知道：

	过早的优化是万恶之源 Premature optimization is the root of all evil.
										                —— Donald Knuth

`优化总是发生在目前的情况下不能满足当前的需求，其他我想不出什么理由去优化它。`

`优化很多时候和业务是紧密关联的，优化业务可能比优化程序效率更高、成本更低！`

### 索引性能优化
索引性能（Index Performance），我们这样定义它，索引的速度是否提高，可以无缝的提供近实时的功能。
什么时候会发生索引慢呢？
（1）你读的慢（doc from db，file，inputstream等等）
（2）你处理的慢（中文下的分词等）
（3）你写的慢（还是老式的机械盘？！ 高性能的盘或者ssd）

还有就是针对不同场景选择的判断，如果你索引的文件非常大，数量多，那应该选择elasticsearch提供的bulk接口，在create doc速度能跟上的时候，bulk 是可以提高速度的。

### 查询性能优化
查询性能（Query Perofrmance），说起来比索引更麻烦一些，面对的场景也更多一些；

面对海量数据以及不同的集群，针对业务需求去查询往往会很慢，有什么策略可以搞定这种情况？有，那就是`routing`[Routing a Document to a Shard](https://www.elastic.co/guide/en/elasticsearch/guide/current/routing-value.html)、[_routing field](https://www.elastic.co/guide/en/elasticsearch/reference/5.1/mapping-routing-field.html).

查询策略，分别查询vs合并查询？索引越来越大，单个 shard 也很巨大，查询速度也越来越慢。这时候，是选择分索引还是更多的shards？在实践过程中，更多的 shards 会带来额外的索引压力，即 IO 压力。我们选择了分索引。比如按照每个大分类一个索引，或者主要的大城市一个索引。然后将他们进行合并查询。

索引越来越大，资源使用也越来越多。若是要进行更细的集群分配，大索引使用的资源成倍增加。有什么办法能减小索引？
根据具体业务需求，减少某些大的索引，这是一个很好的办法，这样这个集群各方面占用的资源会有一定程度的下降，当让你要说这些少的索引怎么办，这些索引可以放在单独的集群中。

## 应用性能优化 - [from youzan](http://tech.youzan.com/search-engine1/)
一、使用应用级队列防止雪崩
ES一个问题是在高峰期时候极容易发生雪崩. ES有健全的线程池系统来保证并发与稳定性问题. 但是在流量突变的情况下(比如双十一秒杀)还是很容易发生瘫痪的现象, 主要的原因如下:

ES几乎为每类操作配置一个线程池; 只能保证每个线程池的资源使用时合理的, 当2个以上的线程池竞争资源时容易造成资源响应不过来.

ES没有考虑网络负载导致稳定的问题.

在AS里我们实现了面向请求的全局队列来保证稳定性. 它主要做了3件事情.
![](http://image.bfstack.com/mweb/14979525149331.png!medium)

1. 根据业务把请求分成一个个slide, 每个slide对应一个队列. 默认一个应用就是一个slide, 一个应用也可以区分不同的slide, 这样可以保护一个应用内重要的查询.
2. 每个队列配置一个队列长度, 默认为50.
3. 每个队列计算这个队列的平均响应时间. 当队列平均响应时间超过200ms, 停止工作1s, 如果请求溢出就写入溢出日志留数据恢复使用. 如果连续10次队列平均响应时间超过500ms就报警, 以便工程师第一时间处理.

二、自动降级
应用级队列解决雪崩问题有点粗暴, 如果一个应用本身查询就非常慢, 很容易让一个应用持续超时很久. 我们根据搜索引擎的特点编写了自动降级功能.

比如商品搜索的例子, 商品搜索最基本的功能是布尔查询, 但是还需要按照相关性分数和质量度排序等功能, 甚至还有个性化需求. 完成简单的布尔查询, ES使用bitsets操作就可以做到, 但是如果如果需要相关性分, 就必须使用倒排索引, 并有大量CPU消耗来计算分数. ES的bitsets比倒排索引快50倍左右.

对于有降级方案的slide, AS在队列响应过慢时候直接使用降级query代替正常query. 这种方法让我们在不扩容的情况下成功度过了双十一的流量陡增.

三、善用filtered query
理解lucence filter工作原理对于写出高性能查询语句至关重要. 许多搜索性能优化都和filter的使用有关. filter使用bitsets进行布尔运算, quey使用倒排索引进行计算, 这是filter比query快的原因. bitsets的优势主要体现在:

1. bitsetcache在内存里面, 永不消失(除非被LRU).
2. bitsets利用CPU原生支持的位运算操作, 比倒排索引快个数量级
3. 多个bitsets的与运算也是非常的快(一个64位CPU可以同时计算64个DOC的与运算)
4. bitsets 在内存的存储是独立于query的, 有很强的复用性
5. 如果一个bitset片段全是0, 计算会自动跳过这些片段, 让bitsets在数据稀疏情况下同样表现优于倒排索引.

举个例子:
``` java
query:bool:
    tag:'mac'
    region:'beijing'
    title: "apple"
```

lucence处理这个query的方式是在倒排索引中寻找这三个term的倒排链 ,并使用跳指针技术求交, 在运算过程中需要对每个doc进行算分. 实际上tag和region对于算分并没有作用, 他们充当是过滤器的作用.

这就是过滤器使用场景, 它只存储存在和不存在两种状态. 如果我们把tag和region使用bitsets进行存储, 这样这两个过滤器可以一直都被缓存在内存里面, 这样会快很多. 另外tag和region之间的求交非常迅速, 因为64位机器可以时间一个CPU周期同时处理64个doc的位运算.

一个lucence金科玉律是: 能用filter就用filter, 除非必须使用query(当且仅当你需要算分的时候).
正确的写法为:

``` java
query:
    filtered:
        query:
             title: "apple"
         filter:
            tag:"mac"
             region:"beijing"
```
四、其他

1. 线上集群关闭分片自动均衡. 分片的自动均衡主要目的防止更新造成各个分片数据分布不均匀. 但是如果线上一个节点挂掉后, 很容易触发自动均衡, 一时间集群内部的数据移动占用所有带宽. 建议采用闲时定时均衡策略来保证数据的均匀.

2. 尽可能延长refresh时间间隔. 为了确保实时索引es索引刷新时间间隔默认为1秒, 索引刷新会导致查询性能受影响, 在确保业务时效性保证的基础上可以适当延长refresh时间间隔保证查询的性能.

3. 除非有必要把all字段去掉. 索引默认除了索引每个字段外, 还有额外创建一个all的字段, 保存所有文本, 去掉这个字段可以把索引大小降低50%.

4. 创建索引时候, 尽可能把查询比较慢的索引和快的索引物理分离.

##6. 参考（Reference）
1. [elastic调优参考](http://www.cnblogs.com/guguli/p/5218297.html)
2. [elastic监控](https://github.com/Wprosdocimo/Elasticsearch-zabbix)
3. [Mastering Elasticsearch(中文版)](http://udn.yyuap.com/doc/mastering-elasticsearch/chapter-4/41_README.html)
4. [ELK-权威指南](http://kibana.logstash.es/content/logstash/plugins/input/file.html)
5. [Elasticsearch 权威指南](http://www.learnes.net/index.html)
6. [elasticsearch 生产环境配置](http://www.biglittleant.cn/2016/12/01/elastic-study1/)
7. [有赞搜索引擎实践(工程篇)](http://tech.youzan.com/search-engine1/)


**[更新于2017-05-22 - v1.0 ]
[更新于2017-09-26 - v1.01]**

(完)
