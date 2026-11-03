/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.JobDetails
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.tradinglib.gp.GPIDs;
import java.io.Serializable;

public interface IGPNode
extends Serializable {
    public void setFitness(double var1, byte var3);

    public double getFitness(byte var1);

    public void destroy();

    public void setGPIDs(GPIDs var1);

    public GPIDs getGPIDs();

    public IGPNode clonePassed();

    public IGPNode cloneDismissed(int var1);

    public IGPNode cloneFull();

    public IGPNode cloneForMigration();

    public int getDismissalReason();

    public boolean passedEvaluation();

    public void setJobDetails(JobDetails var1);

    public JobDetails getJobDetails();

    public int getHash();

    public String getAsString();

    public void setFitness(IGPNode var1);

    public int getFingerprint();

    public Exception getException();

    public String getErrorMsg();
}

