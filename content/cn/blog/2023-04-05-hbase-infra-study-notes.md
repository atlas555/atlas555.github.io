---
title: "《Hbase原理和实践》学习摘要"
date: 2023-04-05
author: "张晓龙"
slug: hbase-theory-practice
draft: false
toc: true
keywords:
- Hbase
- 学习笔记
description : "介绍Hbase原理和实践，以及核心摘要"
categories: bigdata
tags: 
- data-infra
- hbase
---

记录于 2023.02.13

## 一、基本情况和原理

### 1、HBase使用现状

（1）使用HBase存储海量数据，服务于各种在线系统以及离线分析系统，业务场景包括订单系统、消息存储系统、用户画像、搜索推荐、安全风控以及物联网时序数据存储等。最近，阿里云、华为云等云提供商先后推出了HBase云服务，为国内更多公司低门槛地使用HBase服务提供了便利。

（2）系统特性：

容量巨大：HBase的单表可以支持千亿行、百万列的数据规模，数据容量可以达到TB甚至PB级别
良好的可扩展性：HBase集群可以非常方便地实现集群容量扩展，主要包括数据存储节点扩展以及读写服务节点扩展
稀疏性：HBase支持大量稀疏存储，即允许大量列值为空，并不占用任何存储空间。
高性能：HBase目前主要擅长于OLTP场景，数据写操作性能强劲，对于随机单点读以及小范围的扫描读，其性能也能够得到保证
多版本：HBase支持多版本特性，即一个KV可以同时保留多个版本
支持过期：HBase支持TTL过期特性，用户只需要设置过期时间，超过TTL的数据就会被自动清理，不需要用户写程序手动删除。
缺陷

HBase本身不支持很复杂的聚合运算（如Join、GroupBy等）。如果业务中需要使用聚合运算，可以在HBase之上架设Phoenix组件或者Spark组件，前者主要应用于小规模聚合的OLTP场景，后者应用于大规模聚合的OLAP场景
HBase本身并没有实现二级索引功能，所以不支持二级索引查找。好在针对HBase实现的第三方二级索引方案非常丰富，比如目前比较普遍的使用Phoenix提供的二级索引功能
HBase原生不支持全局跨行事务，只支持单行事务模型

### 2、HBase数据模型

称HBase为“sparse, distributed, persistent multidimensional sorted map”，即HBase本质来看是一个Map，从逻辑视图来看，HBase中的数据是以表形式进行组织的，HBase中的表也由行和列构成。从物理视图来看，HBase是一个Map，由键值（KeyValue，KV）构成，不过与普通的Map不同，HBase是一个稀疏的、分布式的、多维排序的Map。

（1）逻辑视图，HBase中的基本概念。

table：表，一个表包含多行数据。
row：行，一行数据包含一个唯一标识rowkey、多个column以及对应的值。在HBase中，一张表中所有row都按照rowkey的字典序由小到大排序。
column：列，与关系型数据库中的列不同，HBase中的column由column family（列簇）以及qualifier（列名）两部分组成，两者中间使用":"相连。比如contents:html，其中contents为列簇，html为列簇下具体的一列。column family在表创建的时候需要指定，用户不能随意增减。一个column family下可以设置任意多个qualifier，因此可以理解为HBase中的列可以动态增加，理论上甚至可以扩展到上百万列。
timestamp：时间戳，每个cell在写入HBase的时候都会默认分配一个时间戳作为该cell的版本，当然，用户也可以在写入的时候自带时间戳。HBase支持多版本特性，即同一rowkey、column下可以有多个value存在，这些value使用timestamp作为版本号，版本越大，表示数据越新。

下图所示，表中主要存储网页信息。
示例表中包含两行数据，两个rowkey分别为com.cnn.www和com.example.www，按照字典序由小到大排列。
每行数据有三个列簇，分别为anchor、contents以及people，其中列簇anchor下有两列，分别为cnnsi.com以及my.look.ca，其他两个列簇都仅有一列。

可以看出，根据行com.cnn.www以及列anchor:cnnsi.com可以定位到数据CNN，对应的时间戳信息是t9。而同一行的另一列contents:html下却有三个版本的数据，版本号分别为t5、t6和t7。

（2）多维稀疏排序Map

HBase中Map的key是一个复合键，由rowkey、column family、qualifier、type以及timestamp组成，value即为cell的值。

{"com.cnn.www","anchor","cnnsi.com","put","t9"} -> "CNN"
多维：这个特性比较容易理解。HBase中的Map与普通Map最大的不同在于，key是一个复合数据结构，由多维元素构成，包括rowkey、column family、qualif ier、type以及timestamp。
稀疏：稀疏性是HBase一个突出特点。从图1-3逻辑表中行"com.example.www"可以看出，整整一行仅有一列（people:author）有值，其他列都为空值。在其他数据库中，对于空值的处理一般都会填充null，而对于HBase，空值不需要任何填充。这个特性为什么重要？因为HBase的列在理论上是允许无限扩展的，对于成百万列的表来说，通常都会存在大量的空值，如果使用填充null的策略，势必会造成大量空间的浪费。因此稀疏性是HBase的列可以无限扩展的一个重要条件。
排序：构成HBase的KV在同一个文件中都是有序的，但规则并不是仅仅按照rowkey排序，而是按照KV中的key进行排序——先比较rowkey，rowkey小的排在前面；如果rowkey相同，再比较column，即column family:qualif ier，column小的排在前面；如果column还相同，再比较时间戳timestamp，即版本信息，timestamp大的排在前面。这样的多维元素排序规则对于提升HBase的读取性能至关重要，在后面读取章节会详细分析。
分布式：很容易理解，构成HBase的所有Map并不集中在某台机器上，而是分布在整个集群中。
（3）物理视图

HBase中的数据是按照列簇存储的，即将数据按照列簇分别存储在不同的目录中。

列簇anchor的所有数据存储在一起形成：

（4）行式存储、列式存储、列簇式存储

行式存储：行式存储系统会将一行数据存储在一起，一行数据写完之后再接着写下一行，最典型的如MySQL这类关系型数据库。行式存储在获取一行数据时是很高效的，但是如果某个查询只需要读取表中指定列对应的数据，那么行式存储会先取出一行行数据，再在每一行数据中截取待查找目标列。这种处理方式在查找过程中引入了大量无用列信息，从而导致大量内存占用。

列式存储：列式存储理论上会将一列数据存储在一起，不同列的数据分别集中存储，最典型的如Kudu、Parquet on HDFS等系统（文件格式），列式存储对于只查找某些列数据的请求非常高效，只需要连续读出所有待查目标列，然后遍历处理即可；但是反过来，列式存储对于获取一行的请求就不那么高效了，需要多次IO读多个列数据，最终合并得到一行数据。另外，因为同一列的数据通常都具有相同的数据类型，因此列式存储具有天然的高压缩特性。

列簇式存储：从概念上来说，列簇式存储介于行式存储和列式存储之间，可以通过不同的设计思路在行式存储和列式存储两者之间相互切换

### 3、HBase体系结构

典型的Master-Slave模型。系统中有一个管理集群的Master节点以及大量实际服务用户读写的RegionServer节点。除此之外，HBase中所有数据最终都存储在HDFS系统中；系统中还有一个ZooKeeper节点，协助Master对集群进行管理

（1）hbase client：HBase客户端（Client）提供了Shell命令行接口、原生Java API编程接口、Thrift/REST API编程接口以及MapReduce编程接口。HBase客户端支持所有常见的DML操作以及DDL操作。HBase客户端访问数据行之前，首先需要通过元数据表定位目标数据所在RegionServer，之后才会发送请求到该RegionServer。同时这些元数据会被缓存在客户端本地，以方便之后的请求访问。如果集群RegionServer发生宕机或者执行了负载均衡等，从而导致数据分片发生迁移，客户端需要重新请求最新的元数据并缓存在本地。

（2）zookeeper：在HBase系统中，ZooKeeper扮演着非常重要的角色。

实现Master高可用：通常情况下系统中只有一个Master工作，一旦Active Master由于异常宕机，ZooKeeper会检测到该宕机事件，并通过一定机制选举出新的Master，保证系统正常运转。
管理系统核心元数据：比如，管理当前系统中正常工作的RegionServer集合，保存系统元数据表hbase:meta所在的RegionServer地址等。
参与RegionServer宕机恢复：ZooKeeper通过心跳可以感知到RegionServer是否宕机，并在宕机后通知Master进行宕机处理。
实现分布式表锁：HBase中对一张表进行各种管理操作（比如alter操作）需要先加表锁，防止其他用户对同一张表进行管理操作，造成表状态不一致。HBase中的表通常都是分布式存储，ZooKeeper可以通过特定机制实现分布式表锁。
（3）Master：Master主要负责HBase系统的各种管理工作：

处理用户的各种管理请求，包括建表、修改表、权限操作、切分表、合并数据分片以及Compaction等。
管理集群中所有RegionServer，包括RegionServer中Region的负载均衡、RegionServer的宕机恢复以及Region的迁移等。
清理过期日志以及文件，Master会每隔一段时间检查HDFS中HLog是否过期、HFile是否已经被删除，并在过期之后将其删除。
（4）RegionServer，RegionServer主要用来响应用户的IO请求，是HBase中最核心的模块，由WAL(HLog)、BlockCache以及多个Region构成。

