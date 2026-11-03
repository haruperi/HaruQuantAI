/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.conditions;

public class DismissStruct {
    public String dismissMessage;
    public int dismissReason;

    public DismissStruct(int n, String string) {
        this.dismissReason = n;
        this.dismissMessage = string;
    }
}

