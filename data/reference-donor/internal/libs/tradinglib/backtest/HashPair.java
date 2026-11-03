/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtest;

public class HashPair {
    public int connectionHash;
    public int symbolHash;

    public HashPair(int n, int n2) {
        this.connectionHash = n;
        this.symbolHash = n2;
    }

    public HashPair() {
    }
}

