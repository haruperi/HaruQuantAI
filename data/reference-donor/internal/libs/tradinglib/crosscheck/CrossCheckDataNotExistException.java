/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.crosscheck;

public class CrossCheckDataNotExistException
extends Exception {
    private String crossCheckName = null;

    public CrossCheckDataNotExistException(String string) {
        this.crossCheckName = string;
    }
}

