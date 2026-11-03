/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.data.download;

import com.strategyquant.tradinglib.data.download.DownloadDispatcher;

public interface IDownloadDispatcher {
    public void extecuteDownloadJob(DownloadDispatcher.Details var1) throws Exception;

    public boolean isCryptoExchangeDownload(String var1);

    public boolean isMt5DownloadExecuted();

    public void performStop(String var1, DownloadDispatcher.Details var2);

    public void performPause(String var1, DownloadDispatcher.Details var2);

    public void performResume(String var1, DownloadDispatcher.Details var2);
}

