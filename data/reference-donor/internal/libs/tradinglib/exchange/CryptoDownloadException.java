/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.exchange;

public class CryptoDownloadException
extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final int code;

    public CryptoDownloadException(String string, int n) {
        super(string);
        this.code = n;
    }

    public int getCode() {
        return this.code;
    }
}

