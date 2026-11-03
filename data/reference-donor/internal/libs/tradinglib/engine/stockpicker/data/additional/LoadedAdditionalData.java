/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.additional;

import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;

public class LoadedAdditionalData
extends ObjectArrayList<LoadedSymbolData> {
    private Exception loadException = null;

    public void setException(Exception exception) {
        this.loadException = exception;
    }

    public Exception getException() {
        return this.loadException;
    }

    public LoadedAdditionalData clone() {
        LoadedAdditionalData loadedAdditionalData = new LoadedAdditionalData();
        ObjectListIterator objectListIterator = this.iterator();
        while (objectListIterator.hasNext()) {
            LoadedSymbolData loadedSymbolData = (LoadedSymbolData)objectListIterator.next();
            loadedAdditionalData.add(loadedSymbolData != null ? loadedSymbolData.clone() : null);
        }
        loadedAdditionalData.loadException = this.loadException;
        return loadedAdditionalData;
    }
}

