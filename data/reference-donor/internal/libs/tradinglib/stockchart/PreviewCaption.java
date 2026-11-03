/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

public class PreviewCaption {
    private int index;
    private String caption;

    public PreviewCaption() {
    }

    public PreviewCaption(int n, String string) {
        this.index = n;
        this.caption = string;
    }

    public int getIndex() {
        return this.index;
    }

    public void setIndex(int n) {
        this.index = n;
    }

    public String getCaption() {
        return this.caption;
    }

    public void setCaption(String string) {
        this.caption = string;
    }
}

