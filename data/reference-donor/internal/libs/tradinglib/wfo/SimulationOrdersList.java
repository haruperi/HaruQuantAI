/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.wfo;

public class SimulationOrdersList {
    public long[] openTime;
    public long[] closeTime;
    public byte[] type;
    public byte[] closeType;
    public float[] pL;
    public float[] size;
    public float[] openPrice;
    public float[] closePrice;
    public short[] barsInTrade;
    public String[] symbol;
    public float[] mae;
    public float[] mfe;
    public float[] commswap;
    public float[] stoploss;
    private int index = 0;
    private double checksum = 0.0;

    public SimulationOrdersList(int n) {
        this.openTime = new long[n];
        this.closeTime = new long[n];
        this.type = new byte[n];
        this.closeType = new byte[n];
        this.pL = new float[n];
        this.size = new float[n];
        this.openPrice = new float[n];
        this.closePrice = new float[n];
        this.barsInTrade = new short[n];
        this.symbol = new String[n];
        this.mae = new float[n];
        this.mfe = new float[n];
        this.commswap = new float[n];
        this.stoploss = new float[n];
    }

    public void add(long l, long l2, byte by, byte by2, float f, float f2, float f3, float f4, short s, String string, float f5, float f6, float f7, float f8) {
        this.openTime[this.index] = l;
        this.closeTime[this.index] = l2;
        this.type[this.index] = by;
        this.closeType[this.index] = by2;
        this.pL[this.index] = f;
        this.size[this.index] = f2;
        this.openPrice[this.index] = f3;
        this.closePrice[this.index] = f4;
        this.barsInTrade[this.index] = s;
        this.symbol[this.index] = string;
        this.mae[this.index] = f5;
        this.mfe[this.index] = f6;
        this.commswap[this.index] = f7;
        this.stoploss[this.index] = f8;
        ++this.index;
        this.checksum += (double)((float)(l + l2 + (long)by + (long)by2) + f + f2 + f3 + f4 + (float)s + (float)string.hashCode() + f5 + f6 + f7 + f8);
    }

    public int getHash() {
        return Double.hashCode(this.checksum);
    }
}

