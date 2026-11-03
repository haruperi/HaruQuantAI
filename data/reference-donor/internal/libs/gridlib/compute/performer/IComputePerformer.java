/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.performer;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.compute.performer.IJobStatusChangedHandler;
import com.strategyquant.gridlib.topology.GridTopology;

public interface IComputePerformer
extends AutoCloseable {
    public void addJobFinishedHandler(IJobStatusChangedHandler var1);

    public void execute(GridJob<?> var1, String var2, ExecuteOptions var3) throws Exception;

    public void commit() throws Exception;

    public void pause(String var1) throws Exception;

    public void pause(String var1, String var2) throws Exception;

    public void stop(String var1) throws Exception;

    public void stop(String var1, String var2) throws Exception;

    public void restart(String var1) throws Exception;

    public void restart(String var1, String var2) throws Exception;

    public boolean sendMessageToJob(String var1, String var2, GridMessage var3) throws Exception;

    public GridTopology getGridTopology();

    public String getGridDescriptions();

    public void setProgress(String var1, String var2, int var3);

    public void setGroupRestrictions(String var1, int var2);

    public void check();

    public void setJobWaiting(String var1, String var2, boolean var3);

    public int getComputedThread();

    public int getUsedComputedThreads();

    public void setUsedComputedThreads(int var1);
}

