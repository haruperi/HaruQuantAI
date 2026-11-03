/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.LoadedAdditionalData;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedPickerData {
    public static final Logger Log = LoggerFactory.getLogger(LoadedPickerData.class);
    public PickerDataTimeline timeline;
    public LoadedStockGroupData stockGroupData;
    public LoadedAdditionalData additionalData;
    private Exception loadException = null;

    public Exception getException() {
        return this.loadException;
    }

    public void setException(Exception exception) {
        this.loadException = exception;
    }

    public long getSymbolDataFrom(String string) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.stockGroupData.getSymbolData(string);
        int n = loadedSymbolData.getRealDataIndexStartD();
        return this.timeline.indexToTimeD(n);
    }

    public long getSymbolDataTo(String string) throws TradingException {
        LoadedSymbolData loadedSymbolData = this.stockGroupData.getSymbolData(string);
        int n = loadedSymbolData.getRealDataIndexEndD();
        return this.timeline.indexToTimeD(n);
    }

    public boolean symbolDataExists(String string) throws TradingException {
        return this.stockGroupData.getSymbolData(string) != null;
    }

    public LoadedPickerData clone() {
        LoadedPickerData loadedPickerData = new LoadedPickerData();
        loadedPickerData.timeline = this.timeline.clone();
        loadedPickerData.stockGroupData = this.stockGroupData.clone();
        loadedPickerData.additionalData = this.additionalData.clone();
        loadedPickerData.loadException = this.loadException;
        return loadedPickerData;
    }

    public void clear() {
        this.timeline.clear();
        this.stockGroupData.clear();
        this.additionalData.clear();
    }
}

