/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.JobDetails
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationIndexes
implements IGPNode {
    public static final Logger Log2 = LoggerFactory.getLogger((String)"OptimizationIndexes");
    private short[] indexes;
    private double fitness = -1.0;
    private GPIDs gpIDs = new GPIDs();
    private JobDetails jobDetails;
    private int dismissalReason;
    private ResultsGroup result = null;
    private String errorMsg;
    private Exception exception;

    public OptimizationIndexes(short[] sArray) {
        this.indexes = sArray;
    }

    @Override
    public void setFitness(double d, byte by) {
        this.fitness = d;
    }

    @Override
    public double getFitness(byte by) {
        return this.fitness;
    }

    @Override
    public void setGPIDs(GPIDs gPIDs) {
        this.gpIDs.set(gPIDs);
    }

    @Override
    public GPIDs getGPIDs() {
        return this.gpIDs;
    }

    @Override
    public void destroy() {
        if (this.result != null) {
            this.result.clear();
            this.result = null;
        }
    }

    public OptimizationIndexes clone() {
        OptimizationIndexes optimizationIndexes = new OptimizationIndexes(this.cloneArray(this.indexes));
        optimizationIndexes.fitness = this.fitness;
        optimizationIndexes.gpIDs.set(this.gpIDs);
        if (this.result != null) {
            optimizationIndexes.result = this.result.clone();
        }
        return optimizationIndexes;
    }

    @Override
    public IGPNode clonePassed() {
        return this.clone();
    }

    @Override
    public IGPNode cloneForMigration() {
        return this.clone();
    }

    @Override
    public IGPNode cloneDismissed(int n) {
        OptimizationIndexes optimizationIndexes = new OptimizationIndexes(this.cloneArray(this.indexes));
        optimizationIndexes.fitness = this.fitness;
        optimizationIndexes.gpIDs.set(this.gpIDs);
        optimizationIndexes.dismissalReason = this.dismissalReason;
        optimizationIndexes.result = null;
        return optimizationIndexes;
    }

    private short[] cloneArray(short[] sArray) {
        if (sArray == null) {
            return null;
        }
        short[] sArray2 = new short[sArray.length];
        for (int i = 0; i < sArray.length; ++i) {
            sArray2[i] = sArray[i];
        }
        return sArray2;
    }

    @Override
    public int getDismissalReason() {
        return this.dismissalReason;
    }

    @Override
    public boolean passedEvaluation() {
        return this.errorMsg == null;
    }

    public void setError(int n, String string, Exception exception) {
        this.fitness = 0.0;
        this.dismissalReason = n;
        this.errorMsg = string;
        this.exception = exception;
    }

    public static String convertToString(short[] sArray) {
        if (sArray == null) {
            return "[null]";
        }
        StringBuilder stringBuilder = new StringBuilder("[");
        for (int i = 0; i < sArray.length; ++i) {
            if (i > 0) {
                stringBuilder.append(",");
            }
            stringBuilder.append(String.format("%d", sArray[i]));
        }
        stringBuilder.append("]");
        return stringBuilder.toString();
    }

    @Override
    public String getErrorMsg() {
        return this.errorMsg;
    }

    @Override
    public void setJobDetails(JobDetails jobDetails) {
        this.jobDetails = jobDetails;
    }

    @Override
    public JobDetails getJobDetails() {
        return this.jobDetails;
    }

    public short[] getIndexes() {
        return this.indexes;
    }

    public void setIndexes(short[] sArray) {
        this.indexes = sArray;
    }

    public ResultsGroup getResult() {
        return this.result;
    }

    public void setResult(ResultsGroup resultsGroup) {
        this.result = resultsGroup;
    }

    public int getLength() {
        return this.indexes.length;
    }

    public boolean isSame(short[] sArray) {
        if (sArray == null || sArray.length != this.indexes.length) {
            return false;
        }
        for (int i = 0; i < this.indexes.length; ++i) {
            if (this.indexes[i] == sArray[i]) continue;
            return false;
        }
        return true;
    }

    @Override
    public int getHash() {
        return Arrays.hashCode(this.indexes);
    }

    @Override
    public String getAsString() {
        StringBuilder stringBuilder = new StringBuilder(this.gpIDs.toString());
        stringBuilder.append("[");
        for (int i = 0; i < this.indexes.length; ++i) {
            if (i > 0) {
                stringBuilder.append(",");
            }
            stringBuilder.append(this.indexes[i]);
        }
        stringBuilder.append("]");
        return stringBuilder.toString();
    }

    @Override
    public IGPNode cloneFull() {
        return null;
    }

    @Override
    public void setFitness(IGPNode iGPNode) {
        OptimizationIndexes optimizationIndexes = (OptimizationIndexes)iGPNode;
        this.fitness = optimizationIndexes.getFitness((byte)0);
        this.result = optimizationIndexes.getResult();
    }

    @Override
    public int getFingerprint() {
        return 0;
    }

    @Override
    public Exception getException() {
        return this.exception;
    }
}

