/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.tradinglib.ChartData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MarketPriceHolder {
    public static final Logger Log = LoggerFactory.getLogger((String)"AbstractTradingSimulator");
    private TwoTickEvents[] tickData = new TwoTickEvents[4];
    private TickEvent oneSymbolCurrentTick = new TickEvent();
    private int oneSymbolHash;
    private ChartData oneSymbolChartData;
    private int symbolsCount = 0;

    public void registerNewSymbol(ChartData chartData) {
        int n = chartData.getSymbolHash();
        if (this.containsSymbol(n)) {
            return;
        }
        if (this.symbolsCount == this.tickData.length - 1) {
            this.resizeArray();
        }
        this.tickData[this.symbolsCount] = new TwoTickEvents(n, chartData);
        ++this.symbolsCount;
        if (this.symbolsCount == 1) {
            this.oneSymbolHash = n;
            this.oneSymbolChartData = chartData;
        }
    }

    private void resizeArray() {
        TwoTickEvents[] twoTickEventsArray = new TwoTickEvents[this.tickData.length + 5];
        for (int i = 0; i < this.tickData.length; ++i) {
            twoTickEventsArray[i] = this.tickData[i];
        }
        this.tickData = twoTickEventsArray;
    }

    public boolean containsSymbol(int n) {
        if (this.symbolsCount == 0) {
            return false;
        }
        if (this.symbolsCount == 1) {
            return this.oneSymbolHash == n;
        }
        for (int i = 0; i < this.symbolsCount; ++i) {
            if (this.tickData[i].symbolHash != n) continue;
            return true;
        }
        return false;
    }

    public TickEvent setNewTick(int n, TickEvent tickEvent) {
        if (this.symbolsCount == 0) {
            return null;
        }
        if (this.symbolsCount == 1) {
            if (this.oneSymbolHash != n) {
                return null;
            }
            this.oneSymbolCurrentTick.copyValues(tickEvent);
            return this.oneSymbolCurrentTick;
        }
        for (int i = 0; i < this.symbolsCount; ++i) {
            if (this.tickData[i].symbolHash != n) continue;
            this.tickData[i].setNewTick(tickEvent);
            return this.tickData[i].current;
        }
        return null;
    }

    public TickEvent getCurrentTick(int n) {
        if (this.symbolsCount == 1 && this.oneSymbolHash == n) {
            return this.oneSymbolCurrentTick;
        }
        TwoTickEvents twoTickEvents = this.getTickData(n);
        return twoTickEvents.current;
    }

    private TwoTickEvents getTickData(int n) {
        if (this.symbolsCount == 0) {
            throw new IllegalArgumentException("Symbol with this hash doesn't exist (1)!");
        }
        if (this.symbolsCount == 1) {
            if (this.tickData[0].symbolHash != n) {
                throw new IllegalArgumentException("Symbol with this hash doesn't exist (2)!");
            }
            return this.tickData[0];
        }
        for (int i = 0; i < this.symbolsCount; ++i) {
            if (this.tickData[i].symbolHash != n) continue;
            return this.tickData[i];
        }
        throw new IllegalArgumentException("Symbol with this hash doesn't exist (2)!");
    }

    private boolean notInitialized(TickEvent tickEvent) {
        return tickEvent.getTime() == -1L;
    }

    public ChartData getChartData(int n) {
        if (this.symbolsCount == 1 && this.oneSymbolHash == n) {
            return this.oneSymbolChartData;
        }
        TwoTickEvents twoTickEvents = this.getTickData(n);
        return twoTickEvents.chartData;
    }

    class TwoTickEvents {
        ChartData chartData;
        TickEvent current = new TickEvent();
        int symbolHash;

        public TwoTickEvents(int n, ChartData chartData) {
            this.chartData = chartData;
            this.symbolHash = n;
        }

        public void setNewTick(TickEvent tickEvent) {
            this.current.copyValues(tickEvent);
        }
    }
}

