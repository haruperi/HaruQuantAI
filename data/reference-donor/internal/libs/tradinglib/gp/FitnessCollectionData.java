/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.SQUtils;

public class FitnessCollectionData {
    private int generation;
    public double bestFitnessIS;
    public double bestFitnessIST;
    public double bestFitnessISV;
    public double bestFitnessOOS;
    public double bestFitnessFS;
    public double topAvgFitnessIS;
    public double topAvgFitnessIST;
    public double topAvgFitnessISV;
    public double topAvgFitnessOOS;
    public double topAvgFitnessFS;
    public double avgFitnessIS;
    public double avgFitnessIST;
    public double avgFitnessISV;
    public double avgFitnessOOS;
    public double avgFitnessFS;

    public FitnessCollectionData(int n) {
        this.generation = n;
    }

    public void reset() {
        this.bestFitnessIS = 0.0;
        this.bestFitnessISV = 0.0;
        this.bestFitnessIST = 0.0;
        this.bestFitnessOOS = 0.0;
        this.bestFitnessFS = 0.0;
        this.topAvgFitnessIS = 0.0;
        this.topAvgFitnessISV = 0.0;
        this.topAvgFitnessIST = 0.0;
        this.topAvgFitnessOOS = 0.0;
        this.topAvgFitnessFS = 0.0;
        this.avgFitnessIS = 0.0;
        this.avgFitnessISV = 0.0;
        this.avgFitnessIST = 0.0;
        this.avgFitnessOOS = 0.0;
        this.avgFitnessFS = 0.0;
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("\nBST IS:");
        stringBuilder.append(SQUtils.round2((double)this.bestFitnessIS));
        stringBuilder.append(", ISV:");
        stringBuilder.append(SQUtils.round2((double)this.bestFitnessISV));
        stringBuilder.append(", IST:");
        stringBuilder.append(SQUtils.round2((double)this.bestFitnessIST));
        stringBuilder.append(", OOS:");
        stringBuilder.append(SQUtils.round2((double)this.bestFitnessOOS));
        stringBuilder.append(", FS:");
        stringBuilder.append(SQUtils.round2((double)this.bestFitnessFS));
        stringBuilder.append("\n");
        stringBuilder.append("TOP IS:");
        stringBuilder.append(SQUtils.round2((double)this.topAvgFitnessIS));
        stringBuilder.append(", ISV:");
        stringBuilder.append(SQUtils.round2((double)this.topAvgFitnessISV));
        stringBuilder.append(", IST:");
        stringBuilder.append(SQUtils.round2((double)this.topAvgFitnessIST));
        stringBuilder.append(", OOS:");
        stringBuilder.append(SQUtils.round2((double)this.topAvgFitnessOOS));
        stringBuilder.append(", FS:");
        stringBuilder.append(SQUtils.round2((double)this.topAvgFitnessFS));
        stringBuilder.append("\n");
        stringBuilder.append("AVG IS:");
        stringBuilder.append(SQUtils.round2((double)this.avgFitnessIS));
        stringBuilder.append(", ISV:");
        stringBuilder.append(SQUtils.round2((double)this.avgFitnessISV));
        stringBuilder.append(", IST:");
        stringBuilder.append(SQUtils.round2((double)this.avgFitnessIST));
        stringBuilder.append(", OOS:");
        stringBuilder.append(SQUtils.round2((double)this.avgFitnessOOS));
        stringBuilder.append(", FS:");
        stringBuilder.append(SQUtils.round2((double)this.avgFitnessFS));
        stringBuilder.append("\n");
        stringBuilder.append("-----------------------------------");
        return stringBuilder.toString();
    }
}

