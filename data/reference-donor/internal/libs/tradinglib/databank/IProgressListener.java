/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.databank;

public interface IProgressListener {
    public void onProgress(double var1);

    public void onDone();

    public void onError(double var1, String var3);
}

