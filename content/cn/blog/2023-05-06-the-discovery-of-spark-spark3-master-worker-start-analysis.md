---
title: "Saprk3.x Journey of Discovery | Spark3.x 主节点 Master 和 Worker 节点 启动过程分析"
date: 2023-05-06
author: "张晓龙"
slug: spark-master-worker-launch-analysis
description: "Saprk3.x Journey of Discovery | Spark3.x 主节点 Master 和 Worker 节点 启动过程分析"
categories: bigdata
tags: 
- The discovery of Spark
- spark
keywords: 
- RPC
- spark
- master
- worker
- The discovery of Spark
draft: false
toc: true
---

{{< vpost tagx="tags/the-discovery-of-spark" >}}

---

今天开始学习 spark master 和 worker 启动过程。首先本文进行主节点 Master 的启动分析

## 1. 前置知识点介绍

Spark 架构体系中各个专有名词的解释。

> 1. Master 和 Worker 概念 ： 集群的主从节点角色
> 2. Driver、Executor 概念：
>   driver: 负责任务的调度和监控
>   executor: 负责任务的执行
>   用户提交Application一个，就会启动一个Driver + N个 Executor
> 3. Application、Job、Stage、Task
>   Application：完整的用来实现某个业务的一个完成的程序：一个jar包中的带main方法的一个类
>   Job：由这个application中的action算子来决定到底有多少个job, 一个action会生成一个job
>   Stage：一个job按照shuffle依赖切分成多个stage
>   Task：stage中的可以并行运行的任务

