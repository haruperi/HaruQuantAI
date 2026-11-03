/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import java.util.Set;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedStockGroupData {
    public static final Logger Log = LoggerFactory.getLogger(LoadedStockGroupData.class);
    private Object2ObjectOpenHashMap<String, LoadedSymbolData> symbolsData = new Object2ObjectOpenHashMap();
    private StampedLock lock = new StampedLock();
    private long stamp = 0L;
    private BasketDto dto = null;
    private Exception loadException = null;

    public LoadedStockGroupData() {
    }

    public LoadedStockGroupData(BasketDto basketDto) {
        this.dto = basketDto;
    }

    public void clear() {
        this.symbolsData.clear();
    }

    public Exception getException() {
        return this.loadException;
    }

    public void setException(Exception exception) {
        this.loadException = exception;
    }

    public int getSymbolsCount() {
        return this.symbolsData.size();
    }

    public Set<String> getSymbols() {
        return this.symbolsData.keySet();
    }

    public void putSymbolData(String string, LoadedSymbolData loadedSymbolData) {
        this.stamp = this.lock.writeLock();
        try {
            this.symbolsData.put((Object)string, (Object)loadedSymbolData);
        }
        finally {
            this.lock.unlock(this.stamp);
        }
    }

    public LoadedSymbolData getSymbolData(String string) {
        return (LoadedSymbolData)this.symbolsData.get((Object)string);
    }

    public LoadedStockGroupData clone() {
        LoadedStockGroupData loadedStockGroupData = new LoadedStockGroupData();
        loadedStockGroupData.symbolsData = new Object2ObjectOpenHashMap();
        this.symbolsData.forEach((string, loadedSymbolData) -> loadedStockGroupData.symbolsData.put(string, (Object)(loadedSymbolData != null ? loadedSymbolData.clone() : null)));
        loadedStockGroupData.loadException = this.loadException;
        return loadedStockGroupData;
    }
}

