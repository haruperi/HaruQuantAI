/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.gridlib.compute.common.RingBuffer
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.quality;

import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.gridlib.compute.common.RingBuffer;
import com.strategyquant.lib.SQTime;

public class DataProblemEvaluator {
    private static final int AVERAGE_COUNT = 30;
    private static final double SPIKE_CHECK_MULTIPLICATOR = 5.0;
    private long lastTime = -1L;
    private int lastDayOfWeek = -1;
    private int minHour;
    private int maxHour;
    private long milisForTimeframe;
    private long beginGap = -1L;
    private long endGap = -1L;
    private long storedCount = 0L;
    private RingBuffer<Double> ringBuffer = new RingBuffer(30);
    private double lastOpen;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ProblemKind evalProblemKind(VersatileData versatileData, boolean bl) {
        int n = SQTime.getDayOfWeek((long)versatileData.time);
        try {
            if (!bl && !this.checkGap(versatileData.time, n)) {
                ProblemKind problemKind = ProblemKind.GAP;
                return problemKind;
            }
            if (!this.checkLow(versatileData)) {
                ProblemKind problemKind = ProblemKind.LOW_PROBLEM;
                return problemKind;
            }
            if (!this.checkHigh(versatileData)) {
                ProblemKind problemKind = ProblemKind.HIGH_PROBLEM;
                return problemKind;
            }
            if (!this.checkOpenSpike(versatileData)) {
                ProblemKind problemKind = ProblemKind.SPIKE;
                return problemKind;
            }
            ProblemKind problemKind = null;
            return problemKind;
        }
        finally {
            this.storeLast(versatileData, n);
        }
    }

    public long getMilisForTimeframe() {
        return this.milisForTimeframe;
    }

    public long getBeginGap() {
        return this.beginGap;
    }

    public long getEndGap() {
        return this.endGap;
    }

    private boolean checkGap(long l, int n) {
        if (this.lastTime == -1L || n == 7) {
            return true;
        }
        if (n != this.lastDayOfWeek) {
            if (this.lastDayOfWeek != -1 && this.lastDayOfWeek != 7 && SQTime.getHour((long)this.lastTime) < this.maxHour) {
                this.beginGap = this.lastTime + this.milisForTimeframe;
                this.endGap = SQTime.setHour((long)this.lastTime, (int)this.maxHour);
                return false;
            }
            int n2 = SQTime.getHour((long)l);
            if (n2 != this.minHour) {
                this.beginGap = SQTime.setHour((long)l, (int)this.minHour);
                this.endGap = l - this.milisForTimeframe;
                return false;
            }
            return true;
        }
        long l2 = l - this.lastTime;
        if (l2 > this.milisForTimeframe) {
            this.beginGap = this.lastTime + this.milisForTimeframe;
            this.endGap = l - this.milisForTimeframe;
            return false;
        }
        return true;
    }

    private boolean checkOpenSpike(VersatileData versatileData) {
        if (this.storedCount < 30L) {
            return true;
        }
        double d = 0.0;
        for (Double d2 : this.ringBuffer) {
            d += d2.doubleValue();
        }
        double d3 = d / 30.0;
        double d4 = 5.0 * d3;
        double d5 = Math.abs(versatileData.high - versatileData.low);
        boolean bl = d5 < d4;
        return bl;
    }

    private void storeLast(VersatileData versatileData, int n) {
        this.lastTime = versatileData.time;
        this.lastOpen = versatileData.open;
        this.lastDayOfWeek = n;
        this.ringBuffer.add((Object)Math.abs(versatileData.high - versatileData.low));
        ++this.storedCount;
    }

    private boolean checkHigh(VersatileData versatileData) {
        return !(versatileData.high < versatileData.low) && !(versatileData.high < versatileData.open) && !(versatileData.high < versatileData.close);
    }

    private boolean checkLow(VersatileData versatileData) {
        return !(versatileData.low > versatileData.high) && !(versatileData.low > versatileData.open) && !(versatileData.low > versatileData.close);
    }

    public void setMinMaxHour(int n, int n2) {
        this.minHour = n;
        this.maxHour = n2;
    }

    public void setTimeframe(String string) throws TradingException {
        this.milisForTimeframe = TimeframeManager.getMillis((String)string);
        if (this.milisForTimeframe == 0L) {
            throw new IllegalArgumentException("Not supported timeframe:" + string);
        }
    }

    public static enum ProblemKind {
        GAP("gap"),
        LOW_PROBLEM("bad OHLC - low value"),
        HIGH_PROBLEM("bad OHLC - high value"),
        SPIKE("Spike - this candle is more than 5x bigger than average");

        private String desc;

        private ProblemKind(String string2) {
            this.desc = string2;
        }

        public String getDesc() {
            return this.desc;
        }
    }
}

