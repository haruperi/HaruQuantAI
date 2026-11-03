/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.SQUUID
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simplegrid;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.SQUUID;
import com.strategyquant.tradinglib.project.IProgressStatusListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.io.Serializable;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class SimpleGridEngine<JobClass extends GridJob<ResultClass>, ResultClass extends Serializable>
implements IProgressStatusListener {
    public static Logger Log = LoggerFactory.getLogger((String)"SimpleGridEngine");
    private long start;
    protected int batchSize = 0;
    private boolean allDone = false;
    private GridClient gridClient = SQGrid.getGridClient();
    private StopPauseEngine progressEngine;
    private String jobGroupID;
    private int jobsCountThreshold;
    private GridJob parentGridJob;
    private boolean singleThreaded = false;
    ArrayList<JobClass> firstJobsGroup = null;

    public SimpleGridEngine(StopPauseEngine stopPauseEngine, GridJob gridJob) throws Exception {
        this(stopPauseEngine, gridJob, false);
    }

    public SimpleGridEngine(StopPauseEngine stopPauseEngine, GridJob gridJob, boolean bl) throws Exception {
        this.progressEngine = stopPauseEngine;
        this.jobGroupID = SQUUID.randomUUID();
        this.parentGridJob = gridJob;
        this.singleThreaded = bl;
        this.batchSize = 5;
        this.jobsCountThreshold = SQGrid.getGridClient().getRecommendedBatchSize();
        this.gridClient.registerMessageListener(this.jobGroupID, new IGridMessageListener(){

            public void messageReceived(GridMessage gridMessage) {
                SimpleGridEngine.this.processMessage(gridMessage);
            }
        });
        stopPauseEngine.registerStatusListener(this);
    }

    public void unregisterListeners() {
        if (this.progressEngine != null) {
            this.progressEngine.unregisterStatusListener(this);
        }
        if (this.gridClient != null) {
            this.gridClient.removeMessageListener(this.jobGroupID);
        }
    }

    @Override
    public void onStatusChanged(int n) {
        if (n == 4 || n == 3 || n == 50) {
            this.gridClient.stop(this.jobGroupID);
            this.progressEngine.unregisterStatusListener(this);
        }
    }

    public void start() throws Exception {
        if (this.singleThreaded) {
            this.runSingleThreaded();
        } else {
            this.runOnGrid();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void runSingleThreaded() throws Exception {
        ArrayList<JobClass> arrayList;
        TradingException tradingException = null;
        while ((arrayList = this.firstJobsGroup != null ? this.firstJobsGroup : this.createJobsBatch(this.batchSize, this.gridClient)) != null) {
            for (int i = 0; i < arrayList.size(); ++i) {
                GridJob gridJob = (GridJob)arrayList.get(i);
                this.progressEngine.checkPaused();
                if (this.progressEngine.isStopped()) {
                    return;
                }
                JobDetails jobDetails = new JobDetails(gridJob.getJobId());
                Serializable serializable = null;
                try {
                    long l = System.currentTimeMillis();
                    serializable = (Serializable)gridJob.call();
                    long l2 = System.currentTimeMillis() - l;
                    jobDetails.setDuration(l2);
                    this.processResult(serializable, jobDetails);
                    continue;
                }
                catch (TradingException tradingException2) {
                    Log.error("Trading exception during optimization", (Throwable)tradingException2);
                    tradingException = tradingException2;
                    continue;
                }
                catch (Throwable throwable) {
                    if ("BACKTESTNODE".equals(MainApp.getProduct())) {
                        jobDetails.setException(throwable.getMessage());
                    } else {
                        jobDetails.setException(SQUtils.getStackTrace((Throwable)throwable));
                    }
                    this.processResult(serializable, jobDetails);
                    Log.error("Error while running task #{}", (Object)i, (Object)throwable);
                    continue;
                }
                finally {
                    if (gridJob != null) {
                        gridJob.destroy();
                    }
                }
            }
        }
    }

    private void runOnGrid() throws Exception {
        ArrayList<JobClass> arrayList = this.firstJobsGroup != null ? this.firstJobsGroup : this.createJobsBatch(this.batchSize, this.gridClient);
        if (arrayList != null) {
            if (this.parentGridJob != null) {
                for (GridJob gridJob : arrayList) {
                    gridJob.setPriority(this.parentGridJob.getPriority() + 1);
                }
            }
            this.gridClient.executeOnGrid(this.jobGroupID, arrayList);
            if (this.parentGridJob != null) {
                this.gridClient.waitForFinish((Object)this, this.parentGridJob.getJobId(), this.parentGridJob.getJobGroupId(), this.jobGroupID);
            } else {
                this.gridClient.waitForFinish((Object)this, null, null, this.jobGroupID);
            }
            this.gridClient.removeMessageListener(this.jobGroupID);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected void processMessage(GridMessage gridMessage) {
        block14: {
            ArrayList<JobClass> arrayList;
            JobDetails jobDetails;
            try {
                if (gridMessage.getMessageID() == 1) {
                    jobDetails = gridMessage.getJobDetails();
                    arrayList = null;
                    if (gridMessage.getData() != null) {
                        arrayList = gridMessage.getData();
                    }
                    this.processResult(arrayList, jobDetails);
                    this.progressEngine.checkPaused();
                    if (this.progressEngine.isStopped()) {
                        this.gridClient.stop(this.jobGroupID);
                        return;
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Cannot process finished job", (Throwable)exception);
                this.onError("Cannot process finished job", exception);
            }
            try {
                if (gridMessage.getMessageID() != 1) break block14;
                jobDetails = this.gridClient;
                synchronized (jobDetails) {
                    if (this.gridClient.countAllJobs(this.jobGroupID) < (long)this.jobsCountThreshold && !this.progressEngine.isStopped()) {
                        arrayList = this.createJobsBatch(this.batchSize, this.gridClient);
                        if (arrayList != null) {
                            this.gridClient.executeOnGrid(this.jobGroupID, arrayList);
                        } else if (this.gridClient.countAllJobs(this.jobGroupID) == 0L && !this.progressEngine.isPaused()) {
                            this.gridClient.stop(this.jobGroupID);
                        }
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Cannot create new batch of jobs", (Throwable)exception);
                this.onError("Cannot create new batch of jobs", exception);
            }
        }
    }

    public boolean isStopped() {
        return false;
    }

    public boolean shouldRestart() {
        return this.gridClient.countAllJobs(this.jobGroupID) == 0L;
    }

    public void stopped() {
        this.gridClient.stop(this.jobGroupID);
    }

    public void addFirstJobsBatch(ArrayList<JobClass> arrayList) {
        this.firstJobsGroup = arrayList;
    }

    protected abstract ArrayList<JobClass> createJobsBatch(int var1, GridClient var2) throws Exception;

    protected abstract void processResult(ResultClass var1, JobDetails var2) throws Exception;

    protected abstract void onError(String var1, Exception var2);
}