WAL(HLog)：HLog在HBase中有两个核心作用——其一，用于实现数据的高可靠性，HBase数据随机写入时，并非直接写入HFile数据文件，而是先写入缓存，再异步刷新落盘。为了防止缓存数据丢失，数据写入缓存之前需要首先顺序写入HLog，这样，即使缓存数据丢失，仍然可以通过HLog日志恢复；其二，用于实现HBase集群间主从复制，通过回放主集群推送过来的HLog日志实现主从复制。
BlockCache：HBase系统中的读缓存。客户端从磁盘读取数据之后通常会将数据缓存到系统内存中，后续访问同一行数据可以直接从内存中获取而不需要访问磁盘。
带有大量热点读的业务请求来说，缓存机制会带来极大的性能提升。

BlockCache缓存对象是一系列Block块，一个Block默认为64K，由物理上相邻的多个KV数据组成。BlockCache同时利用了空间局部性和时间局部性原理，前者表示最近将读取的KV数据很可能与当前读取到的KV数据在地址上是邻近的，缓存单位是Block（块）而不是单个KV就可以实现空间局部性；后者表示一个KV数据正在被访问，那么近期它还可能再次被访问。

当前BlockCache主要有两种实现——LRUBlockCache和BucketCache，前者实现相对简单，而后者在GC优化方面有明显的提升。

Region：数据表的一个分片，当数据表大小超过一定阈值就会“水平切分”，分裂为两个Region。Region是集群负载均衡的基本单位。通常一张表的Region会分布在整个集群的多台RegionServer上，一个RegionServer上会管理多个Region，当然，这些Region一般来自不同的数据表。

一个Region由一个或者多个Store构成，Store的个数取决于表中列簇（column family）的个数，多少个列簇就有多少个Store。HBase中，每个列簇的数据都集中存放在一起形成一个存储单元Store，因此建议将具有相同IO特性的数据设置在同一个列簇中。

每个Store由一个MemStore和一个或多个HFile组成。MemStore称为写缓存，用户写入数据时首先会写到MemStore，当MemStore写满之后（缓存数据超过阈值，默认128M）系统会异步地将数据f lush成一个HFile文件。显然，随着数据不断写入，HFile文件会越来越多，当HFile文件数超过一定阈值之后系统将会执行Compact操作，将这些小文件通过一定策略合并成一个或多个大文件。

（5）HDFS：HBase底层依赖HDFS组件存储实际数据，包括用户数据文件、HLog日志文件等最终都会写入HDFS落盘

## 二、基础数据结构

HBase的一个列簇（Column Family）本质上就是一棵LSM树（Log-Structured Merge-Tree）。

LSM树分为内存部分和磁盘部分。

内存部分是一个维护有序数据集合的数据结构。一般来讲，内存数据结构可以选择平衡二叉树、红黑树、跳跃表（SkipList）等维护有序集的数据结构，这里由于考虑并发性能，HBase选择了表现更优秀的跳跃表。

磁盘部分是由一个个独立的文件组成，每一个文件又是由一个个数据块组成。对于数据存储在磁盘上的数据库系统来说，磁盘寻道以及数据读取都是非常耗时的操作（简称IO耗时）。为了避免不必要的IO耗时，可以在磁盘中存储一些额外的二进制数据，这些数据用来判断对于给定的key是否有可能存储在这个数据块中，这个数据结构称为布隆过滤器（Bloom Filter）

### 1、跳跃表

跳跃表（SkipList）是一种能高效实现插入、删除、查找的内存数据结构，期望复杂度都是O(logN)，在并发场景下加锁粒度更小，从而可以实现更高的并发性

跳跃表由多条分层的链表组成（设为S0, S1, S2, ... , Sn），例如图中有6条链表。
每条链表中的元素都是有序的。
每条链表都有两个元素：+∞（正无穷大）和- ∞（负无穷大），分别表示链表的头部和尾部。
从上到下，上层链表元素集合是下层链表元素集合的子集，即S1是S0的子集，S2是S1的子集。
跳跃表的高度定义为水平链表的层数
操作：增删改

时间复杂度 ：

1、性质1一个节点落在第k层的概率为pk-1。

2、性质2一个最底层链表有n个元素的跳跃表，总共元素个数为[插图]，其中k为跳跃表的高度。  – – O(n)

3、性质3跳跃表的高度为O(logn)。  — O(logn)

4、性质4跳跃表的查询时间复杂度为O(logN)。高度k为O(logN)级别，所以，查询走过的期望步数也为O(logN)

5、性质5跳跃表的插入/删除时间复杂度为O(logN)。

### 2、LSM 树

LSM树的索引对写入请求更友好。因为无论是何种写入请求，LSM树都会将写入操作处理为一次顺序写，而HDFS擅长的正是顺序写（且HDFS不支持随机写），因此基于HDFS实现的HBase采用LSM树作为索引是一种很合适的选择。

LSM树的索引一般由两部分组成，一部分是内存部分，一部分是磁盘部分。内存部分一般采用跳跃表来维护一个有序的KeyValue集合。磁盘部分一般由多个内部KeyValue有序的文件组成。

KeyValue存储格式：

keyLen：占用4字节，用来存储KeyValue结结构中Key所占用的字节长度。
valueLen：占用4字节，用来存储KeyValue结构中Value所占用的字节长度。
rowkeyLen：占用2字节，用来存储rowkey占用的字节长度。
rowkeyBytes：占用rowkeyLen个字节，用来存储rowkey的二进制内容。
familyLen：占用1字节，用来存储Family占用的字节长度。
familyBytes：占用familyLen字节，用来存储Family的二进制内容。
qualif ierBytes：占用qualif ierLen个字节，用来存储Qualif ier的二进制内容。注意，HBase并没有单独分配字节用来存储qualif ierLen，因为可以通过keyLen和其他字段的长度计算出qualif ierLen。
timestamp：占用8字节，表示timestamp对应的long值。
type：占用1字节，表示这个KeyValue操作的类型，HBase内有Put、Delete、Delete Column、DeleteFamily，等等。注意，这是一个非常关键的字段，表明了LSM树内存储的不只是数据，而是每一次操作记录
通常来说，在LSM树的KeyValue中的Key部分，有3个字段必不可少：

Key的二进制内容。
一个表示版本号的64位long值，在HBase中对应timestamp；这个版本号通常表示数据的写入先后顺序，版本号越大的数据，越优先被用户读取。甚至会设计一定的策略，将那些版本号较小的数据过期淘汰（HBase中有TTL策略）。
type，表示这个KeyValue是Put操作，还是Delete操作，或者是其他写入操作。本质上，LSM树中存放的并非数据本身，而是操作记录。这对应了LSM树（Log-Structured Merge-Tree）中Log的含义，即操作日志。

LSM树的索引结构

一个LSM树的索引主要由两部分构成：内存部分和磁盘部分。内存部分是一个ConcurrentSkipListMap，Key就是前面所说的Key部分，Value是一个字节数组。数据写入时，直接写入MemStore中。

LSM树索引结构如图2-8所示。内存部分导出形成一个有序数据文件的过程称为flush。为了避免flush影响写入性能，会先把当前写入的MemStore设为Snapshot，不再容许新的写入操作写入这个Snapshot的MemStore。另开一个内存空间作为MemStore，让后面的数据写入。一旦Snapshot的MemStore写入完毕，对应内存空间就可以释放。这样，就可以通过两个MemStore来实现稳定的写入性能（和 hadoop 写入数据同样的策略）。

旦用户有读取请求，则需要将大量的磁盘文件进行多路归并，之后才能读取到所需的数据。因为需要将那些Key相同的数据全局综合起来，最终选择出合适的版本返回给用户，所以磁盘文件数量越多，在读取的时候随机读取的次数也会越多，从而影响读取操作的性能。

为了优化读取操作的性能，我们可以设置一定策略将选中的多个hf ile进行多路归并，合并成一个文件。文件个数越少，则读取数据时需要seek操作的次数越少，读取性能则越好。

按照选中的文件个数，我们将compact操作分成两种类型。一种是major compact，是将所有的hf ile一次性多路归并成一个文件
一种是minor compact，即选中少数几个hf ile，将它们多路归并成一个文件。这种方式的优点是，可以进行局部的compact，通过少量的IO减少文件个数，提升读取操作的性能，适合较高频率地跑；
总结：LSM树的索引结构本质是将写入操作全部转化成磁盘的顺序写入，极大地提高了写入操作的性能。但是，这种设计对读取操作是非常不利的，因为需要在读取的过程中，通过归并所有文件来读取所对应的KV，这是非常消耗IO资源的。因此，在HBase中设计了异步的compaction来降低文件个数，达到提高读取性能的目的。由于HDFS只支持文件的顺序写，不支持文件的随机写，而且HDFS擅长的场景是大文件存储而非小文件，所以上层HBase选择LSM树这种索引结构是最合适的

### 3、布隆过滤器 bloomfilter

1、HBase的Get操作就是通过运用低成本高效率的布隆过滤器来过滤大量无效数据块的，从而节省大量磁盘IO。

2、在HBASE-20636中，腾讯团队介绍了一种很神奇的设计。他们的游戏业务rowkey是这样设计的：

也就是用userid和其他字段拼接生成rowkey。而且业务大部分的请求都按照某个指定用户的userid来扫描这个用户下的所有数据，即按照userid来做前缀扫描。基于这个请求特点，可以把rowkey中固定长度的前缀计算布隆过滤器，这样按照userid来前缀扫描时（前缀固定，所以计算布隆过滤器的Key值也就固定），同样可以借助布隆过滤器优化性能，HBASE-20636中提到有一倍以上的性能提升。另外，对于Get请求，同样可以借助这种前缀布隆过滤器提升性能。因此，这种设计对Get和基于前缀扫描的Scan都非常友好。

## 三、hbase 的依赖 和 hbase client 操作

### 1、zk

看看HBase在ZooKeeper上都存储了哪些信息

