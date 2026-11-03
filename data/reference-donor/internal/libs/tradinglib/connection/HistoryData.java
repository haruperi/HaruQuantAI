/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.io.VersatileData;
import java.util.ArrayList;

public class HistoryData {
    public static final int TypeTick = 0;
    public static final int TypeMinute = 1;
    private ChartDef chart;
    private int type;
    private long fromTime;
    private long toTime;
    private ArrayList<VersatileData> data = new ArrayList();

    public HistoryData(ChartDef chartDef, int n, long l, long l2) {
        this.chart = chartDef;
        this.type = n;
        this.fromTime = l;
        this.toTime = l2;
    }

    public void addMinuteData(long l, double d, double d2, double d3, double d4, double d5) {
        VersatileData versatileData = new VersatileData();
        versatileData.set(2, l, this.chart.getConnectionHash(), this.chart.getSymbolHash(), d, d2, d3, d4, d5);
        this.data.add(versatileData);
    }

    public ArrayList<VersatileData> getData() {
        return this.data;
    }
}

