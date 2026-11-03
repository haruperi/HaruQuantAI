/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

public class NotEnoughSpaceException
extends Exception {
    public static final int TOO_MANY_TESTS = 1;
    public static final int NO_DISC_SPACE = 2;
    private int reason = 0;

    public NotEnoughSpaceException(int n, String string) {
        super(string);
        this.reason = n;
    }
}

