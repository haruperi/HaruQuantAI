/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.memory.CpuInfo
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.jobslib;

import com.strategyquant.jobslib.JobCompletionListener;
import com.strategyquant.jobslib.JobsList;
import com.strategyquant.jobslib.SQJob;
import com.strategyquant.lib.memory.CpuInfo;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JobEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"JobEngine");
    private static JobEngine instance = null;
    private ExecutorService executor;
    private JobsList jobs = new JobsList();

    public static void init(JobEngine jobEngine) throws Exception {
        if (instance != null) {
            throw new Exception("JobEngine.init() called more than once!");
        }
        instance = jobEngine;
    }

    public JobEngine(int n) {
        if (n <= 0) {
            n = CpuInfo.getAvailableProcessors();
        }
        this.executor = Executors.newFixedThreadPool(n);
    }

    private static JobEngine get() {
        return instance;
    }

    public static void submit(ISQTask iSQTask, SQJob sQJob) {
        JobEngine.get()._submit(iSQTask, sQJob);
    }

    public static JobsList jobs() {
        return JobEngine.get()._jobs();
    }

    private JobsList _jobs() {
        return this.jobs;
    }

    private void _submit(ISQTask iSQTask, SQJob sQJob) {
        this._addJobToArray(iSQTask, sQJob);
        sQJob.addCompletionListener(new JobCompletionListener(){

            @Override
            public void onCompleted(SQJob sQJob) {
                JobEngine.this._removeFromArray(sQJob);
            }
        });
        this._executeJob(sQJob);
    }

    private void _executeJob(final SQJob sQJob) {
        this.executor.submit(new Runnable(){
            final /* synthetic */ JobEngine this$0;
            {
                this.this$0 = jobEngine;
            }

            @Override
            public void run() {
                sQJob.runWithCallback(this.this$0.executor);
            }
        }, this.executor);
    }

    private void _addJobToArray(ISQTask iSQTask, SQJob sQJob) {
        this.jobs.add(sQJob);
    }

    protected void _removeFromArray(SQJob sQJob) {
        this.jobs.remove(sQJob);
    }
}

