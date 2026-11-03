/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.exception;

public class TaskErrorInfo {
    public String strategyName;
    public String exception;

    public TaskErrorInfo(String string, String string2) {
        this.strategyName = string;
        this.exception = string2;
    }
}