meta-region-server：存储HBase集群hbase:meta元数据表所在的RegionServer访问地址。客户端读写数据首先会从此节点读取hbase:meta元数据的访问地址，将部分元数据加载到本地，根据元数据进行数据路由。
master/backup-masters：通常来说生产线环境要求所有组件节点都避免单点服务，HBase使用ZooKeeper的相关特性实现了Master的高可用功能。其中Master节点是集群中对外服务的管理服务器，backup-masters下的子节点是集群中的备份节点，一旦对外服务的主Master节点发生了异常，备Master节点可以通过选举切换成主Master，继续对外服务。需要注意的是备Master节点可以是一个，也可以是多个。
table：集群中所有表信息。
region-in-transition：在当前HBase系统实现中，迁移Region是一个非常复杂的过程。首先对这个Region执行unassign操作，将此Region从open状态变为off line状态（中间涉及PENDING_CLOSE、CLOSING以及CLOSED等过渡状态），再在目标RegionServer上执行assign操作，将此Region从off line状态变成open状态。这个过程需要在Master上记录此Region的各个状态。目前，RegionServer将这些状态通知给Master是通过ZooKeeper实现的，RegionServer会在region-in-transition中变更Region的状态，Master监听ZooKeeper对应节点，以便在Region状态发生变更之后立马获得通知，得到通知后Master再去更新Region在hbase:meta中的状态和在内存中的状态。
table-lock：HBase系统使用ZooKeeper相关机制实现分布式锁。HBase中一张表的数据会以Region的形式存在于多个RegionServer上，因此对一张表的DDL操作（创建、删除、更新等操作）通常都是典型的分布式操作。每次执行DDL操作之前都需要首先获取相应表的表锁，防止多个DDL操作之间出现冲突，这个表锁就是分布式锁。分布式锁可以使用ZooKeeper的相关特性来实现，在此不再赘述。
online-snapshot：用来实现在线snapshot操作。表级别在线snapshot同样是一个分布式操作，需要对目标表的每个Region都执行snapshot，全部成功之后才能返回成功。Master作为控制节点给各个相关RegionServer下达snapshot命令，对应RegionServer对目标Region执行snapshot，成功后通知Master。Master下达snapshot命令、RegionServer反馈snapshot结果都是通过ZooKeeper完成的。
replication：用来实现HBase复制功能。
splitWAL/recovering-regions：用来实现HBase分布式故障恢复。为了加速集群故障恢复，HBase实现了分布式故障恢复，让集群中所有RegionServer都参与未回放日志切分。ZooKeeper是Master和RegionServer之间的协调节点。
rs：集群中所有运行的RegionServer。

### 2、HDFS

1、擅长的场景是大文件（一般认为字节数超过数十MB的文件为大文件）的顺序读、随机读和顺序写。从API层面，HDFS并不支持文件的随机写（Seek+Write）以及多个客户端同时写同一个文件

2、一个线上的高可用HDFS集群主要由4个重要的服务组成：NameNode、DataNode、JournalNode、ZkFailoverController。

namenode:NameNode存储并管理HDFS的文件元数据，这些元数据主要包括文件属性（文件大小、文件拥有者、组以及各个用户的文件访问权限等）以及文件的多个数据块分布在哪些存储节点上。需要注意的是，文件元数据是在不断更新的，因此NameNode本质上是一个独立的维护所有文件元数据的高可用KV数据库系统。为了保证每一次文件元数据都不丢失，NameNode采用写EditLog和FsImage的方式来保证元数据的高效持久化。每一次文件元数据的写入，都是先做一次EditLog的顺序写，然后再修改NameNode的内存状态。同时NameNode会有一个内部线程，周期性地把内存状态导出到本地磁盘持久化成FsImage（假设导出FsImage的时间点为t），那么对于小于时间点t的EditLog都认为是过期状态，是可以清理的，这个过程叫做推进checkpoint。
JournalNode，为了保证两个NameNode在切换前后能读到一致的EditLog，HDFS单独实现了一个叫做JournalNode的服务。线上集群一般部署奇数个JournalNode（一般是3个，或者5个），在这些JournalNode内部，通过Paxos协议来保证数据一致性。因此可以认为，JournalNode其实就是用来维护EditLog一致性的Paxos组。
ZKFailoverController主要用来实现NameNode的自动切换。
locality和短路读对HBase的读性能影响重大。在locality=1.0情况下，不开短路读的p99性能要比开短路读差10%左右。如果用locality=0和locality=1相比，读操作性能则差距巨大。

### 3、HDFS在HBase系统中扮演的角色

HBase使用HDFS存储所有数据文件，从HDFS的视角看，HBase就是它的客户端。这样的架构有几点需要说明：

HBase本身并不存储文件，它只规定文件格式以及文件内容，实际文件存储由HDFS实现。•
HBase不提供机制保证存储数据的高可靠，数据的高可靠性由HDFS的多副本机制保证。•
HBase-HDFS体系是典型的计算存储分离架构。这种轻耦合架构的好处是，一方面可以非常方便地使用其他存储替代HDFS作为HBase的存储方案；另一方面对于云上服务来说，计算资源和存储资源可以独立扩容缩容，给云上用户带来了极大的便利。
3、hbase 在 hdfs 的文件类型和内容
在机器上执行 hdfs -ls /hbase

参数说明如下：

.hbase-snapshot：snapshot文件存储目录。用户执行snapshot后，相关的snapshot元数据文件存储在该目录。•
.tmp：临时文件目录，主要用于HBase表的创建和删除操作。表创建的时候首先会在tmp目录下执行，执行成功后再将tmp目录下的表信息移动到实际表目录下。表删除操作会将表目录移动到tmp目录下，一定时间过后再将tmp目录下的文件真正删除。•
MasterProcWALs：存储Master Procedure过程中的WAL文件。Master Procedure功能主要用于可恢复的分布式DDL操作。在早期HBase版本中，分布式DDL操作一旦在执行到中间某个状态发生宕机等异常的情况时是没有办法回滚的，这会导致集群元数据不一致。Master Procedure功能使用WAL记录DDL执行的中间状态，在异常发生之后可以通过WAL回放明确定位到中间状态点，继续执行后续操作以保证整个DDL操作的完整性。•
WALs：存储集群中所有RegionServer的HLog日志文件。•
archive：文件归档目录。这个目录主要会在以下几个场景下使用。
所有对HFile文件的删除操作都会将待删除文件临时放在该目录。○
进行Snapshot或者升级时使用到的归档目录。○
Compaction删除HFile的时候，也会把旧的HFile移动到这里。•
corrupt：存储损坏的HLog文件或者HFile文件。•
data：存储集群中所有Region的HFile数据。HFile文件在data目录下的完整路径如下所示

.tabledesc：表描述文件，记录对应表的基本schema信息。○
.tmp：表临时目录，主要用来存储Flush和Compaction过程中的中间结果。以flush为例，MemStore中的KV数据落盘形成HFile首先会生成在.tmp目录下，一旦完成再从.tmp目录移动到对应的实际文件目录。○
.regioninfo：Region描述文件。○
recovered.edits：存储故障恢复时该Region需要回放的WAL日志数据。RegionServer宕机之后，该节点上还没有来得及flush到磁盘的数据需要通过WAL回放恢复，WAL文件首先需要按照Region进行切分，每个Region拥有对应的WAL数据片段，回放时只需要回放自己的WAL数据片段即可。
• hbase.id：集群启动初始化的时候，创建的集群唯一id。
hbase.version：HBase软件版本文件，代码静态版本。•
oldWALs：WAL归档目录。一旦一个WAL文件中记录的所有KV数据确认已经从MemStore持久化到HFile，那么该WAL文件就会被移到该目录。
3、Base系统内部设计了一张特殊的表——hbase:meta表
专门用来存放整个集群所有的Region信息。hbase:meta中的hbase指的是namespace，HBase容许针对不同的业务设计不同的namespace，系统表采用统一的namespace，即hbase；meta指的是hbase这个namespace下的表名。

### 4、hbase:meta表内具体存放的是哪些信息呢？

hbase:meta的一个rowkey就对应一个Region，rowkey主要由TableName（业务表名）、StartRow（业务表Region区间的起始rowkey）、Timestamp（Region创建的时间戳）、EncodedName（上面3个字段的MD5 Hex值）4个字段拼接而成。每一行数据又分为4列，分别是info:regioninfo、info:seqnumDuringOpen、info:server、info:serverstartcode。

• info:regioninfo：该列对应的Value主要存储4个信息，即EncodedName、RegionName、Region的StartRow、Region的StopRow。•
info:seqnumDuringOpen：该列对应的Value主要存储Region打开时的sequenceId。•
info:server：该列对应的Value主要存储Region落在哪个RegionServer上。•
info:serverstartcode：该列对应的Value主要存储所在RegionServer的启动Timestamp。

HBase作为一个分布式数据库系统，一个大的集群可能承担数千万的查询写入请求，而hbase:meta表只有一个Region，如果所有的流量都先请求hbase:meta表找到Region，再请求Region所在的RegionServer，那么hbase:meta表的将承载巨大的压力，这个Region将马上成为热点Region，且根本无法承担数千万的流量。

解决思路很简单：把hbase:meta表的Region信息缓存在HBase客户端

HBase客户端有一个叫做MetaCache的缓存，在调用HBase API时，客户端会先去MetaCache中找到业务rowkey所在的Region，

•Region信息为空，说明MetaCache中没有这个rowkey所在Region的任何Cache。此时直接用上述查询语句去hbase:meta表中Reversed Scan即可

