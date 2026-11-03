/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.tradinglib.stockchart.Indicator;
import com.strategyquant.tradinglib.stockchart.Trade;
import java.util.List;

public class StockChartData {
    private String title;
    private List<Double> open;
    private List<Double> close;
    private List<Double> high;
    private List<Double> low;
    private long[] xVals;
    private Indicator[] indicators;
    private Trade[] trades;
    private int precision = 5;

    public Trade[] getTrades() {
        return this.trades;
    }

    public void setTrades(Trade[] tradeArray) {
        this.trades = tradeArray;
    }

    public String getTitle() {
        return this.title;
    }

    public void setTitle(String string) {
        this.title = string;
    }

    public List<Double> getOpen() {
        return this.open;
    }

    public void setOpen(List<Double> list) {
        this.open = list;
    }

    public List<Double> getClose() {
        return this.close;
    }

    public void setClose(List<Double> list) {
        this.close = list;
    }

    public List<Double> getHigh() {
        return this.high;
    }

    public void setHigh(List<Double> list) {
        this.high = list;
    }

    public List<Double> getLow() {
        return this.low;
    }

    public void setLow(List<Double> list) {
        this.low = list;
    }

    public Indicator[] getIndicators() {
        return this.indicators;
    }

    public void setIndicators(Indicator[] indicatorArray) {
        this.indicators = indicatorArray;
    }

    public long[] getxVals() {
        return this.xVals;
    }

    public void setxVals(long[] lArray) {
        this.xVals = lArray;
    }

    public int getPrecision() {
        return this.precision;
    }

    public void setPrecision(int n) {
        this.precision = n;
    }
}

