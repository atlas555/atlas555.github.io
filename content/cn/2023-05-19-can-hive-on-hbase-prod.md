---
title: "生产环境下 hive 查询 hbase 数据技术架构的可能性"
date: 2023-05-19
author: "张晓龙"
slug: pro-env-hive-on-hbase
draft: false
show_toc: false
keywords:
- production
- hive
- hbase
- architecture
description : "生产环境下 hive 查询 hbase 数据技术架构的可能性"
categories: bigdata
tags: 
- hive
---

线上hive 想查询 hbase 的数据，目前是将 hbase 数据同步到 hive 中，然后通过 hive 引擎查询。那 **能不能通过 hive 直接查询 hbase 的数据呢**？ **首先答案是可以的**。

通过 Hive 外表的方式，利用 `org.apache.hadoop.hive.hbase.HBaseStorageHandler` [组件（维护Hive字段和HBase中的列）](https://cwiki.apache.org/confluence/display/Hive/StorageHandlers)，实际上是 Hive 提供对外的接口，然后通过实现这套接口来操作 hive 以外的数据存储。

先认识下 hive StorageHandlers：

> StorageHandlers: a storage handler implementation is also available for Hypertable, and others are being developed for Cassandra, Azure Table, JDBC (MySQL and others), MongoDB, ElasticSearch, Phoenix HBase, VoltDB and Google Spreadsheets.  A Kafka handler demo is available.
>
> Hive storage handler support builds on existing extensibility features in both Hadoop and Hive:
> 
> - input formats
> - output formats
> - serialization/deserialization libraries
> 
> These two distinctions (managed vs. external and native vs non-native) are orthogonal. Hence, there are four possibilities for base tables:
> 
> - managed native: what you get by default with CREATE TABLE
> - external native: what you get with CREATE EXTERNAL TABLE when no STORED BY clause is specified
> - managed non-native: what you get with CREATE TABLE when a STORED BY clause is specified; Hive stores the definition in its metastore, but does not create any files itself;instead, it calls the storage handler with a request to create a corresponding object structure
> - external non-native: what you get with CREATE EXTERNAL TABLE when a STORED BY clause is specified; Hive registers the definition in its metastore and calls the storage handler to check that it matches the primary definition in the other system
> 
> Hive feature : allows Hive QL statements to access HBase tables for both read (SELECT) and write (INSERT). It is even possible to combine access to HBase tables with native Hive tables via joins and unions.

简单的外表关联。举个例子：

``` sql
hive> CREATE EXTERNAL TABLE hive_test (
   > rowkey string,
   > a string,
   > b string,
   > c string
   > ) STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler' WITH
   > SERDEPROPERTIES("hbase.columns.mapping" = ":key,cf:a,cf:b,cf:c")
   > TBLPROPERTIES("hbase.table.name" = "some_existing_table","hbase.mapred.output.outputtable" = "some_existing_table");
```

**需要特殊关注的就是hive 字段和 hbase column 的 map 处理**。内部比较多的 cases 处理，详见相关资料[2]。

来看一个例子：

```sql
// external table
CREATE EXTERNAL TABLE tbl(id string, data map<string,string>)
STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'
WITH SERDEPROPERTIES ("hbase.columns.mapping" = ":key,data:")
TBLPROPERTIES("hbase.table.name" = "tbl");

// sql case 1 :  speed really fast!
select * from tbl", "select id from tbl", "select id, data
from tbl

// sql case 2 : speed incredibly slow!!!
select id from tbl where substr(id, 0, 5) = "12345"
```

这里的问题就是查询速度极慢！分析其原因 case 2 查询 scan 全表数据导致。

Hive HBase handler 不能很好的处理hbase rowkey 的起止位置，比如 substr(id, 0, 5) = "12345"，没有使用 start & stop row keys，导致查询慢。

explain hive sql，如果不存在filterExpr，则 query 会 scan 整表。

``` sql
EXPLAIN SELECT * FROM tbl WHERE (id>='12345') AND (id<'12346')
STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Alias -> Map Operator Tree:
        tbl 
          TableScan
            alias: tbl 
            filterExpr:
                expr: ((id>= '12345') and (id < '12346'))
                type: boolean
            Filter Operator
                ....
```

有一个方式能够利用 hbase 的 row-key prefixes，将上述 sql 的 substr(id, 0, 5) = "12345" 改为 id>="12345" AND id<"12346" 即可，hbase 的 row key 会 SCAN (12345, 12346)。 

hive on hbase 整合使用 Tips：

> 1. Make sure you set the following properties to take advantage of batching to reduce the number of RPC calls (the number depends on the size of your columns)
> 
>     SET hbase.scan.cache=10000;
> 
>     SET hbase.client.scanner.cache=10000;
> 
> 2. Make sure you set the following properties to run a distributed job in your task trackers instead of running local job.
> 
>     SET mapred.job.tracker=[YOUR_JOB_TRACKER]:8021;
> 
>     SET hbase.zookeeper.quorum=[ZOOKEEPER_NODE_1],[ZOOKEEPER_NODE_2],[ZOOKEEPER_NODE_3];
> 
> 3. Reduce the amount of columns of your SELECT statement to the minimum. Try not to SELECT *
> 
> 4. Whenever you want to use start & stop row keys to prevent full table scans, always provide key>=x and key<y expressions (don't use the BETWEEN operator)
> 
> 5. Always EXPLAIN SELECT your queries before executing them
> 

----
综合来看：**能不能通过 hive 直接查询 hbase 的数据应用到生产环境**？

**答案是：最好不要！如果想用但有条件**

条件：

1、**不能用在线上 ETL pipeline（出于效率、SLA、数据管理考虑），可以用的离线数据分析场景**

2、SQL 写法需要改造优化，避免全表 scan

3、只进行查询操作，不进行 insert。避免大数据量 insert 数据到外表hbase， 造成 hbase WAL 过载。

相关资料：

1. [Tuning Hive Queries That Uses Underlying HBase Table](https://stackoverflow.com/questions/30074734/tuning-hive-queries-that-uses-underlying-hbase-table)
2. [HBaseIntegration](https://cwiki.apache.org/confluence/display/Hive/HBaseIntegration)
3. [Using Hive to access an existing HBase table example](https://docs.cloudera.com/HDPDocuments/HDP3/HDP-3.0.1/hbase-data-access/content/hdag_using_hive_to_access_an_existing_hbase_table_example.html)