•Region信息不为空，但是调用RPC请求对应RegionServer后发现Region并不在这个RegionServer上。这说明MetaCache信息过期了，同样直接Reversed Scan hbase:meta表，找到正确的Region并缓存。通常，某些Region在两个RegionServer之间移动后会发生这种情况。但事实上，无论是RegionServer宕机导致Region移动，还是由于Balance导致Region移动，发生的几率都极小。而且，也只会对Region移动后的极少数请求产生影响，这些请求只需要通过HBase客户端自动重试locate meta即可成功。
•Region信息不为空，且调用RPC请求到对应RegionSsrver后，发现是正确的RegionServer。绝大部分的请求都属于这种情况

### 5、HBase客户端的Scan操作应该是比较复杂的RPC操作

1、Scan必须能设置众多维度的属性。常用的有startRow、endRow、Filter、caching、batch、reversed、maxResultSize、version、timeRange。

2、用户每次执行scanner.next()，都会尝试去名为cache的队列中拿result（步骤4）。如果cache队列已经为空，则会发起一次RPC向服务端请求当前scanner的后续result数据（步骤1）。客户端收到result列表之后（步骤2），通过scanResultCache把这些results内的多个cell进行重组，最终组成用户需要的result放入到Cache中（步骤3）。其中，步骤1+步骤2+步骤3统称为loadCache操作。

理解Scan的几个重要的概念。

• caching：每次loadCache操作最多放caching个result到cache队列中。控制caching，也就能控制每次loadCache向服务端请求的数据量，避免出现某一次scanner.next()操作耗时极长的情况。
• batch：用户拿到的result中最多含有一行数据中的batch个cell。如果某一行有5个cell，Scan设的batch为2，那么用户会拿到3个result，每个result中cell个数依次为2，2，1。•
allowPartial：用户能容忍拿到一行部分cell的result。设置了这个属性，将跳过图4-3中的第三步重组流程，直接把服务端收到的result返回给用户。•
maxResultSize：loadCache时单次RPC操作最多拿到maxResultSize字节的结果集。

### 6、hbase client 访问的坑

1、RPC 重试机制设置
几种导致重试的常见异常：•

待访问Region所在的RegionServer发生宕机，此时Region已经被移到一个新的RegionServer上，但由于客户端存在meta缓存，首次RPC请求仍然访问到了旧的RegionServer。后续将重试发起RPC。•
服务端负载较大，导致单次RPC响应超时。客户端后续将继续重试，直到RPC成功或者超过客户容忍最大延迟。•
访问meta表或者ZooKeeper异常。
假设某业务要求单次HBase的读请求延迟不超过1s，那么该如何设置上述4个超时，

答案：首先，hbase.client.operation.timeout应该设成1s。其次，在SSD集群上，如果集群参数设置合适且集群服务正常，则基本可以保证p99延迟在100ms以内，因此hbase.rpc. timeout设成100ms。这里，hbase.client.pause用默认的100ms。最后，在1s之内，第一次RPC耗时100ms，休眠100ms；第二次RPC耗时100ms，休眠200ms；第三次RPC耗时100ms，休眠300ms；第四次RPC耗时100ms，休眠500ms（不是完全线性递增的）。因此，在hbase.client.operation.timeout内，至少可执行4次RPC重试，

2、cas 接口是 region 串行执行的，吞吐受限
这些CAS接口在RegionServer上是Region级别串行执行的，也就是说，同一个Region内部的多个CAS操作是严格串行执行的，不同Region间的多个CAS操作可以并行执行。

重要的CAS（Compare And Swap）：checkAndPut、incrementColumnValue（）

对那些依赖CAS（Compare-And-Swap:指increment/append这样的读后写原子操作）接口的服务，需要意识到这个操作的吞吐是受限的，因为CAS操作本质上是Region级别串行执行的。当然，在HBase 2.x版已经调整设计，对同一个Region内的不同行可以并行执行CAS，这大大提高了Region内的CAS吞吐。

3、Scan Filter设置 和优化很重要！！！

case：我们之前碰到过一种情况，有两个集群，互为主备，其中一个集群由于工具bug导致数据缺失，想通过另一个备份集群的数据来修复异常集群。最快的方式就是，把备份集群的数据导一个快照拷贝到异常集群，然后通过CopyTable工具扫快照生成HFile，最后bulk load到异常集群，完成数据的修复。另外的一种场景是，用户在写入大量数据后，发现选择的split keys不合适，想重新选择split keys建表。这时，也可以通过Snapshot生成HFile再bulk load的方式生成新表。

4、业务发现请求延迟很高，但是HBase服务端延迟正常

某些业务发现HBase客户端上报的p99和p999延迟非常高，但是观察HBase服务端的p99和p999延迟正常。这种情况下一般需要观察HBase客户端的监控和日志。按照我们的经验，一般来说，有这样一些常见问题：

HBase客户端所在进程Java GC。由于HBase客户端作为业务代码的一个Java依赖，因此一旦业务进程发生较为严重的Full GC，必然会导致HBase客户端监控到的请求延迟很高，这时需要排查GC的原因。•
业务进程所在机器的CPU或者网络负载较高。对于上层业务来说一般不涉及磁盘资源的开销，所以主要看load和网络是否过载。•
HBase客户端层面的bug。这种情况出现的概率不大，但也不排除有这种可能。

## 四、RegionServer的核心模块

RegionServer是HBase系统中最核心的组件，主要负责用户数据写入、读取等基础操作。RegionServer组件实际上是一个综合体系，包含多个各司其职的核心模块：HLog、MemStore、HFile以及BlockCache

功能：

一个RegionServer由一个（或多个）HLog、一个BlockCache以及多个Region组成。其中，

HLog用来保证数据写入的可靠性；

BlockCache可以将数据块缓存在内存中以提升数据读取性能；

Region是HBase中数据表的一个数据分片，一个RegionServer上通常会负责多个Region的数据读写。

一个Region由多个Store组成，每个Store存放对应列簇的数据，比如一个表中有两个列簇，这个表的所有Region就都会包含两个Store。

每个Store包含一个MemStore和多个HFile，用户数据写入时会将对应列簇数据写入相应的MemStore，一旦写入数据的内存大小超过设定阈值，系统就会将MemStore中的数据落盘形成HFile文件

### 1、HLog

HBase中系统故障恢复以及主从复制都基于HLog实现
所有写入操作（写入、更新以及删除）的数据都先以追加形式写入HLog，再写入MemStore。大多数情况下，HLog并不会被读取，但如果RegionServer在某些异常情况下发生宕机，此时已经写入MemStore中但尚未f lush到磁盘的数据就会丢失，需要回放HLog补救丢失的数据。
Base主从复制需要主集群将HLog日志发送给从集群，从集群在本地执行回放操作，完成集群之间的数据复制。

•每个RegionServer拥有一个或多个HLog，每个HLog是多个Region共享的
HLog中，日志单元WALEntry（图中小方框）表示一次行级更新的最小追加单元，它由HLogKey和WALEdit两部分组成，其中HLogKey由table name、region name以及sequenceid等字段构成。
WALEdit用来表示一个事务中的更新集合，为了解决日志结构无法保证行级事务的原子性，HBase将一个行级事务的写入操作表示为一条记录。

HLog 的生命周期：HLog 创建、HLog 滚动、HL失效、HL删除

1）HLog构建：HBase的任何写入（更新、删除）操作都会先将记录追加写入到HLog文件中。

2）HLog滚动：HBase后台启动一个线程，每隔一段时间进行日志滚动。日志滚动会新建一个新的日志文件，接收新的日志数据。日志滚动机制主要是为了方便过期日志数据能够以文件的形式直接删除。

3）HLog失效：写入数据一旦从MemStore中落盘，对应的日志数据就会失效。为了方便处理，HBase中日志失效删除总是以文件为单位执行。

4）HLog删除：Master后台会启动一个线程，每隔一段时间检查一次文件夹oldWALs下的所有失效日志文件，确认是否可以删除

HBase系统中一张表会被水平切分成多个Region，每个Region负责自己区域的数据读写请求。水平切分意味着每个Region会包含所有的列簇数据，HBase将不同列簇的数据存储在不同的Store中，每个Store由一个MemStore和一系列HFile组成

### 2、MemStore

HBase基于LSM树模型实现，所有的数据写入操作首先会顺序写入日志HLog，再写入MemStore，当MemStore中数据大小超过阈值之后再将这些数据批量写入磁盘，生成一个新的HFile文件。

这种写入方式将一次随机IO写入转换成一个顺序IO写入（HLog顺序写入）加上一次内存写入（MemStore写入），使得写入性能得到极大提升
HFile中KeyValue数据需要按照Key排序，排序之后可以在文件级别根据有序的Key建立索引树，极大提升数据读取效率。（MemStore就是KeyValue数据排序的实际执行者。）
MemStore作为一个缓存级的存储组件，总是缓存着最近写入的数据。对于很多业务来说，最新写入的数据被读取的概率会更大，
在数据写入HFile之前，可以在内存中对KeyValue数据进行很多更高级的优化。比如，如果业务数据保留版本仅设置为1，在业务更新比较频繁的场景下，MemStore中可能会存储某些数据的多个版本。这样，MemStore在将数据写入HFile之前实际上可以丢弃老版本数据，仅保留最新版本数据。

内部结构，

保证高效的写入效率，又能够保证高效的多线程读取效率？
HBase并没有直接使用原始跳跃表，而是使用了JDK自带的数据结构ConcurrentSkipListMap。ConcurrentSkipListMap底层使用跳跃表来保证数据的有序性，并保证数据的写入、查找、删除操作都可以在O(logN)的时间复杂度完成。ConcurrentSkipListMap有个非常重要的特点是线程安全，它在底层采用了CAS原子性操作，避免了多线程访问条件下昂贵的锁开销，极大地提升了多线程访问场景下的读写性能。

