/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.data.download;

import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;

public class SpeedEvaluator {
    private static final double NANO_TO_SECS = 1.0E9;
    private static final double KBS_CONST = 1024.0;
    private volatile int avgDownloadSpeedCounter = 0;
    private volatile double avgDownloadSpeed = 0.0;
    private Object downloadSpeedLock = new Object();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void evalSpeed(DownloadResultDto downloadResultDto) {
        long l = downloadResultDto.getDownloadedSize();
        long l2 = downloadResultDto.getDuration();
        if (l > 0L && l2 > 0L) {
            Object object = this.downloadSpeedLock;
            synchronized (object) {
                double d = (double)l * 8.0 / 1024.0 / ((double)l2 / 1.0E9);
                this.avgDownloadSpeed += d;
                ++this.avgDownloadSpeedCounter;
            }
        }
    }

    public void reset() {
        this.avgDownloadSpeedCounter = 0;
        this.avgDownloadSpeed = 0.0;
    }

    public String getSpeed() {
        double d = this.avgDownloadSpeed / (double)this.avgDownloadSpeedCounter;
        String string = "Kbps";
        if (d > 1024.0) {
            string = "Mbps";
            d /= 1024.0;
        }
        double d2 = (double)Math.round(d * 10.0) / 10.0;
        String string2 = d2 + string;
        return string2;
    }
}

