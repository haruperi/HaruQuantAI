/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.backtester;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.signals.CollectedSignals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.Signals;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestData {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestData");
    private String symbol;
    private LoadedPickerData pickerData;
    private CollectedSignals signals;
    private ChartSetup chartSetup;
    private int currentBarD;
    private int currentBarW;
    private int currentBarM;

    public BacktestData(ChartSetup chartSetup, LoadedPickerData loadedPickerData, CollectedSignals collectedSignals) {
        this.chartSetup = chartSetup;
        this.pickerData = loadedPickerData;
        this.signals = collectedSignals;
        this.currentBarD = 0;
        this.currentBarW = 0;
        this.currentBarM = 0;
    }

    public double Open(int n, int n2) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.getChartData(n);
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return loadedSymbolData.OpenD(this.currentBarD - n2);
            }
            case "Weekly": {
                return loadedSymbolData.OpenW(this.currentBarW - n2);
            }
            case "Monthly": {
                return loadedSymbolData.OpenM(this.currentBarM - n2);
            }
        }
        return 0.0;
    }

    public double OpenD(int n, int n2) throws TradingException {
        return this.getChartData(n).OpenD(this.currentBarD - n2);
    }

    public double OpenW(int n, int n2) throws TradingException {
        return this.getChartData(n).OpenW(this.currentBarW - n2);
    }

    public double OpenM(int n, int n2) throws TradingException {
        return this.getChartData(n).OpenM(this.currentBarM - n2);
    }

    public double Close(int n, int n2) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.getChartData(n);
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return loadedSymbolData.CloseD(this.currentBarD - n2);
            }
            case "Weekly": {
                return loadedSymbolData.CloseW(this.currentBarW - n2);
            }
            case "Monthly": {
                return loadedSymbolData.CloseM(this.currentBarM - n2);
            }
        }
        return 0.0;
    }

    public double CloseD(int n, int n2) throws TradingException {
        return this.getChartData(n).CloseD(this.currentBarD - n2);
    }

    public double CloseW(int n, int n2) throws TradingException {
        return this.getChartData(n).CloseW(this.currentBarW - n2);
    }

    public double CloseM(int n, int n2) throws TradingException {
        return this.getChartData(n).CloseM(this.currentBarM - n2);
    }

    public double High(int n, int n2) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.getChartData(n);
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return loadedSymbolData.HighD(this.currentBarD - n2);
            }
            case "Weekly": {
                return loadedSymbolData.HighW(this.currentBarW - n2);
            }
            case "Monthly": {
                return loadedSymbolData.HighM(this.currentBarM - n2);
            }
        }
        return 0.0;
    }

    public double HighD(int n, int n2) throws TradingException {
        return this.getChartData(n).HighD(this.currentBarD - n2);
    }

    public double HighW(int n, int n2) throws TradingException {
        return this.getChartData(n).HighW(this.currentBarW - n2);
    }

    public double HighM(int n, int n2) throws TradingException {
        return this.getChartData(n).HighM(this.currentBarM - n2);
    }

    public double Low(int n, int n2) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.getChartData(n);
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return loadedSymbolData.LowD(this.currentBarD - n2);
            }
            case "Weekly": {
                return loadedSymbolData.LowW(this.currentBarW - n2);
            }
            case "Monthly": {
                return loadedSymbolData.LowM(this.currentBarM - n2);
            }
        }
        return 0.0;
    }

    public double LowD(int n, int n2) throws TradingException {
        return this.getChartData(n).LowD(this.currentBarD - n2);
    }

    public double LowW(int n, int n2) throws TradingException {
        return this.getChartData(n).LowW(this.currentBarW - n2);
    }

    public double LowM(int n, int n2) throws TradingException {
        return this.getChartData(n).LowM(this.currentBarM - n2);
    }

    public double VolumeD(int n, int n2) throws TradingException {
        return this.getChartData(n).VolumeD(this.currentBarD - n2);
    }

    public double VolumeW(int n, int n2) throws TradingException {
        return this.getChartData(n).VolumeW(this.currentBarW - n2);
    }

    public double VolumeM(int n, int n2) throws TradingException {
        return this.getChartData(n).VolumeM(this.currentBarM - n2);
    }

    public long TimeD(int n) throws TradingException {
        return this.pickerData.timeline.indexToTimeD(this.currentBarD - n);
    }

    public long TimeW(int n) throws TradingException {
        return this.pickerData.timeline.indexToTimeW(this.currentBarW - n);
    }

    public long TimeM(int n) throws TradingException {
        return this.pickerData.timeline.indexToTimeM(this.currentBarM - n);
    }

    public LoadedSymbolData getChartData(int n) {
        if (n == 0 || this.pickerData.additionalData.get(n - 1) == null) {
            return this.pickerData.stockGroupData.getSymbolData(this.symbol);
        }
        return (LoadedSymbolData)this.pickerData.additionalData.get(n - 1);
    }

    public LoadedSymbolData getChartSymbolData(int n, String string) {
        if (n == 0 || this.pickerData.additionalData.get(n - 1) == null) {
            return this.pickerData.stockGroupData.getSymbolData(string);
        }
        return (LoadedSymbolData)this.pickerData.additionalData.get(n - 1);
    }

    public String getChartTimeframe(int n) {
        ChartDef chartDef = this.chartSetup.getCharts().get(n);
        return chartDef.getTimeframe();
    }

    public void setCurrentBar(int n) throws TradingException {
        this.currentBarD = n;
        long l = this.pickerData.timeline.indexToTimeD(n);
        long l2 = SQTime.setFirstDayOfWeek((long)l);
        long l3 = SQTime.setDayOfMonth((long)l, (int)1);
        this.currentBarW = this.pickerData.timeline.timeToIndexW(l2);
        this.currentBarM = this.pickerData.timeline.timeToIndexM(l3);
    }

    public double Volume(int n, int n2) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.getChartData(n);
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return loadedSymbolData.VolumeD(this.currentBarD - n2);
            }
            case "Weekly": {
                return loadedSymbolData.VolumeW(this.currentBarW - n2);
            }
            case "Monthly": {
                return loadedSymbolData.VolumeM(this.currentBarM - n2);
            }
        }
        return 0.0;
    }

    public int getCurrentBar(int n) {
        switch (this.getChartTimeframe(n)) {
            case "D1": {
                return this.currentBarD;
            }
            case "Weekly": {
                return this.currentBarW;
            }
            case "Monthly": {
                return this.currentBarM;
            }
        }
        return 0;
    }

    public long getCurrentTime() throws TradingException {
        return this.pickerData.timeline.indexToTimeD(this.currentBarD);
    }

    public long getTime(int n) throws TradingException {
        return this.pickerData.timeline.indexToTimeD(this.currentBarD - n);
    }

    public int getCurrentBar() {
        return this.currentBarD;
    }

    public LoadedPickerData getPickerData() {
        return this.pickerData;
    }

    public LoadedStockGroupData getStockGroupData() {
        return this.pickerData.stockGroupData;
    }

    public Signals Signals(long l, boolean bl) {
        if (!this.signals.containsKey(l) && bl) {
            this.signals.put(l, new Signals());
        }
        return (Signals)this.signals.get(l);
    }

    public String getSymbol(int n) {
        String string;
        if (n == 0) {
            return this.symbol;
        }
        ChartDef chartDef = this.chartSetup.getCharts().get(n);
        String string2 = chartDef.getSymbol();
        if (string2.equals(string = this.chartSetup.getMainChart().getSymbol())) {
            return this.symbol;
        }
        return string2;
    }

    public void init(String string) {
        this.symbol = string;
        this.currentBarD = 0;
        this.currentBarW = 0;
        this.currentBarM = 0;
    }

    public boolean exists(int n) throws TradingException {
        return this.OpenD(0, n) > 0.0;
    }
}

