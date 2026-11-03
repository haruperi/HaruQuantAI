/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  javax.jms.JMSException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.ListenerManager;
import com.strategyquant.gridlib.compute.JobResult;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.compute.performer.FinishListener;
import com.strategyquant.gridlib.compute.performer.IComputePerformer;
import com.strategyquant.gridlib.compute.performer.IJobStatusChangedHandler;
import com.strategyquant.gridlib.compute.performer.JmsComputePerformer;
import com.strategyquant.gridlib.compute.performer.MultithreadComputePerformer;
import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.topology.GridTopology;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.atomic.AtomicLong;
import javax.jms.JMSException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Compute
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(Compute.class);
    private Map<Integer, AtomicLong> runningCounts = new Int2ObjectOpenHashMap();
    private Map<Integer, AtomicLong> waitingCounts = new Int2ObjectOpenHashMap();
    private Map<Integer, AtomicLong> runningUndeliveredCounts = new Int2ObjectOpenHashMap();
    private JmsComputePerformer jmsPerformer;
    private MultithreadComputePerformer localPerformer;
    private final Config config;
    private boolean runOnNode;
    private ListenerManager listenerManager;
    private List<FinishListener> finishListeners = new ArrayList<FinishListener>();
    private volatile String justStoppingJobGroupID;

    public Compute(JmsConnectionInfo jmsConnectionInfo, Config config, boolean bl) throws JMSException {
        this.config = config;
        this.runOnNode = bl;
        this.createPerformers(jmsConnectionInfo);
        boolean bl2 = this.isLocalMode() && !bl;
        this.listenerManager = new ListenerManager(jmsConnectionInfo, bl2);
        TimerTask timerTask = new TimerTask(){

            @Override
            public void run() {
                try {
                    Compute.this.checkFinishListeners();
                }
                catch (Exception exception) {
                    LOGGER.error("Error while handling finish listeners", (Throwable)exception);
                }
            }
        };
        Timer timer = new Timer("Timer");
        long l = 500L;
        long l2 = 200L;
        timer.scheduleAtFixedRate(timerTask, l, l2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected void checkFinishListeners() {
        List<FinishListener> list = this.finishListeners;
        synchronized (list) {
            Iterator<FinishListener> iterator = this.finishListeners.iterator();
            while (iterator.hasNext()) {
                FinishListener finishListener = iterator.next();
                if (!finishListener.isFinished()) continue;
                LOGGER.debug("Group " + finishListener.getWaitGroupId() + " is finished - notify");
                finishListener.notifyWaitingObj();
                iterator.remove();
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void wakeupAllWaiting() {
        List<FinishListener> list = this.finishListeners;
        synchronized (list) {
            for (FinishListener finishListener : this.finishListeners) {
                LOGGER.debug("Group " + finishListener.getWaitGroupId() + " is finished - notify");
                finishListener.notifyWaitingObj();
            }
        }
    }

    public void registerMessageListener(String string, IGridMessageListener iGridMessageListener) {
        this.listenerManager.registerMessageListener(string, iGridMessageListener);
    }

    public boolean isRegisteredMessageListener(String string) {
        return this.listenerManager.isRegisteredMessageListener(string);
    }

    public void removeMessageListener(String string) {
        this.listenerManager.removeMessageListener(string);
    }

    public boolean sendMessageToJob(String string, String string2, GridMessage gridMessage) {
        try {
            return this.getPerformer().sendMessageToJob(string, string2, gridMessage);
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
            return false;
        }
    }

    public boolean sendMessageToListener(String string, GridMessage gridMessage) {
        return this.listenerManager.sendToListener(string, gridMessage);
    }

    private void prepareComputePerformer(IComputePerformer iComputePerformer) {
        iComputePerformer.addJobFinishedHandler(new IJobStatusChangedHandler(){

            @Override
            public void onJobFinished(String string, String string2, JobResult<Serializable> jobResult) {
                Compute.this.jobFinished(string, string2, jobResult);
            }

            @Override
            public void onJobExecuted(String string, String string2) {
                Compute.this.jobExecuted(string, string2);
            }
        });
    }

    private void jobExecuted(String string, String string2) {
        this.decrementJobCounter(string2, this.waitingCounts);
        this.incrementJobsCounter(string2, this.runningCounts);
        this.incrementJobsCounter(string2, this.runningUndeliveredCounts);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected void jobFinished(String string, String string2, JobResult<?> jobResult) {
        GridMessage gridMessage = new GridMessage(1, null, (Serializable)jobResult.getData());
        JobDetails jobDetails = new JobDetails(string);
        jobDetails.setDuration(jobResult.getDuration());
        jobDetails.setException(jobResult.getErrorMessage());
        gridMessage.setJobDetails(jobDetails);
        this.decrementJobCounter(string2, this.runningCounts);
        try {
            this.sendMessageToListener(string2, gridMessage);
        }
        finally {
            this.decrementJobCounter(string2, this.runningUndeliveredCounts);
        }
    }

    private void createPerformers(JmsConnectionInfo jmsConnectionInfo) {
        try {
            if (jmsConnectionInfo.getTarget() != null && !this.runOnNode) {
                this.jmsPerformer = new JmsComputePerformer(jmsConnectionInfo, this.config);
                this.prepareComputePerformer(this.jmsPerformer);
                return;
            }
        }
        catch (JMSException jMSException) {
            LOGGER.error("Error while creating JMS compute performer", (Throwable)jMSException);
        }
        this.localPerformer = new MultithreadComputePerformer(this.config);
        this.prepareComputePerformer(this.localPerformer);
    }

    public boolean isLocalMode() {
        return this.jmsPerformer == null;
    }

    public IComputePerformer getPerformer() {
        if (this.jmsPerformer != null && this.jmsPerformer.getGridTopology().getTotalCores() != 0) {
            return this.jmsPerformer;
        }
        return this.localPerformer;
    }

    public void execute(String string, List<? extends GridJob<?>> list, ExecuteOptions executeOptions) throws Exception {
        for (GridJob<?> gridJob : list) {
            if (string.equals(this.justStoppingJobGroupID)) {
                LOGGER.debug("Skipping execution loop due stopping the group:" + string);
                break;
            }
            this.incrementJobsCounter(string, this.waitingCounts);
            gridJob.setJobGroupId(string);
            try {
                this.getPerformer().execute(gridJob, string, executeOptions);
            }
            catch (Exception exception) {
                LOGGER.error("Error while registering job. Removing it from wating counts.", (Throwable)exception);
                this.decrementJobCounter(string, this.waitingCounts);
            }
        }
        this.getPerformer().commit();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void incrementJobsCounter(String string, Map<Integer, AtomicLong> map) {
        Map<Integer, AtomicLong> map2 = map;
        synchronized (map2) {
            int n = string.hashCode();
            AtomicLong atomicLong = map.get(n);
            if (atomicLong == null) {
                atomicLong = new AtomicLong(0L);
            }
            atomicLong.incrementAndGet();
            map.put(n, atomicLong);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void decrementJobCounter(String string, Map<Integer, AtomicLong> map) {
        Map<Integer, AtomicLong> map2 = map;
        synchronized (map2) {
            int n = string.hashCode();
            AtomicLong atomicLong = map.get(n);
            if (atomicLong == null) {
                return;
            }
            long l = atomicLong.decrementAndGet();
            if (l == 0L) {
                map.remove(n);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void close() throws Exception {
        if (this.localPerformer != null) {
            this.localPerformer.close();
        }
        if (this.jmsPerformer != null) {
            this.jmsPerformer.close();
        }
        this.listenerManager.close();
        List<FinishListener> list = this.finishListeners;
        synchronized (list) {
            this.finishListeners.clear();
        }
    }

    public void pause(String string) {
        try {
            this.getPerformer().pause(string);
            this.listenerManager.sendToListener(string, new GridMessage(2));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void stop(String string) {
        this.justStoppingJobGroupID = string;
        try {
            this.getPerformer().stop(string);
            Map<Integer, AtomicLong> map = this.waitingCounts;
            synchronized (map) {
                this.waitingCounts.remove(string.hashCode());
            }
            this.listenerManager.sendToListener(string, new GridMessage(4));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
        this.justStoppingJobGroupID = null;
    }

    public void restart(String string) {
        try {
            this.getPerformer().restart(string);
            this.listenerManager.sendToListener(string, new GridMessage(3));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
    }

    public long getRunningJobsCount(String string) {
        return this.getCount(string, this.runningCounts);
    }

    public long getExecutedUndeliveredJobsCount(String string) {
        return this.getCount(string, this.runningUndeliveredCounts);
    }

    public long getWaitingJobsCount(String string) {
        return this.getCount(string, this.waitingCounts);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public long getCount(String string, Map<Integer, AtomicLong> map) {
        Map<Integer, AtomicLong> map2 = map;
        synchronized (map2) {
            if (string == null) {
                long l = 0L;
                for (AtomicLong atomicLong : map.values()) {
                    l += atomicLong.get();
                }
                return l;
            }
            int n = string.hashCode();
            AtomicLong atomicLong = map.get(n);
            long l = atomicLong == null ? 0L : atomicLong.get();
            return l;
        }
    }

    public GridTopology getGridTopology() {
        return this.getPerformer().getGridTopology();
    }

    public String getGridDescriptions() {
        return this.getPerformer().getGridDescriptions();
    }

    public void setProgress(String string, String string2, int n) {
        this.getPerformer().setProgress(string, string2, n);
        GridMessage gridMessage = new GridMessage(6, string, Integer.valueOf(n));
        this.sendMessageToListener(string2, gridMessage);
    }

    public void setJobWaiting(String string, String string2, boolean bl) {
        this.getPerformer().setJobWaiting(string, string2, bl);
    }

    public void waitForAllTaskFinished() throws InterruptedException {
        LOGGER.debug("Waiting for all task completed");
        do {
            Thread.sleep(2000L);
        } while (!this.runningCounts.isEmpty());
        LOGGER.info("All tasks completed");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void waitForFinish(Object object, String string, String string2, String string3) throws InterruptedException {
        this.getPerformer().setJobWaiting(string, string2, true);
        LOGGER.debug("Job: {}({}) is going to sleep", (Object)string, (Object)string2);
        FinishListener finishListener = new FinishListener(this, object, string3);
        Object object2 = this.finishListeners;
        synchronized (object2) {
            this.finishListeners.add(finishListener);
        }
        try {
            object2 = object;
            synchronized (object2) {
                object.wait();
            }
        }
        finally {
            this.setJobWaiting(string, string2, false);
        }
        LOGGER.debug("Job: {}({}) woken up", (Object)string, (Object)string2);
    }

    public void setGroupRestrictions(String string, int n) {
        this.getPerformer().setGroupRestrictions(string, n);
    }

    public void check() {
        this.getPerformer().check();
    }

    public int getComputedThread() {
        return this.getPerformer().getComputedThread();
    }

    public int getUsedComputedThreads() {
        return this.getPerformer().getUsedComputedThreads();
    }

    public void setUsedComputedThreads(int n) {
        this.getPerformer().setUsedComputedThreads(n);
    }

    public void stop(String string, String string2) {
        this.justStoppingJobGroupID = string;
        try {
            this.getPerformer().stop(string, string2);
            this.listenerManager.sendToListener(string, new GridMessage(4, null, (Serializable)((Object)string2)));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
        this.justStoppingJobGroupID = null;
    }

    public void pause(String string, String string2) {
        try {
            this.getPerformer().pause(string, string2);
            this.listenerManager.sendToListener(string, new GridMessage(2, null, (Serializable)((Object)string2)));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
    }

    public void restart(String string, String string2) {
        try {
            this.getPerformer().restart(string, string2);
            this.listenerManager.sendToListener(string, new GridMessage(3, null, (Serializable)((Object)string2)));
        }
        catch (Exception exception) {
            LOGGER.error("", (Throwable)exception);
        }
    }
}

