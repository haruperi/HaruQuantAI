/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.connection;

public interface IConnectionListener {
    public void onConnectionAdd(String var1, String var2, String var3, int var4, double var5, double var7, String var9);

    public void onConnectionPLChange(String var1, double var2);

    public void onConnectionAccountBalanceChange(String var1, double var2);

    public void onConnectionOpenOrdersChange(String var1, int var2);

    public void onConnectionStateChange(String var1, String var2);

    public void onConnectionError(String var1, Exception var2);

    public void onConnectionRemove(String var1);
}

