/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.bartype.BarTypeFactory
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.dataseries.PreparedDataSeries
 *  com.strategyquant.datalib.dataseries.PreparedTimeDataSeries
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.dataseries.PreparedDataSeries;
import com.strategyquant.datalib.dataseries.PreparedTimeDataSeries;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.strategy.MarketData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PreparedChartData
extends ChartData {
    public static final Logger Log = LoggerFactory.getLogger((String)"ChartData");

    public PreparedChartData(ChartData chartData, MarketData marketData, TradingSetup tradingSetup, ChartDef chartDef, int n) throws DataException {
        this.serieIndex = chartData.getSerieIndex();
        this.connectionHash = chartData.getConnectionHash();
        this.symbolHash = chartData.getSymbolHash();
        if (marketData == null && chartDef == null) {
            return;
        }
        this.chartDef = chartDef;
        this.MarketData = marketData;
        this.Connection = chartDef.getConnectionName();
        this.Symbol = chartDef.getSymbol();
        this.Instrument = chartDef.getInstrument();
        this.connectionHash = chartDef.getConnectionHash();
        this.symbolHash = chartDef.getSymbolHash();
        this.Timeframe = chartDef.getTimeframe();
        this.session = chartDef.getSession();
        this.SymbolInfo = chartDef.getSymbolInfo();
        this.Time = new PreparedTimeDataSeries(chartData.Time, n);
        this.Open = new PreparedDataSeries(chartData.Open, n);
        this.High = new PreparedDataSeries(chartData.High, n);
        this.Low = new PreparedDataSeries(chartData.Low, n);
        this.Close = new PreparedDataSeries(chartData.Close, n);
        this.Volume = new PreparedDataSeries(chartData.Volume, n);
        if (this.usesSameDailyDataSeries()) {
            this.TimeD = this.Time;
            this.OpenD = this.Open;
            this.HighD = this.High;
            this.LowD = this.Low;
            this.CloseD = this.Close;
            this.TimeW = this.Time;
            this.OpenW = this.Open;
            this.HighW = this.High;
            this.LowW = this.Low;
            this.CloseW = this.Close;
            this.TimeM = this.Time;
            this.OpenM = this.Open;
            this.HighM = this.High;
            this.LowM = this.Low;
            this.CloseM = this.Close;
        } else {
            this.TimeD = null;
            this.OpenD = null;
            this.HighD = null;
            this.LowD = null;
            this.CloseD = null;
            this.TimeW = null;
            this.OpenW = null;
            this.HighW = null;
            this.LowW = null;
            this.CloseW = null;
            this.TimeM = null;
            this.OpenM = null;
            this.HighM = null;
            this.LowM = null;
            this.CloseM = null;
        }
        this.Time.setShift(0);
        int n2 = this.Time.size();
        this.Time.setShift(n2 - 1);
        this.initializeComputedDataSeries();
        this.barType = BarTypeFactory.getBarType((String)this.Timeframe, (int)chartDef.getBarTimeType()).clone();
        if (n > 0) {
            this.setIndyStartingBar(n);
        } else {
            this.setIndyStartingBar(chartData.getIndyStartingBar());
        }
    }

    @Override
    public void destroy() {
        if (!this.usesSameDailyDataSeries()) {
            if (this.TimeD != null) {
                this.TimeD.destroy();
                this.TimeD = null;
            }
            if (this.OpenD != null) {
                this.OpenD.destroy();
                this.OpenD = null;
            }
            if (this.HighD != null) {
                this.HighD.destroy();
                this.HighD = null;
            }
            if (this.LowD != null) {
                this.LowD.destroy();
                this.LowD = null;
            }
            if (this.CloseD != null) {
                this.CloseD.destroy();
                this.CloseD = null;
            }
            if (this.TimeW != null) {
                this.TimeW.destroy();
                this.TimeW = null;
            }
            if (this.OpenW != null) {
                this.OpenW.destroy();
                this.OpenW = null;
            }
            if (this.HighW != null) {
                this.HighW.destroy();
                this.HighW = null;
            }
            if (this.LowW != null) {
                this.LowW.destroy();
                this.LowW = null;
            }
            if (this.CloseW != null) {
                this.CloseW.destroy();
                this.CloseW = null;
            }
            if (this.TimeM != null) {
                this.TimeM.destroy();
                this.TimeM = null;
            }
            if (this.OpenM != null) {
                this.OpenM.destroy();
                this.OpenM = null;
            }
            if (this.HighM != null) {
                this.HighM.destroy();
                this.HighM = null;
            }
            if (this.LowM != null) {
                this.LowM.destroy();
                this.LowM = null;
            }
            if (this.CloseM != null) {
                this.CloseM.destroy();
                this.CloseM = null;
            }
        }
        if (this.Median != null) {
            this.Median.destroy();
            this.Median = null;
        }
        if (this.Typical != null) {
            this.Typical.destroy();
            this.Typical = null;
        }
        if (this.Weighted != null) {
            this.Weighted.destroy();
            this.Weighted = null;
        }
    }
}

