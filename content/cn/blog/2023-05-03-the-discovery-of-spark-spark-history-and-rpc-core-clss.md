---
title: "Saprk3.x Journey of Discovery | Spark RPC 框架的发展历史和RPC核心类图关系"
date: 2023-05-03
author: "张晓龙"
slug: spark-rpc-history-core-class
description: "Saprk3.x Journey of Discovery | Spark RPC 框架的发展历史和RPC核心类图关系"
categories: bigdata
tags: 
- The discovery of Spark
- spark
- RPC
keywords: 
- RPC
- spark
- spark RPC
- rpc 核心类
- rpc 核心类关系
draft: false
toc: true
---

The Discovery of Spark 系列目录：

1. [Saprk3.x Journey of Discovery | Spark RPC 框架的发展历史和RPC核心类图关系]()

---

开始 spark3.2.x 版本的源码分析，2023.4.27 开始！

## 1. Spark RPC 通信的作用

Spark 作为分布式的计算引擎，涉及非常多的地方需要进行网络通信，比如 spark 各个组件的消息通信、jar 包上传、shuffle 过程中节点间传输、Block 数据的广播等。

将所有的这些通信抽象出来，就和人体的框架类似，需要有管道结构进行各个器官（组件）的互通有无，将所有器官（组件）连接起来。在 spark 中，driver、executor、worker、master 等通信也是类似，通过 RPC（Remote Procedure Call） 框架实现。

spark 中通信举些例子：

- driver 和 master 通信，driver向master发送RegisterApplication消息
- master 和 worker 通信，worker向master上报worker上运行Executor信息
- executor 和 driver 通信，executor运行在worker上，spark的tasks被分发到运行在各个 executor中，executor需要通过向driver发送任务运行结果。
- worker 和 worker的通信，task运行期间需要从其他地方拿数据

在 spark 中，RPC 通信主要有两个作用：<u>**一是状态信息同步，比如 task 等变化信息；二是传输数据内容，比如 shuffle 过程中数据传输或者 board 过程中数据传输**</u>

## 2. Spark RPC 框架几个版本的迭代

在 spark1.6 版本之前，spark rpc 框架是基于 Akka 来实现。spark1.6 版本之后借鉴了 Akka 架构设计实现了基于 Netty 的 RPC 框架。原因详见以下Jira。

