/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

public abstract class TimeDuration {
    public int seconds;
    public int value;

    public TimeDuration(int n) {
        this.value = n;
        this.seconds = this.toSeconds(n);
    }

    public abstract String toString();

    public abstract int toSeconds(int var1);
}