MemStore由两个ConcurrentSkipListMap（称为A和B）实现，写入操作（包括更新删除操作）会将数据写入ConcurrentSkipListMap A，当ConcurrentSkipListMap A中数据量超过一定阈值之后会创建一个新的ConcurrentSkipListMap B来接收用户新的请求，之前已经写满的ConcurrentSkipListMap A会执行异步flush操作落盘形成HFile。（这个过程和 nn 更新的内存模型相似）

为什么MemStore的工作模式会引起严重的内存碎片？这是因为一个RegionServer由多个Region构成，每个Region根据列簇的不同又包含多个MemStore，这些MemStore都是共享内存的，不同Region的数据写入对应的MemStore，因为共享内存，在JVM看来所有MemStore的数据都是混合在一起写入Heap的。随着内存碎片越来越小，最后甚至分配不出来足够大的内存给写入的对象，此时就会触发JVM执行Full GC合并这些内存碎片。

解决：为了优化这种内存碎片可能导致的Full GC，HBase借鉴了线程本地分配缓存（Thread-Local Allocation Buffer，TLAB）的内存管理方式，通过顺序化分配内存、内存数据分块等特性使得内存碎片更加粗粒度，有效改善Full GC情况

1）每个MemStore会实例化得到一个MemStoreLAB对象。

2）MemStoreLAB会申请一个2M大小的Chunk数组，同时维护一个Chunk偏移量，该偏移量初始值为0。

3）当一个KeyValue值插入MemStore后，MemStoreLAB会首先通过KeyValue.getBuffer()取得data数组，并将data数组复制到Chunk数组中，之后再将Chunk偏移量往前移动data. length。

4）当前Chunk满了之后，再调用new byte[2 * 1024 * 1024]申请一个新的Chunk。

因为MemStore会在将数据写入内存时首先申请2M的Chunk，再将实际数据写入申请的Chunk中。这种内存管理方式，使得f lush之后残留的内存碎片更加粗粒度，极大降低Full GC的触发频率。

如果这些Chunk能够被循环利用，系统就不需要申请新的Chunk，这样就会使得YGC频率降低，晋升到老年代的Chunk就会减少，CMS GC发生的频率也会降低。这就是MemStore Chunk Pool的核心思想

1）系统创建一个Chunk Pool来管理所有未被引用的Chunk，这些Chunk就不会再被JVM当作垃圾回收。

2）如果一个Chunk没有再被引用，将其放入Chunk Pool。

3）如果当前Chunk Pool已经达到了容量最大值，就不会再接纳新的Chunk。

4）如果需要申请新的Chunk来存储KeyValue，首先从Chunk Pool中获取，如果能够获取得到就重复利用，否则就重新申请一个新的Chunk。

### 3、HFile

HFile文件主要分为4个部分：Scanned block部分、Non-scanned block部分、Load-on-open部分和Trailer。

•Scanned Block部分：顾名思义，表示顺序扫描HFile时所有的数据块将会被读取。这个部分包含3种数据块：Data Block，Leaf Index Block以及Bloom Block。其中Data Block中存储用户的KeyValue数据，Leaf Index Block中存储索引树的叶子节点数据，Bloom Block中存储布隆过滤器相关数据。•
Non-scanned Block部分：表示在HFile顺序扫描的时候数据不会被读取，主要包括Meta Block和Intermediate Level Data Index Blocks两部分。•
Load-on-open部分：这部分数据会在RegionServer打开HFile时直接加载到内存中，包括FileInfo、布隆过滤器MetaBlock、Root Data Index和Meta IndexBlock。•
Trailer部分：这部分主要记录了HFile的版本信息、其他各个部分的偏移值和寻
HFileBlock主要包含两部分：BlockHeader和BlockData。其中BlockHeader主要存储Block相关元数据，BlockData用来存储具体数据。Block元数据中最核心的字段是BlockType字段，表示该Block的类型

1、Data Block是HBase中文件读取的最小单元。Data Block中主要存储用户的KeyValue数据，而KeyValue结构是HBase存储的核心。HBase中所有数据都是以KeyValue结构存储在HBase中。

2、一次get请求根据布隆过滤器进行过滤查找需要执行以下三步操作

1）首先根据待查找Key在Bloom Index Block所有的索引项中根据BlockKey进行二分查找，定位到对应的Bloom Index Entry。

2）再根据Bloom Index Entry中BlockOffset以及BlockOndiskSize加载该Key对应的位数组。

3）对Key进行Hash映射，根据映射的结果在位数组中查看是否所有位都为1，如果不是，表示该文件中肯定不存在该Key，否则有可能存在。

### 4、BlockCache

BlockCache是RegionServer级别的，一个RegionServer只有一个BlockCache，在RegionServer启动时完成BlockCache的初始化工作。HBase先后实现了3种BlockCache方案，LRUBlockCache是最早的实现方案，也是默认的实现方案；第二种方案SlabCache，另一种可选方案BucketCache。

BucketCache，Block写入缓存以及从缓存中读取Block的流程

Block缓存写入流程如下：

1）将Block写入RAMCache。实际实现中，HBase设置了多个RAMCache，系统首先会根据blockKey进行hash，根据hash结果将Block分配到对应的RAMCache中。

2）WriteThead从RAMCache中取出所有的Block。和RAMCache相同，HBase会同时启动多个WriteThead并发地执行异步写入，每个WriteThead对应一个RAMCache。

3）每个WriteThead会遍历RAMCache中所有Block，分别调用bucketAllocator为这些Block分配内存空间。

4）BucketAllocator会选择与Block大小对应的Bucket进行存放，并且返回对应的物理地址偏移量offset。

5）WriteThead将Block以及分配好的物理地址偏移量传给IOEngine模块，执行具体的内存写入操作。

6）写入成功后，将blockKey与对应物理内存偏移量的映射关系写入BackingMap中，方便后续查找时根据blockKey直接定位。

Block缓存读取流程如下：

1）首先从RAMCache中查找。对于还没有来得及写入Bucket的缓存Block，一定存储在RAMCache中。

2）如果在RAMCache中没有找到，再根据blockKey在BackingMap中找到对应的物理偏移地址量offset。

3）根据物理偏移地址offset直接从内存中查找对应的Block数据。

## 五、Hbase 读写流程 & Compaction

### 1、hbase 写入流程

写入流程可以概括为三个阶段。

1）客户端处理阶段：客户端将用户的写入请求进行预处理，并根据集群元数据定位写入数据所在的RegionServer，将请求发送给对应的RegionServer。

2）Region写入阶段：RegionServer接收到写入请求之后将数据解析出来，首先写入WAL，再写入对应Region列簇的MemStore。

数据写入Region的流程可以抽象为两步：追加写入HLog，随机写入MemStore。

HBase使用LMAX Disruptor框架实现了无锁有界队列操作

MemStore的写入流程可以表述为以下3步。

1）检查当前可用的Chunk是否写满，如果写满，重新申请一个2M的Chunk。
2）将当前KeyValue在内存中重新构建，在可用Chunk的指定offset处申请内存创建一个新的KeyValue对象。
3）将新创建的KeyValue对象写入ConcurrentSkipListMap中。
3）MemStore Flush阶段：当Region中MemStore容量超过一定阈值，系统会异步执行f lush操作，将内存中的数据写入文件，形成HFile。

为了减少f lush过程对读写的影响，HBase采用了类似于两阶段提交的方式，将整个f lush过程分为三个阶段。

1）prepare阶段：遍历当前Region中的所有MemStore，将MemStore中当前数据集CellSkipListSet（内部实现采用ConcurrentSkipListMap）做一个快照snapshot，然后再新建一个CellSkipListSet接收新的数据写入。prepare阶段需要添加updateLock对写请求阻塞，结束之后会释放该锁。因为此阶段没有任何费时操作，因此持锁时间很短。
2）flush阶段：遍历所有MemStore，将prepare阶段生成的snapshot持久化为临时文件，临时文件会统一放到目录.tmp下。这个过程因为涉及磁盘IO操作，因此相对比较耗时。
3）commit阶段：遍历所有的MemStore，将flush阶段生成的临时文件移到指定的ColumnFamily目录下，针对HFile生成对应的storefile和Reader，把storefile添加到Store的storefiles列表中，最后再清空prepare阶段生成的snapshot。
流程总结：f lush阶段生成HFile和Compaction阶段生成HFile的流程完全相同，不同的是，f lush读取的是MemStore中的KeyValue写成HFile，而Compaction读取的是多个HFile中的KeyValue写成一个大的HFile，KeyValue来源不同。KeyValue数据生成HFile，首先会构建Bloom Block以及Data Block，一旦写满一个Data Block就会将其落盘同时构造一个Leaf Index Entry，写入Leaf Index Block，直至Leaf Index Block写满落盘。实际上，每写入一个KeyValue就会动态地去构建"Scanned Block"部分，等所有的KeyValue都写入完成之后再静态地构建"Non-scanned Block"部分、"Load on open"部分以及"Trailer"部分。

bulkload的流程

### 2、hbase 读取流程

HBase读数据的流程更加复杂。主要基于两个方面的原因：

一是因为HBase一次范围查询可能会涉及多个Region、多块缓存甚至多个数据存储文件；

二是因为HBase中更新操作以及删除操作的实现都很简单，更新操作并没有更新原有数据，而是使用时间戳属性实现了多版本；删除操作也并没有真正删除原有数据，只是插入了一条标记为"deleted"标签的数据，而真正的数据删除发生在系统异步执行Major Compact的时候。读取过程需要根据版本进行过滤，对已经标记删除的数据也要进行过滤。