![spark-master-worker](https://media.techwhims.com/techwhims/2023/2023-05-05-19-30-09.png)

## 2. Spark 集群启动 shell 脚本的分析

集群启动是 start-all.sh 脚本，在spark3 项目根目录 sbin目录， 这个下面有很多脚本，启动我们需要关注的不多

启动关联关系如下图所示：

![spark-start](https://media.techwhims.com/techwhims/2023/spark-start.jpg)

start-all.sh脚本开始，加载环境变量，然后分别调用 start-master.sh、start-workers.sh 分别启动 master 和 worker。

这两个脚本调用到最后是调用bin/spark-class org.apache.spark.launcher.Main，用这个类加载各自的启动 main 方法。

<u>
Master 的主类：org.apache.spark.deploy.master.Master

Worker 的主类：org.apache.spark.deploy.worker.Worker**
</u>

## 3. Spark Master 启动过程分析

知道进入的主类`org.apache.spark.deploy.master.Master`，剩下的就是分析启动过程。

首先从 main() 方法开始。

``` scala

//以下以截取关键代码 + 注释的方式分析

 // start!
 def main(argStrings: Array[String]): Unit
    // 1. 启动 RpcEnv 和 RpcEndpoint，返回一个 tuple（RpcEnv\web ui port \ rest server port）
    val (rpcEnv, _, _) = startRpcEnvAndEndpoint(args.host, args.port, args.webUiPort, conf)
        // 2. create a rpcEnv
        val rpcEnv = RpcEnv.create(SYSTEM_NAME, host, port, conf, securityMgr)
        // 3. 启动 rpcEndpoint
        val masterEndpoint = rpcEnv.setupEndpoint(ENDPOINT_NAME,new Master(rpcEnv, rpcEnv.address, webUiPort, securityMgr, conf))
            //4. 构造 Master
            new Master(override val rpcEnv: RpcEnv,address: RpcAddress,webUiPort: Int,val securityMgr: SecurityManager,val conf: SparkConf) extends ThreadSafeRpcEndpoint
                // 关键私有变量
                val workers = new HashSet[WorkerInfo]
                val idToApp = new HashMap[String, ApplicationInfo]
                private val waitingApps = new ArrayBuffer[ApplicationInfo]
                val apps = new HashSet[ApplicationInfo]
                private val drivers = new HashSet[DriverInfo]
                private val waitingDrivers = new ArrayBuffer[DriverInfo]
                // After onStart, webUi will be set
                private var webUi: MasterWebUI = null
                private var persistenceEngine: PersistenceEngine = _
                private var leaderElectionAgent: LeaderElectionAgent = _
            // 5. rpcEnv 生命周期：onStart 方法（setupEndpoint 注册 endpoint，在dispatcher中registerRpcEndpoint放入两个Map中，同时返回endpointRef）
            Master.onStart()
                // 6. 构造 webUI
                webUi = new MasterWebUI(this, webUiPort)
                // 绑定
                webUi.bind()
                // 7. 定时调度，检查 worker 是否挂掉了（timeout），验活 （forwardMessageThread name: “master-forward-message-thread”）
                checkForWorkerTimeOutTask = forwardMessageThread.scheduleAtFixedRate(() => Utils.tryLogNonFatalError { self.send(CheckForWorkerTimeOut) },0,workerTimeoutMs, TimeUnit.MILLISECONDS)
                    // 7.1 特殊路径，rpcEndpoint 接受到 worker 的 message：CheckForWorkerTimeOut
                    Master.receive()
                        case CheckForWorkerTimeOut => timeOutDeadWorkers()
                            // timeOutDeadWorkers :Check for, and remove, any timed-out workers
                            val toRemove = workers.filter(_.lastHeartbeat < currentTime - workerTimeoutMs).toArray
                            for (worker <- toRemove) {
                                if (worker.state != WorkerState.DEAD)
                                    removeWorker(worker, s"Not receiving heartbeat for $workerTimeoutSecs seconds")
                                else 
                                    if (worker.lastHeartbeat < currentTime - ((reaperIterations + 1) * workerTimeoutMs)) {
                                        workers -= worker // we've seen this DEAD worker in the UI, etc. for long enough; cull it
                // 8. 如果开启 restserver，则启动
                restServer = Some(new StandaloneRestServer(address.host, port, conf, self, masterUrl))
                // 9. metrics 服务启动
                masterMetricsSystem \ applicationMetricsSystem 启动
                // 10. 持久化引擎 和 选agent
                // PersistenceEngine : Allows Master to persist any state that is necessary in order to recover from a failure.
                // LeaderElectionAgent : A LeaderElectionAgent tracks current master and is a common interface for all election Agents.
                val (persistenceEngine_, leaderElectionAgent_) = recoveryMode match {
                     case "ZOOKEEPER" =>
                        val zkFactory = new ZooKeeperRecoveryModeFactory(conf, serializer) (zkFactory.createPersistenceEngine(), zkFactory.createLeaderElectionAgent(this))
                            // 11. createPersistenceEngine()
                            new ZooKeeperPersistenceEngine(conf, serializer)
                                // create zk node , 路径：/spark/master_status
                                private val workingDir = conf.get(ZOOKEEPER_DIRECTORY).getOrElse("/spark") + "/master_status"
                                private val zk: CuratorFramework = SparkCuratorUtil.newClient(conf)
                                // create path: /spark/master_status
                                SparkCuratorUtil.mkdir(zk, workingDir)
                            // 12. createLeaderElectionAgent(this)
                            new ZooKeeperLeaderElectionAgent(master, conf)
                                // zk note ,and path : /spark/leader_election
                                val workingDir = conf.get(ZOOKEEPER_DIRECTORY).getOrElse("/spark") + "/leader_election"
                                // 创建选举代理对象，内部执行选举
                                private def start(): Unit
                                    // create znode, and 
                                    zk = SparkCuratorUtil.newClient(conf)
                                    leaderLatch = new LeaderLatch(zk, workingDir)
                                    leaderLatch.addListener(this)
                                    leaderLatch.start()
                            // 13 . 特殊路径，参与选举后，如果该 agent 为 leader ，则进行如下操作
                                this.isLeader() // this = ZooKeeperLeaderElectionAgent
                                    updateLeadershipStatus(true)
                                        // 更新状态
                                            if (isLeader && status == LeadershipStatus.NOT_LEADER) {
                                                status = LeadershipStatus.LEADER
                                                masterInstance.electedLeader()
                                                    self.send(ElectedLeader)
                                                    // 14. 特殊路径，rpcEndpoint 接受到 worker 的 message：ElectedLeader
                                                    Master.receive()
                                                        case ElectedLeader =>
                                                            // 从持久化存储中获取 apps、driver、worker 信息
                                                            val (storedApps, storedDrivers, storedWorkers) = persistenceEngine.readPersistedData(rpcEnv)
                                                            // 根据存储信息的情况，判断是初始化启动， 还是 revoery 模式
                                                            state = if (storedApps.isEmpty && storedDrivers.isEmpty && storedWorkers.isEmpty) {
                                                                RecoveryState.ALIVE
                                                            } else {
                                                                RecoveryState.RECOVERING
                                                            }
                                            } else if (!isLeader && status == LeadershipStatus.LEADER) {
                                                status = LeadershipStatus.NOT_LEADER
                                                masterInstance.revokedLeadership()
                                                    // 15. 特殊路径，rpcEndpoint 接受到 worker 的 message：RevokedLeadership
                                                    Master.receive()
                                                        // exit system
                                                        case RevokedLeadership =>
                                                            logError("Leadership has been revoked -- master shutting down.")
                                                            System.exit(0)
                                            }
    // 启动服务后，正常 standby,Wait until [[RpcEnv]] exits.
    rpcEnv.awaitTermination()
        //NettyRpcEnv class
        dispatcher.awaitTermination()
            new CountDownLatch(1).await()
```

master 启动共 1-15 步骤，总结下来核心是做了四件事情：

1. 启动 rpcEndpoint 服务端 2
2. 启动 web ui
3. 选举 active master
4. 启动了一个定时任务：每隔一段时间去检查 workers status (通过Master.receive()方法)

## 4. Spark Worker 启动过程分析

知道进入的主类`org.apache.spark.deploy.master.Worker`，剩下的就是分析启动过程。

首先从 main() 方法开始，分析完 master 启动过程，worker 启动过程非常类似，`不同的是有一个注册过程！这个过程可以特意看下。`

``` scala

//以下以截取关键代码 + 注释的方式分析

 // start!

 def main(argStrings: Array[String]): Unit
    // 1. 启动rpcenv和 endpoint
    val rpcEnv = startRpcEnvAndEndpoint(args.host, args.port, args.webUiPort, args.cores,args.memory, args.masters, args.workDir, conf = conf,resourceFileOpt = conf.get(SPARK_WORKER_RESOURCE_FILE))
        // 2. 创建 rpcEnv
        val rpcEnv = RpcEnv.create(systemName, host, port, conf, securityMgr)

        // 3. setupEndpoint
        rpcEnv.setupEndpoint(ENDPOINT_NAME, new Worker(rpcEnv, webUiPort, cores, memory,masterAddresses, ENDPOINT_NAME, workDir, conf, securityMgr, resourceFileOpt))
            // 4. 构造 worker
            new Worker(rpcEnv, webUiPort, cores, memory,masterAddresses, ENDPOINT_NAME, workDir, conf, securityMgr, resourceFileOpt)
                // 关键的变量
                // A scheduled executor used to send messages at the specified time.
                private val forwardMessageScheduler = ThreadUtils.newDaemonSingleThreadScheduledExecutor("worker-forward-message-scheduler")
                // A separated thread to clean up the workDir and the directories of finished applications.
                private val cleanupThreadExecutor = ExecutionContext.fromExecutorService(ThreadUtils.newDaemonSingleThreadExecutor("worker-cleanup-thread"))
                // Model retries to connect to the master, after Hadoop's model. 先是 6 次，然后是 10 次，前后重试时间间隔不一样
                // master endpointRef
                private var master: Option[RpcEndpointRef] = None
                private var activeMasterUrl: String
                val resourcesUsed = new HashMap[String, MutableResourceInfo]()
                var workDir: File = null
                val finishedExecutors = new LinkedHashMap[String, ExecutorRunner]
                val drivers = new HashMap[String, DriverRunner]
                val executors = new HashMap[String, ExecutorRunner]
                val finishedDrivers = new LinkedHashMap[String, DriverRunner]
                val appDirectories = new HashMap[String, Seq[String]]
                val finishedApps = new HashSet[String]
                
                // The shuffle service is not actually started unless configured.
                private val shuffleService = if (externalShuffleServiceSupplier != null) {
                    externalShuffleServiceSupplier.get()
                } else {
                    new ExternalShuffleService(conf, securityMgr)
                        //
                }
                // A thread pool for registering with masters. Make sure we can register with all masters at the same time
                 private val registerMasterThreadPool = ThreadUtils.newDaemonCachedThreadPool("worker-register-master-threadpool",masterRpcAddresses.length)
            // 5. worker endpoint onstart
            Worker.onstart()
                // 6. createWorkDir
                createWorkDir()
                // 7. 启动 externalShuffleService
                startExternalShuffleService()
                    // 开始启动
                    shuffleService.startIfEnabled()
                        // 调用 class ExternalShuffleService 的 start()方法，Start the external shuffle service
                        start()
                            //  构建 transportContext ，用于rpc 通信； 构建 server 
                            transportContext = new TransportContext(transportConf, blockHandler, true)
                            server = transportContext.createServer(port, bootstraps.asJava)
                                return new TransportServer
                // 8. 初始化资源
                setupWorkerResources()
                    // 获取资源
                    resources = getOrDiscoverAllResources(conf, SPARK_WORKER_PREFIX, resourceFileOpt)
                    logResourceInfo(SPARK_WORKER_PREFIX, resources)
                    // 标记资源使用
                    resources.keys.foreach { rName => resourcesUsed(rName) = MutableResourceInfo(rName, new HashSet[String])}
                // 9. 构建 webUI 、绑定
                webUi = new WorkerWebUI(this, workDir, webUiPort)
                webUi.bind()
                // 10. **注册该 worker 到 master 节点**
                registerWithMaster()
                    registrationRetryTimer match {
                        case None =>
                            //  11. 尝试注册所有的 masters
                            registerMasterFutures = tryRegisterAllMasters()
                                // 挨个 master 地址进行注册
                                masterRpcAddresses.map { masterAddress =>
                                    registerMasterThreadPool.submit(new Runnable {})
                                        // 12. new Runnable , 启动 worker 的 endpoint 服务
                                        // setupEndpointRef，获取 master EndpointRef ， 并且通过 verifier 进行验证
                                        val masterEndpoint = rpcEnv.setupEndpointRef(masterAddress, Master.ENDPOINT_NAME)
                                            setupEndpointRefByURI(RpcEndpointAddress(address, endpointName).toString)
                                                defaultLookupTimeout.awaitResult(asyncSetupEndpointRefByURI(uri))
                                                    // 这里进入到 NettyRpcEnv class 内部
                                                    asyncSetupEndpointRefByURI(uri: String)
                                                        val endpointRef = new NettyRpcEndpointRef(conf, addr, this)
                                                        val verifier = new NettyRpcEndpointRef(.....)
                                                        verifier.ask[Boolean](RpcEndpointVerifier.CheckExistence(endpointRef.name)).flatMap{.....}
                                        // 13. 发送注册信息到 master
                                        sendRegisterMessageToMaster(masterEndpoint)
                                            // 通过 master endpointRef 发送消息
                                            masterEndpoint.send(RegisterWorker(workerId,host,port,self,cores,memory,workerWebUiUrl,masterEndpoint.address,resources))
                            // 14. 如果需要重试，则进行重新注册
                            registrationRetryTimer = Some(forwardMessageScheduler.scheduleAtFixedRate( () => Utils.tryLogNonFatalError { Option(self).foreach(_.send(ReregisterWithMaster)) }                                           
                                // ReregisterWithMaster 方法 , 这里调佣 worker.receive() 进行处理
                //15. 启动metricsSystem 服务
                ....
    // 16. 为了 fix SPARK-20989 问题：external shuffle service enabled，multiple workers on one host,only successfully launch the first worker and the rest fails. launch no more than one external shuffle service on each host.give explicit reason of failure instead of fail silently
    require(externalShuffleServiceEnabled == false || sparkWorkerInstances <= 1,"Starting multiple workers on one host is failed because ....")
    
    // 17 启动服务后，正常 standby,Wait until [[RpcEnv]] exits.
    rpcEnv.awaitTermination()
        //NettyRpcEnv class
        dispatcher.awaitTermination()
            new CountDownLatch(1).await()
```

启动逻辑中有两个特殊的代码入口，就是 master.receive() 入口， 启动逻辑有两个地方调用：`其一是注册发送注册消息RegisterWorker，其二是 ReregisterWithMaster`

- masterEndpoint.send(RegisterWorker(workerId,host,port,self,cores,memory,workerWebUiUrl,masterEndpoint.address,resources))
- forwardMessageScheduler.scheduleAtFixedRate(() => Utils.tryLogNonFatalError{ Option(self).foreach(_.send(ReregisterWithMaster)

我们分别看一下具体的逻辑

``` scala
// ------------------------  master -------------- //

// masterEndpoint.send(RegisterWorker , master 接收到待注册worker的 message
Master.receive()
    // 1. 处理 注册 worker 消息
    case RegisterWorker(id, workerHost, workerPort, workerRef, cores, memory, workerWebUiUrl,masterAddress, resources) =>
        // master 的状态
        if (state == RecoveryState.STANDBY)
            // master 还没有好，告诉 worker 在等等重试
             workerRef.send(MasterInStandby)
        // 如果在idToWorker map 中，则给该 worker 发送注册消息 ：RegisteredWorker , 同时告诉 worker 这个注册是一个duplicate 注册信息
        else if (idToWorker.contains(id)) 
            workerRef.send(RegisteredWorker(self, masterWebUiUrl, masterAddress, true))
        // 2. master注册worker流程开始
        else
            // 3. 构建 workerInfo ,记录 worker 基础信息，以及executors、drivers、state、coresUsed、memoryUsed、lastHeartbeat 等
            val worker = new WorkerInfo(id, workerHost, workerPort, cores, memory,workerRef, workerWebUiUrl, workerResources)
                // 核心变量
                  @transient var executors: mutable.HashMap[String, ExecutorDesc] = _ // executorId => info
                  @transient var drivers: mutable.HashMap[String, DriverInfo] = _ // driverId => info
                  @transient var state: WorkerState.Value = _
                  @transient var coresUsed: Int = _
                  @transient var memoryUsed: Int = _
                  @transient var lastHeartbeat: Long = _
            if (registerWorker(worker))
                // 4. 持久化persistenceEngine 加入这个 worker 信息，用于意外恢复
                persistenceEngine.addWorker(worker)
                // 5. 给 worker 发送 RegisteredWorker 消息，告诉注册了
                workerRef.send(RegisteredWorker(self, masterWebUiUrl, masterAddress, false))
                // 6. 重要服务！！！ 
                // 更新当前集群可用的资源情况：Schedule the currently available resources among waiting apps. This method will be called every time a new app joins or resource availability changes
                schedule()
                    // 先更新资源，然后启动等待的 driver
                    for (driver <- waitingDrivers.toList)
                        launchDriver(worker, driver)
                    // driver 的优先级大于 executor，此时在启动 executor：Schedule and launch executors on workers
                    startExecutorsOnWorkers()
            else
                // 7. 注册失败，告诉 worker 重新注册
                 workerRef.send(RegisterWorkerFailed("Attempted to re-register worker at same address: "+ workerAddress))
    
    // 16. 处理心跳消息
    case Heartbeat(workerId, worker) =>
        idToWorker.get(workerId) match {
            case Some(workerInfo) =>
                // 更新心跳时间
                    workerInfo.lastHeartbeat = System.currentTimeMillis()
            case None =>
                // 如果在workers 列表中，但是还没有注册成功，则发送重新注册的消息
                worker.send(ReconnectWorker(masterUrl))


// ------------------------  worker -------------- //
// master 发送注册结果信息给 worker         
  // Master to Worker 的消息
  sealed trait RegisterWorkerResponse

Worker.receive()
    // 8. worker 处理 master 发送过来关于 register 的消息
    case msg: RegisterWorkerResponse =>
      handleRegisterResponse(msg)
         msg match {
            // 9. 处理 master注册成功的消息
            case RegisteredWorker(masterRef, masterWebUiUrl, masterAddress, duplicate) =>
                // 10. 记录新的 Master 地址，Change to use the new master.
                changeMaster(masterRef, masterWebUiUrl, masterAddress)
                    activeMasterUrl = masterRef.address.toSparkURL
                    master = Some(masterRef)
                    connected = true
                    // Cancel any outstanding re-registration attempts because we found a new master
                    cancelLastRegistrationRetry()
                // 11. 定时发送心跳
                forwardMessageScheduler.scheduleAtFixedRate(() => Utils.tryLogNonFatalError { self.send(SendHeartbeat) },0, HEARTBEAT_MILLIS, TimeUnit.MILLISECONDS)
                // 14. 如果设置了old application directories 清理，则在注册的时候自动进行清理
                if enable
                    forwardMessageScheduler.scheduleAtFixedRate(() => Utils.tryLogNonFatalError { self.send(WorkDirCleanup) },CLEANUP_INTERVAL_MILLIS, CLEANUP_INTERVAL_MILLIS, TimeUnit.MILLISECONDS)
                // 15. 给 master 发送当前 executor 基础信息，Used to send state on-the-wire about Executors from Worker to Master
                val execs = executors.values.map { e =>
                    new ExecutorDescription(e.appId, e.execId, e.cores, e.state)
                }
                masterRef.send(WorkerLatestState(workerId, execs.toList, drivers.keys.toSeq))
            // 17. 如果注册失败
            case RegisterWorkerFailed(message) =>
                // 系统退出
                System.exit(1)
            
            // 18. Ignore. Master not yet ready.
            case MasterInStandby =>

    // 12. 进行心跳通信， 在第 11 步有调用这个
    case SendHeartbeat =>
        // connected 在第 10 步中置为 true
        if (connected) { sendToMaster(Heartbeat(workerId, self)) }
            // 13. Send a message to the current master.
            case Some(masterRef) => masterRef.send(message)

```

Worker 启动共 1-18 步骤，总结下来核心是做了四件事情：

1. 启动 RPC 服务
2. 启动 web ui
3. 注册到 master
4. 注册成功之后，定时发心跳

至此，spark master 和 worker 启动逻辑分析完成

## 5. 总结一下 master 和 worker 的启动过程

核心步骤：

1. 集群启动脚本脚本start-all.sh
   - 分析 Master启动：spark-class org.apache.spark.deploy.master.Master
   - Worker启动：spark-class org.apache.sprak.deploy.worker.Worker
2. Master 启动分析
   - 启动 rpc 服务端
   - 启动 web ui
   - 选举 active master
   - 启动了一个定时任务：每隔一段时间去检查 workers status (通过Master.receive()方法)
3. Worker 启动分析
   - 启动 RPC 服务
   - 启动 web ui
   - 先向 Master 注册
   - 注册成功之后，定时发心跳
