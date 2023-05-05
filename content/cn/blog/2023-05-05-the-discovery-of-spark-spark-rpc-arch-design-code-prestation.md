---
title: "Saprk3.x Journey of Discovery | Spark RPC 架构设计和Akka架构以及基于Spark RPC框架的通信代码演示"
date: 2023-05-05
author: "张晓龙"
slug: spark-rpc-architecture-design-code-presentations
description: "Saprk3.x Journey of Discovery | Spark RPC 架构设计和Akka架构以及基于Spark RPC框架的通信代码演示"
categories: bigdata
tags: 
- The discovery of Spark
- spark
- RPC
- akka
keywords: 
- RPC
- spark
- spark RPC
- akka
- architecture
- presentations
- The discovery of Spark
draft: false
toc: true
---

The Discovery of Spark 系列目录：

1. [Saprk3.x Journey of Discovery | Spark 基础&重要的概念（base and important conception）](/cn/posts/spark-basic-conceptions/)
2. [Saprk3.x Journey of Discovery | Spark3.x 新特性 AQE的理解和介绍](/cn/posts/spark-aqe-intro-1/)
3. [Saprk3.x Journey of Discovery | Kyuubi1.7 Overview和部署核心参数调优](/cn/posts/kyuubi-overview-deploy-opt/)
4. [Saprk3.x Journey of Discovery | Spark RPC 框架的发展历史和RPC核心类图关系](/cn/posts/spark-rpc-history-core-class/)
5. [Saprk3.x Journey of Discovery | Spark 2.4 to 3.4 releases notes on spark core and SQL](/cn/posts/spark-version-release-notes/)
6. [Saprk3.x Journey of Discovery | Spark RPC 架构设计和Akka架构以及基于Spark RPC框架的通信代码演示](/cn/posts/spark-rpc-architecture-design-code-presentations/)

---

## 1. Akka 架构和Spark RPC 架构

我们在[上一篇文章](/cn/posts/spark-rpc-history-core-class/)中聊到 spark RPC 架构设计是参考 akka 架构设计的。那我们看下 Akka 是怎么样的？

### 1.1 Akka 是什么

Akka 是一个用 Scala 编写的库，用于在 JVM 平台上简化编写具有可容错的、高可伸缩性的 Java 和 Scala 的 Actor 模型应用。其同时提供了Java 和 Scala 的开发接口。

Akka 允许专注于满足业务需求，而不是编写初级代码。**在 Akka 中，Actor 之间通信的唯一机制就是消息传递**。

Akka 对 Actor 模型的使用提供了一个抽象级别，使得编写正确的并发、并行和分布式系统更加容易。