读流程从头到尾可以分为如下4个步骤：Client-Server读取交互逻辑（其中Client-Server交互逻辑主要介绍HBase客户端在整个scan请求的过程中是如何与服务器端进行交互的），Server端Scan框架体系（了解Server端Scan框架体系，从宏观上介绍HBase RegionServer如何逐步处理一次scan请求），过滤淘汰不符合查询条件的HFile，从HFile中读取待查找Key

1、Client-Server读取交互逻辑
HBase数据读取可以分为get和scan两类，get请求通常根据给定rowkey查找一行记录，scan请求通常根据给定的startkey和stopkey查找多行满足条件的记录。但从技术实现的角度来看，get请求也是一种scan请求（最简单的scan请求，scan的条数为1）。从这个角度讲，所有读取操作都可以认为是一次scan操作。

2、Server端Scan框架体系
一次scan可能会同时扫描一张表的多个Region，对于这种扫描，客户端会根据hbase:meta元数据将扫描的起始区间[startKey, stopKey)进行切分，切分成多个互相独立的查询子区间，每个子区间对应一个Region。比如当前表有3个Region，Region的起始区间分别为：["a","c")，["c", "e")，["e", "g")，客户端设置scan的扫描区间为["b", "f")。因为扫描区间明显跨越了多个Region，需要进行切分，按照Region区间切分后的子区间为["b", "c")，["c", "e")，["e", "f ")。

RegionServer接收到客户端的get/scan请求之后做了两件事情：首先构建scanner iterator体系；然后执行next函数获取KeyValue，并对其进行条件过滤。

（1）构建scanner iterator体系

Scanner的核心体系包括三层Scanner：RegionScanner，StoreScanner，MemStoreScanner和StoreFileScanner。

•一个RegionScanner由多个StoreScanner构成。一张表由多少个列簇组成，就有多少个StoreScanner，每个StoreScanner负责对应Store的数据查找。•
一个StoreScanner由MemStoreScanner和StoreFileScanner构成。
，RegionScanner以及StoreScanner并不负责实际查找操作，它们更多地承担组织调度任务，负责KeyValue最终查找操作的是StoreFileScanner和MemStoreScanner。

步骤 3中，KeyValueScanner合并构建最小堆。将该Store中的所有StoreFileScanner和MemStoreScanner合并形成一个heap（最小堆），所谓heap实际上是一个优先级队列。在队列中，按照Scanner排序规则将Scanner seek得到的KeyValue由小到大进行排序。最小堆管理Scanner可以保证取出来的KeyValue都是最小的，这样依次不断地pop就可以由小到大获取目标KeyValue集合，保证有序性。

（2）执行next函数获取KeyValue，并对其进行条件过滤

1）检查该KeyValue的KeyType是否是Deleted/DeletedColumn/DeleteFamily等，如果是，则直接忽略该列所有其他版本，跳到下列（列簇）。

2）检查该KeyValue的Timestamp是否在用户设定的Timestamp Range范围，如果不在该范围，忽略。

3）检查该KeyValue是否满足用户设置的各种f ilter过滤器，如果不满足，忽略。

4）检查该KeyValue是否满足用户查询中设定的版本数，比如用户只查询最新版本，则忽略该列的其他版本；反之，如果用户查询所有版本，则还需要查询该cell的其他版本。

3、过滤淘汰不符合查询条件的HFile
过滤手段主要有三种：根据KeyRange过滤，根据TimeRange过滤，根据布隆过滤器进行过滤。

4、从HFile中读取待查找Key

1. 根据HFile索引树定位目标Block
2. BlockCache中检索目标Block
3. HDFS文件中检索目标Block

### 3、Compaction

HBase根据合并规模将Compaction分为两类：Minor Compaction和Major Compaction。•

Minor Compaction是指选取部分小的、相邻的HFile，将它们合并成一个更大的HFile。•
Major Compaction是指将一个Store中所有的HFile合并成一个HFile，这个过程还会完全清理三类无意义数据：被删除的数据、TTL过期数据、版本号超过设定版本号的数据。
HBase的体系架构下，Compaction有以下核心作用：

•合并小文件，减少文件数，稳定随机读延迟。•
提高数据的本地化率。•
清除无效数据，减少数据存储量。
Compaction操作是所有LSM树结构数据库所特有的一种操作，它的核心操作是批量将大量小文件合并成大文件用以提高读取性能。另外，Compaction是有副作用的，它在一定程度上消耗系统资源，进而影响上层业务的读取响应

HBase会将该Compaction交由一个独立的线程处理，该线程首先会从对应Store中选择合适的HFile文件进行合并，这一步是整个Compaction的核心

HFile文件合并执行过程

1）分别读出待合并HFile文件的KeyValue，进行归并排序处理，之后写到./tmp目录下的临时文件中。

2）将临时文件移动到对应Store的数据目录。

3）将Compaction的输入文件路径和输出文件路径封装为KV写入HLog日志，并打上Compaction标记，最后强制执行sync。

4）将对应Store数据目录下的Compaction输入文件全部删除。

## 六、Hbase 的负载均衡 & 故障恢复 & 复制

### 1、Region 迁移

HBase中Region迁移是一个非常轻量级的操作。所谓轻量级，是因为HBase的数据实际存储在HDFS上，不需要独立进行管理，因而Region在迁移的过程中不需要迁移实际数据，只要将读写服务迁移即可

Region迁移操作分两个阶段：unassign阶段和assign阶段。

1、unassign 阶段

1）Master生成事件M_ZK_REGION_CLOSING并更新到ZooKeeper组件，同时将本地内存中该Region的状态修改为PENDING_CLOSE。

2）Master通过RPC发送close命令给拥有该Region的RegionServer，令其关闭该Region。

3）RegionServer接收到Master发送过来的命令后，生成一个RS_ZK_REGION_CLOSING事件，更新到ZooKeeper。

4）Master监听到ZooKeeper节点变动后，更新内存中Region的状态为CLOSING。

5）RegionServer执行Region关闭操作。如果该Region正在执行f lush或者Compaction，等待操作完成；否则将该Region下的所有MemStore强制f lush，然后关闭Region相关的服务。

6）关闭完成后生成事件RS_ZK_REGION_CLOSED，更新到ZooKeeper。Master监听到ZooKeeper节点变动后，更新该Region的状态为CLOSED。

2、assign阶段

1）Master生成事件M_ZK_REGION_OFFLINE并更新到ZooKeeper组件，同时将本地内存中该Region的状态修改为PENDING_OPEN。

2）Master通过RPC发送open命令给拥有该Region的RegionServer，令其打开该Region。

3）RegionServer接收到Master发送过来的命令后，生成一个RS_ZK_REGION_OPENING事件，更新到ZooKeeper。

4）Master监听到ZooKeeper节点变动后，更新内存中Region的状态为OPENING。

5）RegionServer执行Region打开操作，初始化相应的服务。

6）打开完成之后生成事件RS_ZK_REGION_OPENED，更新到ZooKeeper，Master监听到ZooKeeper节点变动后，更新该Region的状态为OPEN。

Region的这些状态会存储在三个区域：meta表，Master内存，ZooKeeper的region-in-transition节点

在很多异常情况下，Region状态在三个地方并不能保持一致，这就会出现region-in-transition(RIT)现象

### 2、hbase region 合并

最典型的一个应用场景是，在某些业务中本来接收写入的Region在之后的很长时间都不再接收任何写入，而且Region上的数据因为TTL过期被删除。这种场景下的Region实际上没有任何存在的意义，称为空闲Region。一旦集群中空闲Region很多，就会导致集群管理运维成本增加。

### 3、hbase region 分裂

1、满足Region分裂策略之后就会触发Region分裂。分裂被触发后的第一件事是寻找分裂点。

2、HBase对于分裂点的定义为：整个Region中最大Store中的最大文件中最中心的一个Block的首个rowkey。另外，HBase还规定，如果定位到的rowkey是整个文件的首个rowkey或者最后一个rowkey，则认为没有分裂点。

3、HBase将整个分裂过程包装成了一个事务，目的是保证分裂事务的原子性。整个分裂事务过程分为三个阶段：prepare、execute和rollback。

（1）prepare阶段在内存中初始化两个子Region，具体生成两个HRegionInfo对象，包含tableName、regionName、startkey、endkey等。同时会生成一个transaction journal，这个对象用来记录分裂的进展

（2）execute阶段分裂的核心操作

1）RegionServer将ZooKeeper节点/region-in-transition中该Region的状态更改为SPLITING。

2）Master通过watch节点/region-in-transition检测到Region状态改变，并修改内存中Region的状态，在Master页面RIT模块可以看到Region执行split的状态信息。

3）在父存储目录下新建临时文件夹.split，保存split后的daughter region信息。

4）关闭父Region。父Region关闭数据写入并触发f lush操作，将写入Region的数据全部持久化到磁盘。此后短时间内客户端落在父Region上的请求都会抛出异常NotServingRegionException。

5）在.split文件夹下新建两个子文件夹，称为daughter A、daughter B，并在文件夹中生成reference文件，分别指向父Region中对应文件。这个步骤是所有步骤中最核心的一个环节

6）父Region分裂为两个子Region后，将daughter A、daughter B拷贝到HBase根目录下，形成两个新的Region。

7）父Region通知修改hbase:meta表后下线，不再提供服务。下线后父Region在meta表中的信息并不会马上删除，而是将split列、off line列标注为true，并记录两个子Region

8）开启daughter A、daughter B两个子Region。通知修改hbase:meta表，正式对外提供服务

（3）rollback阶段如果execute阶段出现异常，则执行rollback操作。为了实现回滚，整个分裂过程分为很多子阶段，回滚程序会根据当前进展到哪个子阶段清理对应的垃圾数据。代码中使用JournalEntryType来表征各个子阶段