From 具体 jira [SPARK-5293: Enable Spark user applications to use different versions of Akka](https://issues.apache.org/jira/browse/SPARK-5293):

> A lot of Spark user applications are using (or want to use) Akka. Akka as a whole can contribute great architectural simplicity and uniformity. However, because Spark depends on Akka, it is not possible for users to rely on different versions, and we have received many requests in the past asking for help about this specific issue. For example, Spark Streaming might be used as the receiver of Akka messages - but our dependency on Akka requires the upstream Akka actors to also use the identical version of Akka.
> Since our usage of Akka is limited (mainly for RPC and single-threaded event loop), we can replace it with alternative RPC implementations and a common event loop in Spark.

核心意思是在 spark2.0 版本中移除 Akka 依赖，可以让用户使用任何版本的 Akka 来编程（Akka 是一款非常优秀的开源分布式系统，在一些 Java Application 或者 Java Web 可以利用 Akka 的丰富特性实现分布式一致性、最 一致性以及分布式事务等分布式环境面对的问题）。

现在 saprk3.2 的版本依然是基于 netty 的 rpc 框架（源码位于：spark-core 下的 rpc 目录），其中通过<u>`NettyStreamManager`**来进行文件、jar 上传等管理，基于 netty 的封装实现节点间的Shuffle 过程和 Block 数据的复制与备份**。</u>

## 3. Spark 的 RPC框架组成

spark3.2 基于 netty ，借鉴 Akka 框架设计和实现 RPC 框架。核心组件包括以下几个

``` scala
org/apache/spark/rpc/RpcTimeout.scala
org/apache/spark/rpc/RpcEnvStoppedException.scala
org/apache/spark/rpc/RpcEnv.scala
org/apache/spark/rpc/RpcEndpointRef.scala
org/apache/spark/rpc/RpcEndpointNotFoundException.scala
org/apache/spark/rpc/RpcEndpointAddress.scala
org/apache/spark/rpc/RpcEndpoint.scala
org/apache/spark/rpc/RpcCallContext.scala
org/apache/spark/rpc/RpcAddress.scala
org/apache/spark/rpc/netty/RpcEndpointVerifier.scala
org/apache/spark/rpc/netty/Outbox.scala
org/apache/spark/rpc/netty/NettyStreamManager.scala
org/apache/spark/rpc/netty/NettyRpcEnv.scala
org/apache/spark/rpc/netty/NettyRpcCallContext.scala
org/apache/spark/rpc/netty/MessageLoop.scala
org/apache/spark/rpc/netty/Inbox.scala
org/apache/spark/rpc/netty/Dispatcher.scala

其中列举其中比较重要的类和特征
0. private[spark] trait RpcEnvFactory
1. private[spark] abstract class RpcEnv(conf: SparkConf)
2. private[spark] case class RpcAddress(host: String, port: Int)
3. private[spark] abstract class RpcEndpointRef(conf: SparkConf)
4. private[netty] class NettyRpcEndpointRef(@transient private val conf: SparkConf,
private val endpointAddress: RpcEndpointAddress,@transient @volatile private var nettyEnv: NettyRpcEnv) 
extends RpcEndpointRef(conf)
5. private[netty] class NettyStreamManager(rpcEnv: NettyRpcEnv)
6. private[netty] class NettyRpcEnv(val conf: SparkConf,javaSerializerInstance: JavaSerializerInstance,
host: String,securityManager: SecurityManager,numUsableCores: Int)
```

核心的大致逻辑如下图

![Spark rpc 逻辑交互](https://media.techwhims.com/techwhims/2023/2023-05-01-07-15-49.png)
<center> figure 1: Spark RPC</center>

### 3.1 RpcEndpoint 和 RpcCallContext

RpcEndpoint 是一个响应请求的服务。在 spark 中可以表示为一个个需要通信的组件，如 master、worker、driver 等，根据接收到的消息进行处理，一个RpcEndpoint的生命周期是：

**构造->初始化启动->接收处理->停止（constructor -> onStart -> receive -> onStop）** 

这个RpcEndpoint 确保`onStart`, `receive` and `onStop`按照队列顺序执行。

RpcEndpoint中有 `def receive: PartialFunction[Any, Unit]`和`def receiveAndReply(context: RpcCallContext): PartialFunction[Any, Unit]` 两个关键的接收和回应消息的方法。

前者处理来自 `RpcEndpointRef.send` or `RpcCallContext.reply`的消息，后者处理来自`RpcEndpointRef.ask` 的消息并且进行回应。

RpcCallContext 实现RpcEndpoint的信息回调。

### 3.2 RpcEndpointRef

RpcEndpointRef，是远程 RpcEndpoint 的引用，持有远程 RpcEndpoint 的地址名称等，提供 send 方法和 ask 方法用于发送请求。

![RpcEndpointRef](https://media.techwhims.com/techwhims/2023/2023-04-28-19-30-01.png)

当我们需要向一个具体的 RpcEndpoint 发送 消息时，一般我们需要获取到该 RpcEndpoint 的引用，然后通过该引用发送消息。

### 3.3 RpcEnv 和 NettyRpcEnv

RpcEnv，服务端和客户端使用这个来通信，为 RpcEndpoint 提供处理消息的环境。

RpcEnv 负责 RpcEndpoint 整个生命周期的管理，包括：注册endpoint、endpoint 之间消息的路由、以及停止 endpoint。

对于 server 端来说，`RpcEnv 是 RpcEndpoint 的运行环境`，负责 RpcEndPoint 的生命周期管理， 解析 Tcp 层的数据包以及反序列化数据封装成 RpcMessage，然后根据路由传送到对应的 Endpoint

对于 client 端来说，可以`通过 RpcEnv 获取 RpcEndpoint 的引用`，也就是 RpcEndpointRef，然后通过 RpcEndpointRef 与对应的 Endpoint 通信

NettyRpcEnv 是继承 RpcEnv 的一个netty 的实现。

### 3.4 Dispatcher 、Inbox 和 Outbox

关联的技术点：

**NettyRpcEnv** 中包含 Dispatcher，主要针对服务端，帮助路由到指定的 RpcEndPoint，并调用起业务逻辑；包含NettyStreamManager， 负责文件、jar 上传等管理。

``` scala
// code in NettyRpcEnv
    private val dispatcher: Dispatcher = new Dispatcher(this, numUsableCores)

    private val streamManager = new NettyStreamManager(this)

```

**RPC端点** ，Spark针对于每个节点（Client/Master/Worker）都可以称之为一个Rpc端点,他们都实现RpcEndpoint接口，内部根据不同端点的需求，设计不同的消息和不同的业务处理，如果需要发送 （询问）则调用Dispatcher

关键点：

**Dispatcher：** 消息分发器，路由消息到不同的 RpcEndopint。针对于RPC端点需要发送消息或者从远程RPC接收到的消息，分发至对应的指令 收件箱/发件箱。如果指令接收方是自己存入收件箱，如果指令接收方为非自身端点，则放入发件箱。

**Inbox：** 指令消息收件箱，一个本地端点对应一个收件箱。
<!-- Dispatcher在每次向Inbox存入消息时，都将对应EndpointData加入内部待 Receiver Queue 中，另外Dispatcher创建时会启动一个单独线程进行轮询 Receiver Queue，进行收件箱消息消费 -->

**OutBox：** 指令消息发件箱，一个远程端点对应一个发件箱，当消息放入Outbox后，紧接着将消息通过 TransportClient 发送出去。消息放入发件箱以及发送过程是在同一个线程中进行，这样做的主要原因是远 程消息分为RpcOutboxMessage, OneWayOutboxMessage两种消息，而针对于需要应答的消息直接发送且需要得到结果进行处理

**TransportClient：** ，在 spark 底层网络包`network-common`中`org.apache.spark.network.client`，Netty通信客户端，被`TransportClientFactory`创建，根据OutBox消息的receiver信息，请求对应远程 TransportServer。 典型的工作流例子：

``` java
    For example, a typical workflow might be:
    client.sendRPC(new OpenFile("/foo")) --&gt; returns StreamId = 100
    client.fetchChunk(streamId = 100, chunkIndex = 0, callback)
    client.fetchChunk(streamId = 100, chunkIndex = 1, callback)
    ...
    client.sendRPC(new CloseStream(100))
```

**TransportServer：** Netty通信服务端，一个RPC端点一个TransportServer,接受远程消息后调用 Dispatcher分发消息至对应收发件箱

### 3.5 RpcAddress

远程的 RpcEndpointRef 的地址：Host + Port。

## 4. Spark3.x RPC 框架涉及到的核心类图关系

![Spark3.x RPC 框架核心类图关系](https://media.techwhims.com/techwhims/2023/spark-rpc.png)

关键点

- 核心的 RpcEnv 是一个 trait ，它主要提供了停止，注册，获取 endpoint 等方法的定义，而 NettyRpcEnv 提供了该接口类的一个具体实现。
- 通过工厂 RpcEnvFactory 来产生一个 RpcEnv，而 NettyRpcEnvFactory 用来生成 NettyRpcEnv 对象
- 当我们调用 RpcEnv 中的 setupEndpoint 来注册一个 endpoint 到 rpcEnv 的时候，在 NettyRpcEnv 内部，会将该 endpoint 的名称与其本身映射关系，rpcEndpoint 与 rpcEndpointRef 之间映射关系保存在 dispatcher 对应的成员变量中
- Master、Worker、BlockManager、HeartBeat 都是继承trait RpcEndpoint而来
- transportContext 作为 NettyRpcEnv 关键成员，承担 netty 底层交互信息的角色