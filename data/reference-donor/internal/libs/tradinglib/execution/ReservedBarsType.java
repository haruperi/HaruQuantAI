/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.execution;

public class ReservedBarsType {
    public static final int LOAD_BACK = 1;
    public static final int LOAD_FROM = 2;
    public int type;
    public int minimumReservedBars;
    public int preferredReservedBars;

    public ReservedBarsType(int n, int n2, int n3) {
        this.type = n;
        this.minimumReservedBars = n2;
        this.preferredReservedBars = n3;
    }
}