4、为了实现原子性，HBase使用状态机的方式保存分裂过程中的每个子步骤状态，这样一旦出现异常，系统可以根据当前所处的状态决定是否回滚，以及如何回滚（一旦在分裂过程中出现RegionServer宕机的情况，有可能会出现分裂处于中间状态的情况，也就是RIT状态）

5、分布式系统通过增加节点实现扩展性，但如果说扩容就是增加节点其实并不准确。扩容操作一般分为两个步骤：首先，需要增加节点并让系统感知到节点加入；其次，需要将系统中已有节点负载迁移到新加入节点上。

### 4、宕机原理恢复

Master主要负责集群管理调度，在实际生产线上并没有非常大的压力，因此发生软件层面故障的概率非常低。RegionServer主要负责用户的读写服务，进程中包含很多缓存组件以及与HDFS交互的组件，实际生产线上往往会有非常大的压力，进而造成的软件层面故障会比较多

#### 1、可能导致RegionServer宕机的异常

Full GC异常：长时间的Full GC是导致RegionServer宕机的最主要原因
据不完全统计，80%以上的宕机原因都和JVM Full GC有关。导致JVM发生Full GC的原因有很多：HBase对于Java堆内内存管理的不完善，HBase未合理使用堆外内存，JVM启动参数设置不合理，业务写入或读取吞吐量太大，写入读取字段太大，等等。其中部分原因要归结于HBase系统本身，另一部分原因和用户业务以及HBase相关配置有关

HDFS异常
RegionServer写入读取数据都是直接操作HDFS的，如果HDFS发生异常会导致RegionServer直接宕机。

机器宕机
物理节点直接宕机也是导致RegionServer进程挂掉的一个重要原因。通常情况下，物理机直接宕机的情况相对比较少，但虚拟云主机发生宕机的频率比较高。很多公司会将HBase系统部署在虚拟云环境，因为种种原因发生机器宕机的情况相对就会多一些。网络环境不稳定其实也可以归属于这类。

HBase Bug
生产线上因为HBase系统本身bug导致RegionServer宕机的情况很少，但在之前的版本中有一个问题让笔者印象深刻：RegionServer经常会因为耗尽了机器的端口资源而自行宕机，这个bug的表现是，随着时间的推移，处于close_wait状态的端口越来越多，当超过机器的配置端口数（65535）时RegionServer进程就会被kill掉

#### 2、故障自动恢复的原理

region 恢复：一旦RegionServer发生宕机，HBase会马上检测到这种宕机，并且在检测到宕机之后将宕机RegionServer上的所有Region重新分配到集群中其他正常的RegionServer上，再根据HLog进行丢失数据恢复，恢复完成之后就可以对外提供服务。整个过程都是自动完成的，

1）Master检测到RegionServer宕机。HBase检测宕机是通过ZooKeeper实现的，正常情况下RegionServer会周期性向ZooKeeper发送心跳，一旦发生宕机，心跳就会停止，超过一定时间（SessionTimeout）ZooKeeper就会认为RegionServer宕机离线，并将该消息通知给Master。

2）切分未持久化数据的HLog日志。RegionServer宕机之后已经写入MemStore但还没有持久化到文件的这部分数据必然会丢失，HBase提供了WAL机制来保证数据的可靠性，可以使用HLog进行恢复补救。HLog中所有Region的数据都混合存储在同一个文件中，为了使这些数据能够按照Region进行组织回放，需要将HLog日志进行切分再合并，同一个Region的数据最终合并在一起，方便后续按照Region进行数据恢复。

3）Master重新分配宕机RegionServer上的Region。RegionServer宕机之后，该Region Server上的Region实际上处于不可用状态，所有路由到这些Region上的请求都会返回异常。但这种情况是短暂的，因为Master会将这些不可用的Region重新分配到其他RegionServer上，但此时这些Region还并没有上线，因为之前存储在MemStore中还没有落盘的数据需要回放。

4）回放HLog日志补救数据。第3）步中宕机RegionServer上的Region会被分配到其他RegionServer上，此时需要等待数据回放。第2）步中提到HLog已经按照Region将日志数据进行了切分再合并，针对指定的Region，将对应的HLog数据进行回放，就可以完成丢失数据的补救工作。

5）恢复完成，对外提供服务。数据补救完成之后，可以对外提供读写服务。

### 5、备份和恢复

数据库定期备份、定期演练恢复是当下很多重要业务都在慢慢接受的最佳实践。

Snapshot是HBase非常核心的一个功能，使用在线Snapshot备份可以满足用户很多需求，比如增量备份和数据迁移。

全量/增量备份。任何数据库都需要具有备份的功能来实现数据的高可靠性，Snapshot可以非常方便地实现表的在线备份功能，并且对在线业务请求影响非常小。使用备份数据，用户可以在异常发生时快速回滚到指定快照点。
 ○使用场景一：通常情况下，对于重要的业务数据，建议每天执行一次Snapshot来保存数据的快照记录，并且定期清理过期快照，这样如果业务发生严重错误，可以回滚到之前的一个快照点。
○使用场景二：如果要对集群做重大升级，建议升级前对重要的表执行一次Snapshot，一旦升级有任何异常可以快速回滚到升级前。•
数据迁移。可以使用ExportSnapshot功能将快照导出到另一个集群，实现数据的迁移。
○使用场景一：机房在线迁移。比如业务集群在A机房，因为A机房机位不够或者机架不够需要将整个集群迁移到另一个容量更大的B集群，而且在迁移过程中不能停服。基本迁移思路是，先使用Snapshot在B集群恢复出一个全量数据，再使用replication技术增量复制A集群的更新数据，等待两个集群数据一致之后将客户端请求重定向到B机房。
使用场景二：利用Snapshot将表数据导出到HDFS，再使用Hive\Spark等进行离线OLAP分析，比如审计报表、月度报表等。

Snapshot机制并不会拷贝数据，可以理解为它是原数据的一份指针。

HBase为指定表执行Snapshot操作，实际上真正执行Snapshot的是对应表的所有Region

1. 两阶段提交基本原理HBase使用两阶段提交（Two-Phase Commit，2PC）协议来保证Snapshot的分布式原子性。2PC一般由一个协调者和多个参与者组成，整个事务提交分为两个阶段：prepare阶段和commit阶段（或abort阶段）

两阶段提交协议

1）prepare阶段协调者会向所有参与者发送prepare命令

2）所有参与者接收到命令，获取相应资源（比如锁资源），执行prepare操作确认可以执行成功。一般情况下，核心工作都是在prepare操作中完成

3）返回给协调者prepared应答

4）协调者接收到所有参与者返回的prepared应答（表明所有参与者都已经准备好提交），在本地持久化committed状态

5）持久化完成之后进入commit阶段，协调者会向所有参与者发送commit命令

6）参与者接收到commit命令，执行commit操作并释放资源，通常commit操作都非常简单

7）返回给协调者

## 七、运维监控、系统调优、运维案例

### 1、监控指标

### 2、业务隔离

1、运行队列隔离：HBase并没有提供业务级别的队列设置功能，而是提供了读写队列隔离方案，RegionServer可以同时提供写队列、get请求队列和scan请求队列，这样就将写请求、get请求和scan请求分发到不同的队列，不同队列使用不同的工作线程进行处理，有效隔离了不同请求类型的相互影响。

2、计算资源隔离：RSGroup方案的原理非常清晰：用户可以将集群划分为多个组，每个组里包含指定RegionServer集合，每个组同时可以指定特定的业务。RSGroup最核心的作用是保证业务一旦分配到指定组，对应的Region就只能在该组里面的RegionSever上运行，

### 3、HBCK主要工作在两种模式下：一致性检测只读模式和多阶段修复模式

HBase集群一致性主要包括两个方面。•

HBase Region一致性：集群中所有Region都被assign，而且deploy到唯一一台RegionServer上，并且该Region的状态在内存中、hbase:meta表中以及ZooKeeper这三个地方需要保持一致。•
HBase表完整性：对于集群中任意一张表，每个rowkey都仅能存在于一个Region区间。
一个好的运维习惯是，间隔性（比如每天晚上执行）地执行hbck命令，并在多次出现不一致的情况下发出报警信息。

集群修复的基本原则是首先修复低风险的Region一致性问题（以及部分表完整性问题），再谨慎修复部分高风险的表完整性问题（overlap问题）。

对于HBCK工具，笔者总结最好的实践方式如下：

1）周期性地多次执行hbck命令，对集群进行定期体检，如果发现异常则报警。

2）若能对表执行hbck修复，就对表进行修复，而不要对整个集群进行修复操作。

3）大多数导致集群不一致的问题是“ not deployed on any region server ”，可以放心使用-f ixAssignments进行修复，对于上文提到的几种情况都可以放心地进行修复。

4）对于其他overlap的情况，需要管理员认真分析，再谨慎使用hbck命令进行修复。如果可以手动修复，建议手动修复。

5）如果使用HBCK工具无法修复集群的不一致，需要结合日志进行进一步分析，决定修复方案。

### 4、hbase 建表

建表语句整体上可以拆解成三个部分：表名、列簇属性设置、表属性设置。

1、 表名强烈建议生产线创建表时不要单独使用表名，而应该使用命名空间加表名的形式，同一个业务的相关表放在同一个命名空间下，不同业务使用不同的命名空间。

2、 表属性设置，

•预分区设置属性：预分区是HBase最佳实践中非常重要的一个策略，不经过预分区设置的业务通常在后期会出现数据分布极度不均衡的情况，进而造成读写请求不均衡，严重时会出现写入阻塞、读取延迟不可控，甚至影响整个集群其他业务。因此建议所有业务表上线必须做预分区处理。

