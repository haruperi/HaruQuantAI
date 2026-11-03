/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.order;

public interface IOrderListener {
    public void onOrderAdd(long var1, String var3, String var4, double var5, double var7);

    public void onOrderClosed(long var1);

    public void onOrderChanged(long var1, String var3, double var4, double var6);
}

