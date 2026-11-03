/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.SQTime;

public class ChartOptimalizer {
    private static final long DAY = 86400000L;
    private static final int MAX = 2000;
    private long zoomMin;
    private long zoomMax;
    private Long dataMin;
    private Long dataMax;
    private long[] pixelGroupsX = new long[2000];
    private int[] pixelGroupsCount = new int[2000];
    private double[] pixelGroupsTotal = new double[2000];
    private boolean timeX;

    public OptimizerResult optimalize(boolean bl, long[] lArray, double[] dArray, Long l, Long l2, int n) {
        if (lArray.length != dArray.length) {
            throw new IllegalArgumentException("XVals and YVals must have same size.");
        }
        if (lArray.length == 0 || n < 0) {
            return new OptimizerResult(new long[0], new double[0]);
        }
        this.timeX = bl;
        this.zoomMin = l != null ? l : -1L;
        long l3 = this.zoomMax = l2 != null ? l2 : -1L;
        if (bl) {
            this.zoomMin = SQTime.correctDayStart((long)this.zoomMin);
            this.zoomMax = SQTime.correctDayStart((long)this.zoomMax);
        }
        this.countMinMax(lArray);
        return this.perform(lArray, dArray, n);
    }

    private OptimizerResult perform(long[] lArray, double[] dArray, int n) {
        int n2;
        double d;
        long l = this.dataMax - this.dataMin + 1L;
        if (n > 2000) {
            n = 2000;
        }
        if (this.timeX) {
            long l2 = l / 86400000L + 1L;
            if ((long)n >= l2) {
                d = 8.64E7;
            } else {
                double d2 = (double)l2 / (double)n;
                double d3 = Math.ceil(d2);
                d = 86400000L * (long)d3;
                if (d == 0.0) {
                    d = 8.64E7;
                }
            }
        } else {
            d = (double)l / (double)n;
        }
        int n3 = this.preparePixelGroups(n, d);
        int n4 = lArray.length;
        int n5 = -1;
        int n6 = -1;
        for (n2 = 0; n2 < n4; ++n2) {
            double d4;
            int n7;
            long l3 = lArray[n2];
            if (this.timeX) {
                l3 = SQTime.correctDayStart((long)l3);
            }
            if (!this.fit(l3)) continue;
            n5 = n2;
            if (n6 == -1) {
                n6 = n2;
            }
            if ((n7 = (int)Math.round(d4 = ((double)l3 - (double)this.dataMin.longValue()) / d)) >= n3) {
                n7 = n3 - 1;
            }
            if (n7 < 0) {
                n7 = 0;
            }
            int n8 = n7;
            this.pixelGroupsCount[n8] = this.pixelGroupsCount[n8] + 1;
            int n9 = n7;
            this.pixelGroupsTotal[n9] = this.pixelGroupsTotal[n9] + dArray[n2];
        }
        n2 = this.getPixelsCount();
        long[] lArray2 = new long[n2];
        double[] dArray2 = new double[n2];
        int n10 = 0;
        for (int i = 0; i < n3; ++i) {
            if (this.pixelGroupsCount[i] == 0) continue;
            lArray2[n10] = this.pixelGroupsX[i];
            dArray2[n10] = this.pixelGroupsTotal[i] / (double)this.pixelGroupsCount[i];
            ++n10;
        }
        if (n5 != -1) {
            dArray2[n2 - 1] = dArray[n5];
            lArray2[n2 - 1] = lArray[n5];
        }
        if (n6 != -1) {
            dArray2[0] = dArray[n6];
            lArray2[0] = lArray[n6];
        }
        this.cleanup();
        OptimizerResult optimizerResult = new OptimizerResult(lArray2, dArray2);
        return optimizerResult;
    }

    private void cleanup() {
        for (int i = 0; i < this.pixelGroupsCount.length; ++i) {
            this.pixelGroupsCount[i] = 0;
            this.pixelGroupsTotal[i] = 0.0;
            this.pixelGroupsX[i] = 0L;
        }
    }

    private int getPixelsCount() {
        int n = 0;
        for (int i = 0; i < this.pixelGroupsCount.length; ++i) {
            if (this.pixelGroupsCount[i] <= 0) continue;
            ++n;
        }
        return n;
    }

    private void countMinMax(long[] lArray) {
        long l = Long.MAX_VALUE;
        long l2 = Long.MIN_VALUE;
        for (long l3 : lArray) {
            if (l == Long.MAX_VALUE || l > l3) {
                l = l3;
            }
            if (l2 != Long.MIN_VALUE && l2 >= l3) continue;
            l2 = l3;
        }
        this.dataMin = l;
        this.dataMax = l2;
        if (this.timeX) {
            this.dataMin = SQTime.correctDayStart((long)this.dataMin);
            this.dataMax = SQTime.correctDayStart((long)this.dataMax);
        }
        if (this.zoomMin > 0L && this.dataMin < this.zoomMin) {
            this.dataMin = this.zoomMin;
        }
        if (this.zoomMax > 0L && this.dataMax > this.zoomMax) {
            this.dataMax = this.zoomMax;
        }
    }

    private boolean fit(long l) {
        if (this.zoomMin > 0L && this.zoomMax > 0L) {
            return l <= this.zoomMax && l >= this.zoomMin;
        }
        return true;
    }

    private int preparePixelGroups(int n, double d) {
        int n2 = 0;
        for (int i = 0; i < n; ++i) {
            long l;
            if (this.timeX) {
                l = this.dataMin + (long)d * (long)i;
            } else {
                double d2 = (double)this.dataMin.longValue() + d * (double)i;
                l = Math.round(d2);
            }
            this.pixelGroupsX[i] = l;
            ++n2;
        }
        return n2;
    }

    public static void main(String[] stringArray) {
        int n;
        int n2 = 10000000;
        long[] lArray = new long[n2];
        double[] dArray = new double[n2];
        for (n = 0; n < n2; ++n) {
            lArray[n] = n;
            dArray[n] = Math.random() * 1000.0;
        }
        n = 1000;
        System.out.println("Starting...");
        OptimizerResult optimizerResult = new ChartOptimalizer().optimalize(false, lArray, dArray, 0L, Long.valueOf(n), n);
        System.out.println("4. finished " + optimizerResult);
    }

    public static class OptimizerResult {
        public long[] xVals;
        public double[] yVals;

        public OptimizerResult() {
        }

        public OptimizerResult(long[] lArray, double[] dArray) {
            this.xVals = lArray;
            this.yVals = dArray;
        }

        public long[] getxVals() {
            return this.xVals;
        }

        public double[] getyVals() {
            return this.yVals;
        }

        public int size() {
            if (this.xVals == null) {
                return 0;
            }
            return this.xVals.length;
        }

        public String toString() {
            StringBuilder stringBuilder = new StringBuilder();
            for (int i = 0; i < this.xVals.length; ++i) {
                stringBuilder.append(this.xVals[i] + "," + this.yVals[i] + "\n");
            }
            return "Result[xVals:" + this.xVals.length + ", yVals:" + this.yVals.length + "]\n" + stringBuilder.toString();
        }
    }

    private static class PixelGroup {
        private long xValue;
        private double total = 0.0;
        private int count = 0;

        private PixelGroup() {
        }

        public void prepare(long l) {
            this.xValue = l;
        }

        public void reset() {
            this.count = 0;
            this.total = 0.0;
        }

        public void add(double d) {
            ++this.count;
            this.total += d;
        }

        public long getXValue() {
            return this.xValue;
        }

        public boolean hasValue() {
            return this.count != 0;
        }

        public double getYValues() {
            return this.total / (double)this.count;
        }
    }
}