### 5、Salted Table，对rowkey做哈希是一种很好的解决数据热点的方式

本质上Salted Table通过数据哈希很好地解决了数据热点的问题，同时对get、put这类按照rowkey做点查（只查询一条记录）的操作非常友好，性能也很棒。但是，对于scan操作并不是特别友好，

### 6、hbase 读取性能调优

HBase系统的读取优化可以从三个方面进行：服务器端、客户端、列簇设计

1. 读请求是否均衡？
    优化原理：假如业务所有读请求都落在集群某一台RegionServer上的某几个Region上，很显然，这一方面不能发挥整个集群的并发处理能力，另一方面势必造成此台RegionServer资源严重消耗（比如IO耗尽、handler耗尽等），导致落在该台RegionServer上的其他业务受到波及。也就是说读请求不均衡不仅会造成本身业务性能很差，还会严重影响其他业务。

    观察确认：观察所有RegionServer的读请求QPS曲线，确认是否存在读请求不均衡现象。

    优化建议：Rowkey必须进行散列化处理（比如MD5散列），同时建表必须进行预分区处理。

2. BlockCache设置是否合理？
    优化原理：BlockCache作为读缓存，对于读性能至关重要。默认情况下BlockCache和MemStore的配置相对比较均衡（各占40%），可以根据集群业务进行修正，比如读多写少业务可以将BlockCache占比调大。另一方面，BlockCache的策略选择也很重要，不同策略对读性能来说影响并不是很大，但是对GC的影响却相当显著，尤其在BucketCache的offheap模式下GC表现非常优秀。

    观察确认：观察所有RegionServer的缓存未命中率、配置文件相关配置项以及GC日志，确认BlockCache是否可以优化。

    化建议：如果JVM内存配置量小于20G，BlockCache策略选择LRUBlockCache；否则选择BucketCache策略的offheap模式。

3. HFile文件是否太多？
    优化原理：HBase在读取数据时通常先到MemStore和BlockCache中检索（读取最近写入数据和热点数据），如果查找不到则到文件中检索。HBase的类LSM树结构导致每个store包含多个HFile文件，文件越多，检索所需的IO次数越多，读取延迟也就越高。文件数量通常取决于Compaction的执行策略，一般和两个配置参数有关：hbase.hstore. compactionThreshold和hbase.hstore.compaction.max.size，前者表示一个store中的文件数超过阈值就应该进行合并，后者表示参与合并的文件大小最大是多少，超过此大小的文件不能参与合并。这两个参数需要谨慎设置，如果前者设置太大，后者设置太小，就会导致Compaction合并文件的实际效果不明显，很多文件得不到合并，进而导致HFile文件数变多。

    观察确认：观察RegionServer级别以及Region级别的HFile数，确认HFile文件是否过多。

    优化建议：hbase.hstore.compactionThreshold设置不能太大，默认为3个。

4. Compaction是否消耗系统资源过多？
优化原理：Compaction是将小文件合并为大文件，提高后续业务随机读性能，但是也会带来IO放大以及带宽消耗问题（数据远程读取以及三副本写入都会消耗系统带宽）。正常配置情况下，Minor Compaction并不会带来很大的系统资源消耗，除非因为配置不合理导致Minor Compaction太过频繁，或者Region设置太大发生Major Compaction。

观察确认：观察系统IO资源以及带宽资源使用情况，再观察Compaction队列长度，确认是否由于Compaction导致系统资源消耗过多。

优化建议：对于大Region读延迟敏感的业务（100G以上）通常不建议开启自动Major Compaction，手动低峰期触发。小Region或者延迟不敏感的业务可以开启Major Compaction，但建议限制流量。

5. 数据本地率是不是很低？
优化原理：13.4节详细介绍了HBase中数据本地率的概念，如果数据本地率很低，数据读取时会产生大量网络IO请求，导致读延迟较高。

观察确认：观察所有RegionServer的数据本地率（见jmx中指标PercentFileLocal，在Table Web UI可以看到各个Region的Locality）。

优化建议：尽量避免Region无故迁移。对于本地率较低的节点，可以在业务低峰期执行major_compact。

6. scan缓存是否设置合理？
优化原理：HBase业务通常一次scan就会返回大量数据，因此客户端发起一次scan请求，实际并不会一次就将所有数据加载到本地，而是分成多次RPC请求进行加载，这样设计一方面因为大量数据请求可能会导致网络带宽严重消耗进而影响其他业务，另一方面因为数据量太大可能导致本地客户端发生OOM。在这样的设计体系下，用户会首先加载一部分数据到本地，然后遍历处理，再加载下一部分数据到本地处理，如此往复，直至所有数据都加载完成。数据加载到本地就存放在scan缓存中，默认为100条数据。

通常情况下，默认的scan缓存设置是可以正常工作的。但是对于一些大scan（一次scan可能需要查询几万甚至几十万行数据），每次请求100条数据意味着一次scan需要几百甚至几千次RPC请求，这种交互的代价无疑是很大的。因此可以考虑将scan缓存设置增大，比如设为500或者1000条可能更加合适。笔者之前做过一次试验，在一次scan 10w+条数据量的条件下，将scan缓存从100增加到1000条，可以有效降低scan请求的总体延迟，延迟降低了25%左右。

优化建议：大scan场景下将scan缓存从100增大到500或者1000，用以减少RPC次数。

7. get是否使用批量请求？
优化原理：HBase分别提供了单条get以及批量get的API接口，使用批量get接口可以减少客户端到RegionServer之间的RPC连接数，提高读取吞吐量。另外需要注意的是，批量get请求要么成功返回所有请求数据，要么抛出异常。

优化建议：使用批量get进行读取请求。需要注意的是，对读取延迟非常敏感的业务，批量请求时每次批量数不能太大，最好进行测试。

8. 请求是否可以显式指定列簇或者列？
优化原理：HBase是典型的列簇数据库，意味着同一列簇的数据存储在一起，不同列簇的数据分开存储在不同的目录下。一个表有多个列簇，如果只是根据rowkey而不指定列簇进行检索，不同列簇的数据需要独立进行检索，性能必然会比指定列簇的查询差很多，很多情况下甚至会有2～3倍的性能损失。

优化建议：尽量指定列簇或者列进行精确查找。

9. 离线批量读取请求是否设置禁止缓存？
优化原理：通常在离线批量读取数据时会进行一次性全表扫描，一方面数据量很大，另一方面请求只会执行一次。这种场景下如果使用scan默认设置，就会将数据从HDFS加载出来放到缓存。可想而知，大量数据进入缓存必将其他实时业务热点数据挤出，其他业务不得不从HDFS加载，进而造成明显的读延迟毛刺。

优化建议：离线批量读取请求设置禁用缓存，scan.setCacheBlocks (false)。

10. 布隆过滤器是否设置？
优化原理：布隆过滤器主要用来过滤不存在待检索rowkey的HFile文件，避免无用的IO操作。布隆过滤器取值有两个——row以及rowcol，需要根据业务来确定具体使用哪种。如果业务中大多数随机查询仅仅使用row作为查询条件，布隆过滤器一定要设置为row；如果大多数随机查询使用row+column作为查询条件，布隆过滤器需要设置为rowcol。如果不确定业务查询类型，则设置为row。

优化建议：任何业务都应该设置布隆过滤器，通常设置为row，除非确认业务随机查询类型为row+column，则设置为rowcol。

### 7、hbase 写入性能调优

HBase系统主要应用于写多读少的业务场景，通常来说对系统的写入吞吐量要求都比较高。而在实际生产线环境中，HBase运维人员或多或少都会遇到写入吞吐量比较低、写入比较慢的情况

### 8、Region Server 宕机

触发RegionServer异常宕机的原因多种多样，主要包括：长时间GC导致RegionServer宕机，HDFS DataNode异常导致RegionServer宕机，以及系统严重Bug导致RegionServer宕机。

个

### 9、性能：延迟指标、请求吞吐量

对HBase来说，我们通常所说的性能，其实是分成两个部分的。第一个部分是延迟指标，也就是说单次RPC请求的耗时。我们常用的衡量指标包括：get操作的平均延迟耗时（ms），get操作的p75延迟耗时，get操作的p99延迟耗时，get操作的p999延迟耗时

第二个部分是请求吞吐量，也可以简单理解为每秒能处理的RPC请求次数。最典型的衡量指标是QPS（Query Per Second）。为了实现HBase更高的吞吐量，常见的优化手段有：•为HBase RegionServer配置更合适的Handler数，避免由于个别Handler处理请求太慢，导致吞吐量受限。但Handler数也不能配置太大，因为太多的线程数会导致CPU出现频繁的线程上下文切换，反而影响系统的吞吐量。•在RegionServer端，把读请求和写请求分到两个不同的处理队列中，由两种不同类型的Handler处理。这样可以避免出现因部分耗时的读请求影响写入吞吐量的现象。•某些业务场景下，采用Buffered Put的方式替换不断自动刷新的put操作，本质上也是为了实现更高的吞吐。一般来说，一旦延迟降低，吞吐量都会有不同幅度的提升；反之，吞吐量上去了，受限于系统层面的资源或其他条件，延迟不一定随之降低。

### 10、介绍Pecolator是如何基于HBase/BigTable单行事务实现跨行事务的

Percolator协议本质上是借助BigTable/HBase的单行事务来实现分布式跨行事务，主要的优点有：•基于BigTable/HBase的行级事务，实现了分布式事务协议。代码实现较为简单。•每一行的行锁信息都存储在各自的行内，锁信息是分布式存储在各个节点上的。换句话说，全局锁服务是去中心化的，不会限制整个系统的吞吐。
