/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.exception;

public class StrategyProblem {
    public int code;
    public String shortInfo;
    public String longInfo;

    public StrategyProblem(int n, String string, String string2) {
        this.code = n;
        this.shortInfo = string;
        this.longInfo = string2;
    }
}

