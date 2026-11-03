/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib;

public class TradingException
extends Exception {
    public static final int IndicatorCalculationFailed = 55;
    private int errorCode;

    public TradingException() {
    }

    public TradingException(String string) {
        super(string);
    }

    public TradingException(String string, int n) {
        super(string);
        this.errorCode = n;
    }

    public int getErrorCode() {
        return this.errorCode;
    }

    public TradingException(Exception exception) {
        super(exception);
    }

    public TradingException(String string, Exception exception) {
        super(string, exception);
    }

    public TradingException addCall(String string) {
        return new TradingException(this.getMessage() + " - > " + string);
    }
}

