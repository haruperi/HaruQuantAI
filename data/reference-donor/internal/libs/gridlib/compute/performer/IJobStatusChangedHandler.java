/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.performer;

import com.strategyquant.gridlib.compute.JobResult;
import java.io.Serializable;

public interface IJobStatusChangedHandler {
    public void onJobFinished(String var1, String var2, JobResult<Serializable> var3);

    public void onJobExecuted(String var1, String var2);
}