更详细的可以看一下官网：[akka.io](https://akka.io/)

或者 YouTube The Power of Akka in 1 min：

{{< youtube id="ViE4oLozicQ" title="The Power of Akka in 1 min" >}}

**Akka 系统中最重要的三个概念： ActorSystem、 Actor、 ActorRef**

ActorSystem：管理通信角色 actor 的一个系统概念，在一个服务器节点中，只要存在一个这样的对象就可以，这个对象的作用，就是用来生成和管理所有的 通信角色的生命周期

Actor：存在于一台服务器中的一个 ActorSystem 的内部，用来和其他节点的 actor 进行通信。每个 Actor 都有一个 MailBox，别的 Actor 发送给它的消息都首先储存在 MailBox 中，通过这种方式可以实现异步通信。

- 每个 Actor 是单线程的处理方式，不断的从 MailBox 拉取消息执行处理，所以对于 Actor 的消息处理，不适合调用会阻塞的处理方法。
- Actor 可以改变他自身的状态，可以接收消息，也可以发送消息，还可以生成新的 Actor
- 每一个 ActorSystem 和 Actor都在启动的时候会给定一个 name，如果要从 ActorSystem 中，获取一个 Actor，则通过以下的方式来进行 Actor 的 获取：akka.tcp://asname@bigdata02:9527/user/actorname
- 如果一个 Actor 要和另外一个 Actor 进行通信，则必须先获取对方 Actor 的 ActorRef 对象，然后通过该对象发送消息即可。
- 通过 tell 发送异步消息，不接收响应，通过 ask 发送异步消息，得到 Future 返回，通过异步回到返回处理结果

![Akka-system](https://media.techwhims.com/techwhims/2023/Akka-system.png)

> Spark-1.x 版本中的应用程序执行的时候，会生成给一个 Driver 和 多个 Executor 。 它的内部就有两个 Actor：
> 1、DriverActor： 负责发送任务给其他的 worker 中的 executor 来执行的，作用和 Spark-2.x 版本中的 DriverEndpoint 是一样的
> 2、ClientActor： 负责和 master 进行通信，作用和 Spark-2.x 版本中的 ClientEndpoint 是一样的

## 2. Spark 集群的 RPC 通信组件实现

上面介绍可 Akka ，总结来看有以下三个特点

- 是对并发模型进行了更高的抽象
- 是异步、非阻塞、高性能的事件驱动编程模型
- 是轻量级事件处理(1GB 内存可容纳百万级别个Actor);

Spark1.x 版本RPC通信组件采用 Actor 模型，spark2.x 版本以后，RPC通信组件RpcEndpoint模型。

Spark-1.x 中，用户文件和 jar 包上传，采用 jetty 实现的 HttpFileServer 实现的，Spark-2.x 废弃了，现在使用基于 Spark 内置 RPC 框架 NettyStreamManager

Shuffle 过程 和 Block 数据复制和备份在 Spark-2.x 版本依然沿用 Netty，通过对接口和程序的重新设计，将各个组件间的消息互通，用户文件和 jar 包的上传也一并纳入 Spark 的 RPC 框架。

根据上一篇文章内容，进一步总结如下

- **Spark RPC 客户端的具体实现是 TransportClient**，由 TransportClientFactory 创建，TransportClientFactory 在实例化的时候需要 TransportConf，创建好了之后通过 TransportClientBootstrap 引导启动，创建好的 TransportClient 都会被维护在 TransportClientFactory 的 ClientPool 中
- **Spark RPC 服务端的具体实现是 TransportServer**，创建的时候需要 TransportContext 中的 TransportConf 和 RpcHandler。在 init 初始 化的时候，由 TransportServerBootStrap 引导启动
- 在 Spark RPC 过程中，实现具体的编解码动作的是： **MessageEncoder 和 MessageDecoder**。可以集成多种不同的序列化机制

我们提到Spark-2.x 基于 netty 的 RPC 框架借鉴了Akka 的设计，基于 Actor 模型，各个组件可以认为是一个个独立的实体，各个实体之间通过消息来进行通信。

可以类比为：

- akka      ：ActorSystem   + Actor         + ActorRef
- spark rpc ：RpcEnv        + RpcEndpoint   + RpcEndpointRef

## 3. 使用 Akka 框架实现网络通信代码实例

我们使用 akka 框架实现一个简单的 spark rpc 通信案例。这个 demo 实现公共 4 个scala 文件。

- AkkaSparkMaster.scala
- AkkaSparkWorker.scala
- AkkaSparkWorkerInfo.scala
- Constant.scala

可以建一个简单maven 工程，更多细节详见代码

### 3.1 pom 中重要的依赖，**特别注意 scala-actor 和下面 akka 版本的匹配**，否则运行不起来

``` xml
<dependencies>
        <dependency>
            <groupId>org.scala-lang</groupId>
            <artifactId>scala-library</artifactId>
            <version>2.11.8</version>
        </dependency>
        <dependency>
            <groupId>org.scala-lang</groupId>
            <artifactId>scala-actors</artifactId>
            <version>2.11.8</version>
        </dependency>
        <dependency>
            <groupId>com.typesafe.akka</groupId>
            <artifactId>akka-actor_2.11</artifactId>
            <version>2.4.17</version>
        </dependency>
        <dependency>
            <groupId>com.typesafe.akka</groupId>
            <artifactId>akka-remote_2.11</artifactId>
            <version>2.4.17</version>
        </dependency>
    </dependencies>
```

### 3.2 spark master 代码实现

``` scala
package org.example;


import akka.actor.{Actor, ActorSystem, Props, actorRef2Scala}
import com.typesafe.config.ConfigFactory

import java.util.concurrent.TimeUnit
import scala.collection.mutable
import scala.concurrent.duration.FiniteDuration;

/**
 * @Author Allen Zhang
 * @Date 2023/5/4 17:12
 * @Description mocking Spark master rpc communication
 * 1.override receive method，achieve other actor msg, and match case process
 **/
class AkkaSparkMaster(var hostname: String, var port:Int) extends Actor {

    // store registered worker info to map
    private var id2AkkaSparkWorkerInfoMap = new mutable.HashMap[String, AkkaSparkWorkerInfo]()

    // execute once when actor start first
    override def preStart(): Unit = {
        import context.dispatcher

        context.system.scheduler.schedule(new FiniteDuration(0,TimeUnit.MILLISECONDS), new FiniteDuration(5000,TimeUnit
          .MILLISECONDS), self, CheckTimeOut)
    }

    // core!!!
    override def receive: Receive = {
          // receive register msg
        case RegisterAkkaSparkWorker(workerId,memory,cpu) => {
            val akkaSparkWorkerInfo = new AkkaSparkWorkerInfo(workerId, memory, cpu)
            println(s"node ${workerId} online!")

            id2AkkaSparkWorkerInfoMap.put(workerId, akkaSparkWorkerInfo)

            // store msg info to zk(maybe)
            sender() ! RegisteredAkkaSparkWorker(hostname + ":" + port)
        }

        // receive heartbeat msg
        case HeartBeat(workerId) => {
            val currentTime = System.currentTimeMillis()
            val akkaSparkWorkerInfo = id2AkkaSparkWorkerInfoMap(workerId)

            akkaSparkWorkerInfo.lastHeartBeatTime = currentTime

            id2AkkaSparkWorkerInfoMap(workerId) = akkaSparkWorkerInfo
        }

        //receive checkout signal : check invalid nodeManager since 15s expire
        case CheckTimeOut => {
            val currentTime = System.currentTimeMillis()

            var sparkWorkerInfoSet = id2AkkaSparkWorkerInfoMap.values.toSet
            sparkWorkerInfoSet.filter(workerInfo => {
                val heartbeatTimeOut = 15000
                val bool = currentTime - workerInfo.lastHeartBeatTime > heartbeatTimeOut
                if (bool) {
                    println(s"${workerInfo.workerId} offline")
                }
                bool
            }).foreach(deadWorker =>{
                sparkWorkerInfoSet -= deadWorker
                id2AkkaSparkWorkerInfoMap.remove(deadWorker.workerId)
            })

            println("Current registered node count : " + sparkWorkerInfoSet.size + " node info : " +
              sparkWorkerInfoSet.map(x=>x.toString).mkString(","))
        }
    }
}

object AkkaResourceManager {

    def main(args: Array[String]):Unit ={
        val str =
            """
              |akka.actor.provider = "akka.remote.RemoteActorRefProvider"
              |akka.remote.netty.tcp.hostname = localhost
              |akka.remote.netty.tcp.port = 5678
              """.stripMargin
        val conf = ConfigFactory.parseString(str)

        print(conf)

        val actorSystem = ActorSystem(Constant.SMAS, conf)

        // create a actor named :  SparkMasterActor, and start
        actorSystem.actorOf(Props(new AkkaSparkMaster("localhost",5678)),Constant.SMA)
    }
}

```

### 3.3 spark worker 代码实现

``` scala
package org.example

import akka.actor.{Actor, ActorSelection, ActorSystem, Props}
import com.typesafe.config.ConfigFactory

import java.util.concurrent.TimeUnit
import scala.concurrent.duration.FiniteDuration

class AkkaSparkWorker(val workerHostName:String, val masterHostName: String, val masterPort: Int, val memory: Int,
val cpu:Int) extends Actor{

  var sparkWorkerId:String = workerHostName
  var sparkMasterRef:ActorSelection=_

  // execute when start,
  // register nm to rm
  override def preStart(): Unit = {
    sparkMasterRef = context.actorSelection(s"akka.tcp://${Constant.SMAS}@${masterHostName}:${masterPort}/user/${Constant.SMA}")

    // send message
    println(sparkWorkerId +" start register!")
    sparkMasterRef ! RegisterAkkaSparkWorker(workerId = sparkWorkerId, memory = memory, cpu = cpu)
  }

  // core service!
  override def receive: Receive = {
    case RegisteredAkkaSparkWorker(masterUrl)=>{
      println("masterUrl : " + masterUrl)

      import context.dispatcher
      // receiver : self , actorRef
      // message: SendMessage
      context.system.scheduler.schedule(new FiniteDuration(0,TimeUnit.MILLISECONDS),new FiniteDuration(5000,TimeUnit
        .MILLISECONDS),self,SendMessage)
    }
    case SendMessage=>{
      sparkMasterRef ! HeartBeat(workerId = sparkWorkerId)
      println("current thread id : " + Thread.currentThread().getId)
    }
  }
}

object SparkWorker{

  def main(args: Array[String]): Unit = {
    val remoteHostName = args(0)

    val sparkMasterHostname= args(1)
    val sparkMasterPort = args(2).toInt

    val sparkWorkerMemory = args(3).toInt
    val sparkWorkerCores = args(4).toInt

    val sparkWorkerPort = args(5).toInt
    val sparkWorkerHostname = args(6)

    val str =
      """
        |akka.actor.provider = "akka.remote.RemoteActorRefProvider"
        |akka.remote.netty.tcp.hostname = "localhost"
        |akka.remote.netty.tcp.port = 6789
        """.stripMargin

    val conf = ConfigFactory.parseString(str)

    print(conf)
    val actorSystem = ActorSystem(Constant.SWAS, conf)

    actorSystem.actorOf(Props(new AkkaSparkWorker(sparkWorkerHostname,sparkMasterHostname,sparkMasterPort,
      sparkWorkerMemory,sparkWorkerCores)),Constant.SWA)
  }

}
```

### 3.4 Constant 常量

``` scala
package org.example

// message class
object Constant {
  val SMAS = "SparkMasterActorSystem"
  val SMA = "SparkMasterActor"
  val SWAS = "SparkWorkerActorSystem"
  val SWA = "SparkWorkerActor"
}
```

### 3.5 启动运行spark master 、 spark worker 并且进行通信

1、spark master启动运行，并且在端口 5678 运行

``` bash
[INFO] [05/04/2023 22:59:08.451] [main] [akka.remote.Remoting] Starting remoting
[INFO] [05/04/2023 22:59:08.624] [main] [akka.remote.Remoting] Remoting started; listening on addresses :[akka.tcp://SparkMasterActorSystem@localhost:5678]
[INFO] [05/04/2023 22:59:08.625] [main] [akka.remote.Remoting] Remoting now listens on addresses: [akka.tcp://SparkMasterActorSystem@localhost:5678]
Current registered node count : 0 node info : 
```

2、Spark worker 启动运行，**需要设置运行参数**：`localhost localhost 5678 512 32 6789 worker1` ， 启动运行

``` bash
[INFO] [05/04/2023 23:01:15.870] [main] [akka.remote.Remoting] Starting remoting
[INFO] [05/04/2023 23:01:16.026] [main] [akka.remote.Remoting] Remoting started; listening on addresses :[akka.tcp://SparkWorkerActorSystem@localhost:6789]
[INFO] [05/04/2023 23:01:16.027] [main] [akka.remote.Remoting] Remoting now listens on addresses: [akka.tcp://SparkWorkerActorSystem@localhost:6789]
worker1 start register!
[WARN] [SECURITY][05/04/2023 23:01:16.296] [SparkWorkerActorSystem-akka.remote.default-remote-dispatcher-13] [akka.serialization.Serialization(akka://SparkWorkerActorSystem)] Using the default Java serializer for class [org.example.RegisterAkkaSparkWorker] which is not recommended because of performance implications. Use another serializer or disable this warning using the setting 'akka.actor.warn-about-java-serializer-usage'
masterUrl : localhost:5678
current thread id : 22
[WARN] [SECURITY][05/04/2023 23:01:16.388] [SparkWorkerActorSystem-akka.remote.default-remote-dispatcher-5] [akka.serialization.Serialization(akka://SparkWorkerActorSystem)] Using the default Java serializer for class [org.example.HeartBeat] which is not recommended because of performance implications. Use another serializer or disable this warning using the setting 'akka.actor.warn-about-java-serializer-usage'
current thread id : 22
```

这时候 worker 和 master 进行通信,每 5s 向 master 汇报一次message

``` bash
Current registered node count : 0 node info : 
node worker1 online!
[WARN] [SECURITY][05/04/2023 23:01:16.367] [SparkMasterActorSystem-akka.remote.default-remote-dispatcher-17] [akka.serialization.Serialization(akka://SparkMasterActorSystem)] Using the default Java serializer for class [org.example.RegisteredAkkaSparkWorker] which is not recommended because of performance implications. Use another serializer or disable this warning using the setting 'akka.actor.warn-about-java-serializer-usage'
Current registered node count : 1 node info : worker1,512,32
Current registered node count : 1 node info : worker1,512,32
Current registered node count : 1 node info : worker1,512,32
Current registered node count : 1 node info : worker1,512,32

手动杀掉 worker 后，master 显示节点下线

Current registered node count : 1 node info : worker1,512,32
[WARN] [05/04/2023 23:11:21.605] [SparkMasterActorSystem-akka.remote.default-remote-dispatcher-13] [akka.tcp://SparkMasterActorSystem@localhost:5678/system/endpointManager/reliableEndpointWriter-akka.tcp%3A%2F%2FSparkWorkerActorSystem%40localhost%3A6789-0] Association with remote system [akka.tcp://SparkWorkerActorSystem@localhost:6789] has failed, address is now gated for [5000] ms. Reason: [Disassociated] 
Current registered node count : 1 node info : worker1,512,32
Current registered node count : 1 node info : worker1,512,32
worker1 offline
Current registered node count : 0 node info : 
```

至此，基于 akka 的 Spark RPC 通信案例完毕！

## 4. 使用 Spark 的 RPC 框架实现网络通信代码案例

Spark-2.x 基于 netty 的 RPC 框架借鉴了Akka 的设计，基于 Actor 模型，各个组件可以认为是一个个独立的实体，各个实体之间通过消息来进行通信。

Spark RPC 结构 ：RpcEnv + RpcEndpoint + RpcEndpointRef （对比 akka：ActorSystem + Actor + ActorRef）

我们设计一个简单利用 spark rpc 通信的例子，大致的结构：

- 服务端 EpcEnv **（背后是 TransportServer）**, 启动 Endpoint
- 客户端 EpcEnv **（背后是 TransportClient）**, 获取 EndPointRef
- 客户端 EndPointRef 通过三个方法发送消息给服务端 Endpoint
  - send
  - ask
  - askSync
- 服务端 SayHiEndpoint 服务进行请求处理，然后返回消息

该例子是 maven 工程，包含以下几个重要的文件

- SayHiEndpoint.scala
- SayHiSettings.scala
- SparkRpcClientMain.scala
- SparkRpcServerMain.scala

### 4.1 pom 重要依赖

``` xml
   <dependencies>
        <!-- https://mvnrepository.com/artifact/org.apache.spark/spark-core -->
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-core_2.11</artifactId>
            <version>2.4.6</version>
        </dependency>
        <!-- https://mvnrepository.com/artifact/org.apache.spark/spark-network-common -->
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-network-common_2.13</artifactId>
            <version>3.2.1</version>
        </dependency>
        <!-- https://mvnrepository.com/artifact/org.apache.spark/spark-sql -->
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-sql_2.11</artifactId>
            <version>2.4.6</version>
        </dependency>
    </dependencies>
```

### 4.2 SparkRPC Server code

``` scala
package org.apache.spark

import org.apache.spark.rpc.{RpcEndpoint, RpcEnv}
import org.apache.spark.sql.SparkSession

// Spark RPC server
object SparkRpcServerMain {

  def main(array: Array[String]): Unit= {

    val conf: SparkConf = new SparkConf()

    val sparkSession = SparkSession.builder().config(conf).master("local[*]").appName("Say Hi RPC").getOrCreate()
    val sparkContext: SparkContext = sparkSession.sparkContext
    val sparkEnv: SparkEnv = sparkContext.env

    /**
     * def create(
     * name: String,
     * bindAddress: String,
     * advertiseAddress: String,
     * port: Int,
     * conf: SparkConf,
     * securityManager: SecurityManager,
     * numUsableCores: Int,
     * clientMode: Boolean): RpcEnv
     */
    val rpcEnv = RpcEnv.create(SayHiSettings.getName(), SayHiSettings.getHostname(), SayHiSettings.getHostname(),
      SayHiSettings.getPort(), conf, sparkEnv.securityManager, 1, false)

    val saiHiEndpoint: RpcEndpoint = new SayHiEndpoint(rpcEnv)

    rpcEnv.setupEndpoint(SayHiSettings.getName(), saiHiEndpoint)

    rpcEnv.awaitTermination()
  }
}

```

### 4.3 SparkRPC Client code

``` scala
package org.apache.spark

import org.apache.spark.rpc.{RpcAddress, RpcEndpointRef, RpcEnv}
import org.apache.spark.sql.SparkSession

import scala.concurrent.duration.Duration
import scala.concurrent.{Await, Future}

// Spark RPC server
object SparkRpcClientMain {

  def main(array: Array[String]): Unit= {

    val conf: SparkConf = new SparkConf()

    val sparkSession = SparkSession.builder().config(conf).master("local[*]").appName("Say Hi to RPC Server")
      .getOrCreate()

    val sparkContext: SparkContext = sparkSession.sparkContext

    val sparkEnv: SparkEnv = sparkContext.env

    /**
    def create(
      name: String,
      host: String,
      port: Int,
      conf: SparkConf,
      securityManager: SecurityManager,
      clientMode: Boolean = false)
     */
    val rpcEnv = RpcEnv.create(SayHiSettings.getName(), SayHiSettings.getHostname(),
      SayHiSettings.getPort(), conf, sparkEnv.securityManager,false)

    val endpointRef:RpcEndpointRef = rpcEnv.setupEndpointRef(RpcAddress(SayHiSettings.getHostname(),SayHiSettings
      .getPort()), SayHiSettings.getName())

    // async send
    endpointRef.send(SayHi("hi , i am client allen."))

    import scala.concurrent.ExecutionContext.Implicits.global
    // ask , response value before time out
    val future:Future[String] = endpointRef.ask[String](SayHi(s"ask: hi , i am client allen."))
    future.onComplete {
      case scala.util.Success(value) => println(s"get msg form server : ${value}")
      case scala.util.Failure(exception) => println(s"get msg form server error : ${exception}")
    }

    Await.result(future,Duration.apply("30s"))

    val res = endpointRef.askSync[String](SayBye("i am allen ,and bye!"))

    println(res)

    sparkSession.stop()
  }
}

```

### 4.4 SparkRPC endpoint 实现

``` scala
package org.apache.spark

import org.apache.spark.rpc.{RpcCallContext, RpcEndpoint, RpcEnv}

// service core
class SayHiEndpoint(override val rpcEnv: RpcEnv) extends RpcEndpoint {

  override def onStart(): Unit = {
    println(rpcEnv.address)
    println("start SayHiEndpoint")
  }

  override def receive: PartialFunction[Any, Unit] = {
    case SayHi(msg) => println(s"Receive msg : ${msg}")
  }

  override def receiveAndReply(context: RpcCallContext): PartialFunction[Any, Unit] = {
    case SayHi(msg) => {
      println(s"Receive msg : ${msg}")
      context.reply(s"i am SayHi Server,${msg}")
    }

    case SayBye(msg) => {
      println(s"Receive msg : ${msg}")
      context.reply(s"i am SayHi Server,${msg}")
    }
  }

  override def onStop():Unit = {
    println("Stop SayHiEndpoint")
  }
}

case class SayHi(msg: String)

case class SayBye(msg: String)

```

### 4.5 Spark Common Utils

``` scala
package org.apache.spark

object SayHiSettings {

  val rpcName: String = "say-hi-service"
  val port: Int = 5678
  val hostname: String = "localhost"

  def getName() = {
    rpcName
  }

  def getPort()={
    port
  }

  def getHostname()={
    hostname
  }

  override def toString = s"SayHiSettings($rpcName, $port, $hostname)"
}
```

### 4.6 运行实例

运行代码之前特别注意的点 ： **代码的package名字，必须为org.xxx.spark，否则引入的 RpcEndpoint、RpcEnv等等不能引用（源于源码package限制）**

1、启动 sparkRpcServer

``` bash
23/05/05 12:17:51 INFO SparkContext: Running Spark version 2.4.6
23/05/05 12:17:51 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
23/05/05 12:17:52 INFO SparkContext: Submitted application: Say Hi RPC
23/05/05 12:17:52 INFO SecurityManager: Changing view acls to: wdzxl198
23/05/05 12:17:52 INFO SecurityManager: Changing modify acls to: wdzxl198
23/05/05 12:17:52 INFO SecurityManager: Changing view acls groups to: 
23/05/05 12:17:52 INFO SecurityManager: Changing modify acls groups to: 
23/05/05 12:17:52 INFO SecurityManager: SecurityManager: authentication disabled; ui acls disabled; users  with view permissions: Set(wdzxl198); groups with view permissions: Set(); users  with modify permissions: Set(wdzxl198); groups with modify permissions: Set()
23/05/05 12:17:52 INFO Utils: Successfully started service 'sparkDriver' on port 63840.
23/05/05 12:17:52 INFO SparkEnv: Registering MapOutputTracker
23/05/05 12:17:52 INFO SparkEnv: Registering BlockManagerMaster
23/05/05 12:17:52 INFO BlockManagerMasterEndpoint: Using org.apache.spark.storage.DefaultTopologyMapper for getting topology information
23/05/05 12:17:52 INFO BlockManagerMasterEndpoint: BlockManagerMasterEndpoint up
23/05/05 12:17:52 INFO DiskBlockManager: Created local directory at /private/var/folders/lr/dgy9yr3s759_6cpp7k28k2300000gq/T/blockmgr-e1d0eb47-0f5d-4169-af02-942649ebf366
23/05/05 12:17:52 INFO MemoryStore: MemoryStore started with capacity 4.1 GB
23/05/05 12:17:52 INFO SparkEnv: Registering OutputCommitCoordinator
23/05/05 12:17:52 INFO Utils: Successfully started service 'SparkUI' on port 4040.
23/05/05 12:17:52 INFO SparkUI: Bound SparkUI to 0.0.0.0, and started at http://172.xx.xx.xx:4040
23/05/05 12:17:53 INFO Executor: Starting executor ID driver on host localhost
23/05/05 12:17:53 INFO Utils: Successfully started service 'org.apache.spark.network.netty.NettyBlockTransferService' on port 63841.
23/05/05 12:17:53 INFO NettyBlockTransferService: Server created on 172.xx.xx.xx:63841
23/05/05 12:17:53 INFO BlockManager: Using org.apache.spark.storage.RandomBlockReplicationPolicy for block replication policy
23/05/05 12:17:53 INFO BlockManagerMaster: Registering BlockManager BlockManagerId(driver, 172.xx.xx.xx, 63841, None)
23/05/05 12:17:53 INFO BlockManagerMasterEndpoint: Registering block manager 172.xx.xx.xx:63841 with 4.1 GB RAM, BlockManagerId(driver, 172.xx.xx.xx, 63841, None)
23/05/05 12:17:53 INFO BlockManagerMaster: Registered BlockManager BlockManagerId(driver, 172.xx.xx.xx, 63841, None)
23/05/05 12:17:53 INFO BlockManager: Initialized BlockManager: BlockManagerId(driver, 172.xx.xx.xx, 63841, None)
23/05/05 12:17:53 INFO Utils: Successfully started service 'say-hi-service' on port 5678.
localhost:5678
start SayHiEndpoint
```

2、启动 sparkRpcClient

``` bash
23/05/05 12:19:23 INFO SparkContext: Running Spark version 2.4.6
23/05/05 12:19:23 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
23/05/05 12:19:23 INFO SparkContext: Submitted application: Say Hi to RPC Server
23/05/05 12:19:23 INFO SecurityManager: Changing view acls to: wdzxl198
23/05/05 12:19:23 INFO SecurityManager: Changing modify acls to: wdzxl198
23/05/05 12:19:23 INFO SecurityManager: Changing view acls groups to: 
23/05/05 12:19:23 INFO SecurityManager: Changing modify acls groups to: 
23/05/05 12:19:23 INFO SecurityManager: SecurityManager: authentication disabled; ui acls disabled; users  with view permissions: Set(wdzxl198); groups with view permissions: Set(); users  with modify permissions: Set(wdzxl198); groups with modify permissions: Set()
23/05/05 12:19:24 INFO Utils: Successfully started service 'sparkDriver' on port 63877.
23/05/05 12:19:24 INFO SparkEnv: Registering MapOutputTracker
23/05/05 12:19:24 INFO SparkEnv: Registering BlockManagerMaster
23/05/05 12:19:24 INFO BlockManagerMasterEndpoint: Using org.apache.spark.storage.DefaultTopologyMapper for getting topology information
23/05/05 12:19:24 INFO BlockManagerMasterEndpoint: BlockManagerMasterEndpoint up
23/05/05 12:19:24 INFO DiskBlockManager: Created local directory at /private/var/folders/lr/dgy9yr3s759_6cpp7k28k2300000gq/T/blockmgr-c478391a-1fe2-4433-a204-5b225d360a3e
23/05/05 12:19:24 INFO MemoryStore: MemoryStore started with capacity 4.1 GB
23/05/05 12:19:24 INFO SparkEnv: Registering OutputCommitCoordinator
23/05/05 12:19:24 WARN Utils: Service 'SparkUI' could not bind on port 4040. Attempting port 4041.
23/05/05 12:19:24 INFO Utils: Successfully started service 'SparkUI' on port 4041.
23/05/05 12:19:24 INFO SparkUI: Bound SparkUI to 0.0.0.0, and started at http://172.xx.xx.xx:4041
23/05/05 12:19:24 INFO Executor: Starting executor ID driver on host localhost
23/05/05 12:19:24 INFO Utils: Successfully started service 'org.apache.spark.network.netty.NettyBlockTransferService' on port 63878.
23/05/05 12:19:24 INFO NettyBlockTransferService: Server created on 172.xx.xx.xx:63878
23/05/05 12:19:24 INFO BlockManager: Using org.apache.spark.storage.RandomBlockReplicationPolicy for block replication policy
23/05/05 12:19:24 INFO BlockManagerMaster: Registering BlockManager BlockManagerId(driver, 172.xx.xx.xx, 63878, None)
23/05/05 12:19:24 INFO BlockManagerMasterEndpoint: Registering block manager 172.xx.xx.xx:63878 with 4.1 GB RAM, BlockManagerId(driver, 172.xx.xx.xx, 63878, None)
23/05/05 12:19:24 INFO BlockManagerMaster: Registered BlockManager BlockManagerId(driver, 172.xx.xx.xx, 63878, None)
23/05/05 12:19:24 INFO BlockManager: Initialized BlockManager: BlockManagerId(driver, 172.xx.xx.xx, 63878, None)
23/05/05 12:19:24 WARN Utils: Service 'say-hi-service' could not bind on port 5678. Attempting port 5679.
23/05/05 12:19:24 INFO Utils: Successfully started service 'say-hi-service' on port 5679.
23/05/05 12:19:24 INFO TransportClientFactory: Successfully created connection to localhost/127.0.0.1:5678 after 45 ms (0 ms spent in bootstraps)
```

3、进行通信测试

server端：

``` bash
Receive msg : hi , i am client allen.
Receive msg : ask: hi , i am client allen.
Receive msg : i am allen ,and bye!
```

client 端:

``` bash
get msg form server : i am SayHi Server,ask: hi , i am client allen.
i am SayHi Server,i am allen ,and bye!
```

至此，利用 spark 自己实现的 SparkRPC 框架进行通信演示完毕。