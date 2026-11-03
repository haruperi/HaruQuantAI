/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.SQGrid;
import java.io.Serializable;
import java.util.Map;
import java.util.concurrent.Callable;

public abstract class GridJob<T>
implements Callable<T>,
Serializable {
    private static final long serialVersionUID = 1L;
    public static final int blocking_flag = 1;
    private String jobId;
    private Map<String, Serializable> parameters;
    private int flags;
    private String jobGroupId;
    private int priority;

    public GridJob(String string, int n, Map<String, Serializable> map) {
        this.jobId = string;
        this.flags = n;
        this.parameters = map;
    }

    public String getJobId() {
        return this.jobId;
    }

    public void messageReceived(GridMessage gridMessage) {
    }

    public Map<String, Serializable> getParameters() {
        return this.parameters;
    }

    public void destroy() {
    }

    public boolean isBlocking() {
        boolean bl = (this.flags & 1) != 0;
        return bl;
    }

    public int getPriority() {
        return this.priority;
    }

    public void setPriority(int n) {
        this.priority = n;
    }

    public int getFlags() {
        return this.flags;
    }

    public void sendProgress(int n) {
        SQGrid.getGridClient().sendProgress(this.getJobId(), this.jobGroupId, n);
    }

    public String getJobGroupId() {
        return this.jobGroupId;
    }

    public void setJobGroupId(String string) {
        this.jobGroupId = string;
    }
}

