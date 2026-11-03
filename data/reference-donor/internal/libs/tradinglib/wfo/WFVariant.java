/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.wfo;

public class WFVariant {
    public String params;
    public short[] indexes;
    public int simulationOLHash;
    public String paramsFile;

    public WFVariant(String string, short[] sArray, String string2, int n) {
        this.params = string;
        this.indexes = sArray;
        this.paramsFile = string2;
        this.simulationOLHash = n;
    }
}

