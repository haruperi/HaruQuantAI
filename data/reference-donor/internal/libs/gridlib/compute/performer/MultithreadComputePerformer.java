/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.google.common.util.concurrent.ThreadFactoryBuilder
 *  com.strategyquant.lib.memory.CpuInfo
 *  net.openhft.affinity.AffinityLock
 *  org.apache.commons.lang3.exception.ExceptionUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.compute.performer;

import com.google.common.util.concurrent.ThreadFactoryBuilder;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.compute.JobResult;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.compute.common.JobQueue;
import com.strategyquant.gridlib.compute.common.PausedTasks;
import com.strategyquant.gridlib.compute.performer.IComputePerformer;
import com.strategyquant.gridlib.compute.performer.IJobStatusChangedHandler;
import com.strategyquant.gridlib.concurrent.ThreadPool;
import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.topology.GridTopology;
import com.strategyquant.gridlib.topology.NodeInfo;
import com.strategyquant.gridlib.utils.CoreUsagesEvaluator;
import com.strategyquant.lib.memory.CpuInfo;
import com.sun.management.OperatingSystemMXBean;
import java.io.Serializable;
import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import net.openhft.affinity.AffinityLock;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MultithreadComputePerformer
implements IComputePerformer {
    private static final int MINIMAL_CORES_FOR_SQ = 3;
    private static final int MINIMAL_RESERVED_CORES_FOR_OS = 4;
    private static final int TERMINATION_WAIT = 5000;
    private static final Logger LOGGER = LoggerFactory.getLogger(MultithreadComputePerformer.class);
    private JobQueue<GridJob<?>> taskQueue = new JobQueue();
    private List<IJobStatusChangedHandler> handlers = new LinkedList<IJobStatusChangedHandler>();
    private ThreadPool threadPool;
    private ExecutorService nonBlockingPool;
    private AtomicInteger runningBlockingJobs = new AtomicInteger(0);
    private AtomicInteger runningNonBlockingJobs = new AtomicInteger(0);
    private AtomicInteger waitingBlockingJobs = new AtomicInteger(0);
    private AtomicInteger coreCount = new AtomicInteger();
    private int maximumCoreCount;
    private GridTopology gridTopology;
    private Config config;
    private volatile boolean shuttingDown;

    public MultithreadComputePerformer(Config config) {
        this.config = config;
        this.taskQueue.setFinishedJobsCount(config.getFinishedJobsInDesc());
        this.gridTopology = new GridTopology();
        this.initExecutors();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void fillGridTopology() {
        GridTopology gridTopology = this.gridTopology;
        synchronized (gridTopology) {
            OperatingSystemMXBean operatingSystemMXBean = (OperatingSystemMXBean)ManagementFactory.getOperatingSystemMXBean();
            NodeInfo nodeInfo = null;
            if (this.gridTopology.getNodes().isEmpty()) {
                nodeInfo = new NodeInfo();
                nodeInfo.setIp(this.evalIp());
                nodeInfo.setOsVersion(operatingSystemMXBean.getVersion());
                this.gridTopology.getNodes().add(nodeInfo);
            } else {
                nodeInfo = this.gridTopology.getNodes().get(0);
            }
            double d = 1.073741824E9;
            double d2 = (double)operatingSystemMXBean.getTotalPhysicalMemorySize() / d;
            double d3 = d2 - (double)operatingSystemMXBean.getFreePhysicalMemorySize() / d;
            int n = (int)(operatingSystemMXBean.getSystemCpuLoad() * 100.0);
            nodeInfo.setTotalMemory((double)Math.round(d2 * 10.0) / 10.0);
            nodeInfo.setUsedMemory((double)Math.round(d3 * 10.0) / 10.0);
            nodeInfo.setRunningThreads(this.runningBlockingJobs.get());
            nodeInfo.setCpuUsage(n);
            nodeInfo.setUsedCores(this.coreCount.get());
            this.gridTopology.setTotalCores(nodeInfo.getUsedCores());
        }
    }

    private String evalIp() {
        String string = null;
        if (this.config.getNodeId() != null && !this.config.getNodeId().trim().isEmpty()) {
            string = this.config.getNodeId();
        } else {
            try {
                string = InetAddress.getLocalHost().getHostAddress();
            }
            catch (Exception exception) {
                string = "Can't be determined";
            }
        }
        return string;
    }

    private int adjustCoresForUsage(int n, boolean bl) {
        int n2;
        int n3;
        int n4;
        int n5 = CpuInfo.getAvailableProcessors();
        int n6 = n;
        if (bl && n > (n4 = Math.max(n3 = (int)((float)n5 * 0.8f), n2 = n5 - 4))) {
            n6 = n4;
        }
        if (n6 < 3) {
            n6 = 3;
        }
        if (n6 != n) {
            LOGGER.info("Adjusting used cores to: {} from requested: {}", (Object)n6, (Object)n);
        }
        return n6;
    }

    private void initExecutors() {
        this.maximumCoreCount = CoreUsagesEvaluator.getCores(this.config.getCoreUsage());
        int n = this.adjustCoresForUsage(this.maximumCoreCount, this.config.isAdjustTopSizeOfCores());
        this.coreCount.set(n);
        LOGGER.info("Using: {} cores, core usage configuration: '{}'", (Object)this.coreCount, (Object)this.config.getCoreUsage());
        this.threadPool = new ThreadPool(n, this.config.isUseAffinity());
        java.util.logging.Logger logger = java.util.logging.Logger.getLogger(AffinityLock.class.getName());
        logger.setUseParentHandlers(false);
        ThreadFactory threadFactory = new ThreadFactoryBuilder().setNameFormat("Nonblocking computeThread - %d").build();
        this.nonBlockingPool = Executors.newCachedThreadPool(threadFactory);
    }

    @Override
    public void close() throws Exception {
        this.shuttingDown = true;
        this.threadPool.close();
        this.nonBlockingPool.shutdownNow();
        this.stopAll();
        this.taskQueue.close();
        this.threadPool.waitForTermination(5000L);
        this.nonBlockingPool.awaitTermination(5000L, TimeUnit.MILLISECONDS);
        this.handlers.clear();
    }

    private void stopAll() {
        Set<JobQueue.JobInfo<GridJob<?>>> set = this.taskQueue.getRunningTasks();
        LOGGER.debug("Stopping all running tasks:" + set.size());
        GridMessage gridMessage = new GridMessage(4);
        for (JobQueue.JobInfo<GridJob<?>> jobInfo : set) {
            this.sendMessageToJob(jobInfo.getData(), gridMessage);
        }
    }

    @Override
    public void addJobFinishedHandler(IJobStatusChangedHandler iJobStatusChangedHandler) {
        this.handlers.add(iJobStatusChangedHandler);
    }

    @Override
    public void execute(GridJob<?> gridJob, String string, ExecuteOptions executeOptions) throws Exception {
        if (this.shuttingDown) {
            return;
        }
        this.taskQueue.add(gridJob.getJobId(), string, gridJob.getPriority(), gridJob.isBlocking(), gridJob, executeOptions);
        this.tryToExecute();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void tryToExecute() {
        if (this.shuttingDown) {
            return;
        }
        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("Trying to execute job. Running blocking jobs: {}, non-blocking tasks: {}. Available cores:{}, Waiting tasks:{}", new Object[]{this.runningBlockingJobs, this.runningNonBlockingJobs, this.coreCount, this.waitingBlockingJobs});
        }
        JobQueue.JobInfo<GridJob<?>> jobInfo = null;
        JobQueue<GridJob<?>> jobQueue = this.taskQueue;
        synchronized (jobQueue) {
            boolean bl = this.runningBlockingJobs.get() < this.coreCount.get() + this.waitingBlockingJobs.get();
            jobInfo = this.taskQueue.getNext(true, bl);
            if (jobInfo == null) {
                if (LOGGER.isDebugEnabled()) {
                    LOGGER.debug("Nothing to compute");
                }
                return;
            }
            if (jobInfo.isBlocking() && this.runningBlockingJobs.get() >= this.coreCount.get() + this.waitingBlockingJobs.get() && this.coreCount.get() > 1) {
                if (LOGGER.isDebugEnabled()) {
                    LOGGER.debug("Job can't be executed - no free thread.");
                }
                return;
            }
            this.taskQueue.computing(jobInfo.getId(), jobInfo.getJobGroupId());
            this.incrementRunningTasksCount(jobInfo);
        }
        this.runJob(jobInfo);
    }

    private void incrementRunningTasksCount(JobQueue.JobInfo<?> jobInfo) {
        if (jobInfo.isBlocking()) {
            this.runningBlockingJobs.incrementAndGet();
        } else {
            this.runningNonBlockingJobs.incrementAndGet();
        }
    }

    private void decrementRunningTasksCount(JobQueue.JobInfo<?> jobInfo) {
        if (jobInfo.isBlocking()) {
            this.runningBlockingJobs.decrementAndGet();
        } else {
            this.runningNonBlockingJobs.decrementAndGet();
        }
    }

    private void runJob(final JobQueue.JobInfo<GridJob<?>> jobInfo) {
        if (this.shuttingDown) {
            return;
        }
        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("Running job: {}({}). Blocking: {}", new Object[]{jobInfo.getId(), jobInfo.getJobGroupId(), jobInfo.isBlocking()});
        }
        Runnable runnable = new Runnable(){
            final /* synthetic */ MultithreadComputePerformer this$0;
            {
                this.this$0 = multithreadComputePerformer;
            }

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                this.this$0.callJobStartedHandlers(jobInfo);
                String string = Thread.currentThread().getName();
                Thread.currentThread().setName(string + " - " + jobInfo.getId());
                JobResult<Serializable> jobResult = new JobResult<Serializable>();
                try {
                    if (jobInfo.getData() != null) {
                        Serializable serializable = (Serializable)((GridJob)jobInfo.getData()).call();
                        jobResult.setSuccess(true);
                        jobResult.setData(serializable);
                    } else {
                        jobResult.setSuccess(true);
                    }
                    Thread.currentThread().setName(string);
                    long l = this.this$0.taskQueue.computed(jobInfo.getId(), jobInfo.getJobGroupId(), jobResult.isSuccess(), jobResult.getErrorMessage());
                    jobResult.setDuration(l);
                    this.this$0.callJobFinishedHandlers(jobInfo, jobResult);
                }
                catch (Throwable throwable) {
                    try {
                        jobResult.setSuccess(false);
                        jobResult.setErrorMessage(ExceptionUtils.getStackTrace((Throwable)throwable));
                        if (throwable.getClass().getSimpleName().contains("TaskStoppedException")) {
                            LOGGER.info("Task stopped: {}({})", (Object)jobInfo.getId(), (Object)(jobInfo.getJobGroupId() + ")"));
                        } else {
                            LOGGER.error("Error while running task: {}({})", new Object[]{jobInfo.getId(), jobInfo.getJobGroupId() + ")", throwable});
                        }
                        Thread.currentThread().setName(string);
                        long l = this.this$0.taskQueue.computed(jobInfo.getId(), jobInfo.getJobGroupId(), jobResult.isSuccess(), jobResult.getErrorMessage());
                        jobResult.setDuration(l);
                        this.this$0.callJobFinishedHandlers(jobInfo, jobResult);
                    }
                    catch (Throwable throwable2) {
                        Thread.currentThread().setName(string);
                        long l = this.this$0.taskQueue.computed(jobInfo.getId(), jobInfo.getJobGroupId(), jobResult.isSuccess(), jobResult.getErrorMessage());
                        jobResult.setDuration(l);
                        this.this$0.callJobFinishedHandlers(jobInfo, jobResult);
                        this.this$0.decrementRunningTasksCount(jobInfo);
                        LOGGER.debug("Job {}({}) finished. Running blocking jobs: {}, non-blocking tasks: {}. Available cores:{}, Waiting tasks:{}", new Object[]{jobInfo.getId(), jobInfo.getJobGroupId(), this.this$0.runningBlockingJobs, this.this$0.runningNonBlockingJobs, this.this$0.coreCount, this.this$0.waitingBlockingJobs});
                        this.this$0.tryToExecute();
                        throw throwable2;
                    }
                    this.this$0.decrementRunningTasksCount(jobInfo);
                    LOGGER.debug("Job {}({}) finished. Running blocking jobs: {}, non-blocking tasks: {}. Available cores:{}, Waiting tasks:{}", new Object[]{jobInfo.getId(), jobInfo.getJobGroupId(), this.this$0.runningBlockingJobs, this.this$0.runningNonBlockingJobs, this.this$0.coreCount, this.this$0.waitingBlockingJobs});
                    this.this$0.tryToExecute();
                }
                this.this$0.decrementRunningTasksCount(jobInfo);
                LOGGER.debug("Job {}({}) finished. Running blocking jobs: {}, non-blocking tasks: {}. Available cores:{}, Waiting tasks:{}", new Object[]{jobInfo.getId(), jobInfo.getJobGroupId(), this.this$0.runningBlockingJobs, this.this$0.runningNonBlockingJobs, this.this$0.coreCount, this.this$0.waitingBlockingJobs});
                this.this$0.tryToExecute();
            }
        };
        if (jobInfo.isBlocking()) {
            this.threadPool.execute(runnable, this.waitingBlockingJobs.get() > 0);
        } else {
            this.nonBlockingPool.execute(runnable);
            this.tryToExecute();
        }
    }

    protected void callJobFinishedHandlers(JobQueue.JobInfo<GridJob<?>> jobInfo, JobResult<Serializable> jobResult) {
        for (IJobStatusChangedHandler iJobStatusChangedHandler : this.handlers) {
            try {
                iJobStatusChangedHandler.onJobFinished(jobInfo.getId(), jobInfo.getJobGroupId(), jobResult);
            }
            catch (Throwable throwable) {
                LOGGER.error("Error while running handler", throwable);
            }
        }
    }

    protected void callJobStartedHandlers(JobQueue.JobInfo<GridJob<?>> jobInfo) {
        for (IJobStatusChangedHandler iJobStatusChangedHandler : this.handlers) {
            try {
                iJobStatusChangedHandler.onJobExecuted(jobInfo.getId(), jobInfo.getJobGroupId());
            }
            catch (Throwable throwable) {
                LOGGER.error("Error while running handler", throwable);
            }
        }
    }

    @Override
    public void commit() throws Exception {
    }

    @Override
    public void pause(String string) {
        PausedTasks<GridJob<?>> pausedTasks = this.taskQueue.pause(string);
        GridMessage gridMessage = new GridMessage(2);
        List<JobQueue.JobInfo<GridJob<?>>> list = pausedTasks.getRunningTasks();
        for (JobQueue.JobInfo<GridJob<?>> jobInfo : list) {
            this.sendMessageToJob(jobInfo.getData(), gridMessage);
        }
    }

    @Override
    public void pause(String string, String string2) throws Exception {
        JobQueue.JobInfo<GridJob<?>> jobInfo = this.taskQueue.pause(string, string2);
        if (jobInfo != null) {
            this.sendMessageToJob(jobInfo.getData(), new GridMessage(2));
        }
    }

    private void performStop(JobQueue.JobInfo<GridJob<?>> jobInfo, GridMessage gridMessage) {
        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("Stopping job: {}", (Object)jobInfo.getId());
        }
        if (jobInfo.isExecuted()) {
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Sending stop message to job: {}", (Object)jobInfo.getId());
            }
            this.sendMessageToJob(jobInfo.getData(), gridMessage);
        } else {
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug("Destroying job: {}", (Object)jobInfo.getId());
            }
            try {
                jobInfo.getData().destroy();
            }
            catch (Throwable throwable) {
                LOGGER.error("Error while destroying job", throwable);
            }
            jobInfo.setData(null);
        }
    }

    @Override
    public void stop(String string) {
        Set<JobQueue.JobInfo<GridJob<?>>> set = this.taskQueue.stop(string);
        GridMessage gridMessage = new GridMessage(4);
        for (JobQueue.JobInfo<GridJob<?>> jobInfo : set) {
            this.performStop(jobInfo, gridMessage);
        }
        this.tryToExecute();
    }

    @Override
    public void stop(String string, String string2) throws Exception {
        JobQueue.JobInfo<GridJob<?>> jobInfo = this.taskQueue.stop(string, string2);
        if (jobInfo != null) {
            this.performStop(jobInfo, new GridMessage(4));
            this.tryToExecute();
        }
    }

    @Override
    public void restart(String string) {
        List<JobQueue.JobInfo<GridJob<?>>> list = this.taskQueue.restore(string);
        GridMessage gridMessage = new GridMessage(3);
        for (JobQueue.JobInfo<GridJob<?>> jobInfo : list) {
            this.sendMessageToJob(jobInfo.getData(), gridMessage);
        }
        this.tryToExecute();
    }

    @Override
    public void restart(String string, String string2) throws Exception {
        JobQueue.JobInfo<GridJob<?>> jobInfo = this.taskQueue.restore(string, string2);
        if (jobInfo != null) {
            this.sendMessageToJob(jobInfo.getData(), new GridMessage(3));
            this.tryToExecute();
        }
    }

    @Override
    public boolean sendMessageToJob(String string, String string2, GridMessage gridMessage) {
        JobQueue.JobInfo<GridJob<?>> jobInfo = this.taskQueue.getJobInfo(string, string2);
        if (jobInfo != null) {
            this.sendMessageToJob(jobInfo.getData(), gridMessage);
        }
        return jobInfo != null;
    }

    private void sendMessageToJob(GridJob<?> gridJob, GridMessage gridMessage) {
        try {
            if (gridJob != null) {
                gridJob.messageReceived(gridMessage);
            }
        }
        catch (Throwable throwable) {
            LOGGER.error("Error while handling message in job", throwable);
        }
    }

    @Override
    public GridTopology getGridTopology() {
        this.fillGridTopology();
        return this.gridTopology;
    }

    @Override
    public String getGridDescriptions() {
        return this.taskQueue.getJsonDescriptions();
    }

    @Override
    public void setProgress(String string, String string2, int n) {
        this.taskQueue.updateProgress(string, string2, n);
    }

    @Override
    public void setGroupRestrictions(String string, int n) {
        this.taskQueue.setGroupRestrictions(string, n);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void check() {
        JobQueue<GridJob<?>> jobQueue = this.taskQueue;
        synchronized (jobQueue) {
            this.taskQueue.check();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void setJobWaiting(String string, String string2, boolean bl) {
        LOGGER.debug("Setting job:{}({}) as waiting:{}", new Object[]{string, string2, bl});
        JobQueue.JobInfo<?> jobInfo = null;
        if (string != null && string2 != null) {
            jobInfo = this.taskQueue.setJobWaiting(string, string2, bl);
        }
        if (jobInfo != null && jobInfo.isBlocking()) {
            JobQueue<GridJob<?>> jobQueue = this.taskQueue;
            synchronized (jobQueue) {
                if (bl) {
                    this.waitingBlockingJobs.incrementAndGet();
                } else {
                    int n = this.waitingBlockingJobs.decrementAndGet();
                    if (n < 0) {
                        this.waitingBlockingJobs.set(0);
                    }
                }
            }
        }
        this.tryToExecute();
    }

    @Override
    public int getComputedThread() {
        return this.maximumCoreCount;
    }

    @Override
    public int getUsedComputedThreads() {
        return this.coreCount.get();
    }

    @Override
    public void setUsedComputedThreads(int n) {
        if (n < 0 || n > this.maximumCoreCount) {
            throw new IllegalArgumentException("Invalid count: " + n);
        }
        this.coreCount.set(n);
    }
}

