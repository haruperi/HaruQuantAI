/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.jobslib;

import com.strategyquant.jobslib.JobCompletionListener;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.atomic.AtomicInteger;

public abstract class SQJob {
    public static final int ErrorNone = 0;
    public static final int ErrorException = 1;
    private static final int RunningStatus_BeforeRun = 0;
    private static final int RunningStatus_Running = 1;
    private static final int RunningStatus_Finished = 2;
    public static final int JobStatus_None = 0;
    public static final int JobStatus_Success = 1;
    public static final int JobStatus_Error = 2;
    private AtomicInteger runningStatus = new AtomicInteger(0);
    private AtomicInteger status = new AtomicInteger(0);
    private Object result = null;
    private Exception exception = null;
    private ArrayList<JobCompletionListener> listeners = new ArrayList();

    public void addCompletionListener(JobCompletionListener jobCompletionListener) {
        this.listeners.add(jobCompletionListener);
    }

    protected void setResult(Object object) {
        this.result = object;
    }

    private void callCompletionListeners(ExecutorService executorService) {
        for (JobCompletionListener jobCompletionListener : this.listeners) {
            executorService.submit(new Listener(this, jobCompletionListener));
        }
    }

    void runWithCallback(ExecutorService executorService) {
        try {
            this.runningStatus.set(1);
            this.run();
            this.status.set(1);
        }
        catch (Exception exception) {
            this.status.set(2);
            this.exception = exception;
        }
        finally {
            this.runningStatus.set(2);
            this.callCompletionListeners(executorService);
        }
    }

    public int getId() {
        return System.identityHashCode(this);
    }

    public int getStatus() {
        return this.status.get();
    }

    public boolean isFinished() {
        return this.runningStatus.get() == 2;
    }

    public boolean isRunning() {
        return this.runningStatus.get() == 1;
    }

    public Object getResult() {
        return this.result;
    }

    public abstract void run() throws Exception;

    class Listener
    implements Runnable {
        private SQJob job;
        private JobCompletionListener listener;

        public Listener(SQJob sQJob2, JobCompletionListener jobCompletionListener) {
            this.job = sQJob2;
            this.listener = jobCompletionListener;
        }

        @Override
        public void run() {
            this.listener.onCompleted(this.job);
        }
    }
}

