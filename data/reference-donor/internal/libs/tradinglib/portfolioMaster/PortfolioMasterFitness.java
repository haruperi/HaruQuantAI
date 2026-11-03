/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.portfolioMaster;

import com.strategyquant.tradinglib.IFitnessValue;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.debug.Debugger;

public abstract class PortfolioMasterFitness
extends Debugger
implements IFitnessValue {
    public static String SampleKeyIS = "IS";
    public static String SampleKeyFull = "Full";
    protected String name = null;
    protected byte valueType = 1;
    private double target;
    private double avgMin;
    private double avgMax;

    public PortfolioMasterFitness(String string, byte by, double d, double d2, double d3) {
        this.name = string;
        this.valueType = by;
        this.target = d;
        this.avgMin = d2;
        this.avgMax = d3;
    }

    public String getName() {
        return this.name;
    }

    public int getValueType() {
        return this.valueType;
    }

    public abstract double compute(ResultsGroup var1, byte var2) throws Exception;

    public double transformToFitnessRange(double d) throws Exception {
        double d2 = this.transformToFitnessRange(d, this.target, this.avgMin, this.avgMax, this.valueType);
        if (d2 < 0.0) {
            d2 = 0.0;
        }
        if (d2 > 1.0) {
            d2 = 1.0;
        }
        return d2;
    }

    public abstract String print(double var1) throws Exception;
}

