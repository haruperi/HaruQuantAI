/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals.entry;

import com.strategyquant.tradinglib.OrderTypes;

public class PickerEntrySignal {
    public String symbol;
    public byte type;
    public double price;
    public int barsValid;
    public double posScore;
    public double sl;
    public double pt;
    public int slptValidFrom;
    public int exitAfterBars;
    public byte eod = (byte)-1;
    private boolean used = true;

    public PickerEntrySignal(String string, byte by, double d, int n, double d2, double d3, int n2, int n3, byte by2) {
        this.symbol = string;
        this.type = by;
        this.price = d;
        this.sl = d2;
        this.pt = d3;
        this.slptValidFrom = n2;
        this.barsValid = n;
        this.exitAfterBars = n3;
        this.eod = by2;
        this.used = true;
    }

    public void init(String string, byte by, double d, int n, double d2, double d3, int n2, int n3, byte by2) {
        this.symbol = string;
        this.type = by;
        this.price = d;
        this.sl = d2;
        this.pt = d3;
        this.slptValidFrom = n2;
        this.barsValid = n;
        this.posScore = 0.0;
        this.exitAfterBars = n3;
        this.eod = by2;
        this.used = true;
    }

    public String toString() {
        StringBuffer stringBuffer = new StringBuffer(this.symbol);
        stringBuffer.append("=");
        stringBuffer.append(OrderTypes.toString(this.type));
        stringBuffer.append("(");
        stringBuffer.append(this.posScore);
        stringBuffer.append(")");
        return stringBuffer.toString();
    }

    public void setUnused() {
        this.used = false;
    }

    public boolean isUsed() {
        return this.used;
    }

    public byte getDirection() {
        return OrderTypes.isLongOrder(this.type) ? (byte)1 : -1;
    }
}

