/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.io.VersatileData
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.robustnesstests.DataModifierCallback;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataModifier {
    public static final Logger Log = LoggerFactory.getLogger(PickerDataModifier.class);

    public void modifyData(LoadedPickerData loadedPickerData, DataModifierCallback dataModifierCallback, long l, long l2) throws TradingException {
        if (dataModifierCallback == null) {
            return;
        }
        try {
            String[] stringArray = loadedPickerData.stockGroupData.getSymbols().toArray(new String[loadedPickerData.stockGroupData.getSymbols().size()]);
            for (int i = 0; i < stringArray.length; ++i) {
                String string = stringArray[i];
                LoadedSymbolData loadedSymbolData = loadedPickerData.stockGroupData.getSymbolData(string);
                if (loadedSymbolData == null) continue;
                this.modifySymbolData(loadedPickerData, string, loadedSymbolData, dataModifierCallback, l, l2);
            }
        }
        catch (Exception exception) {
            Log.error("Error modifying data", (Throwable)exception);
            throw new TradingException("Error modifying data", exception);
        }
    }

    private void modifySymbolData(LoadedPickerData loadedPickerData, String string, LoadedSymbolData loadedSymbolData, DataModifierCallback dataModifierCallback, long l, long l2) throws TradingException {
        VersatileData versatileData = new VersatileData();
        TickEvent tickEvent = new TickEvent();
        long l3 = loadedPickerData.timeline.indexToTimeD(loadedSymbolData.getRealDataIndexStartD());
        long l4 = loadedPickerData.timeline.indexToTimeD(loadedSymbolData.getRealDataIndexEndD());
        if (l3 > l) {
            l = l3;
        }
        if (l4 < l2) {
            l2 = l4;
        }
        int n = loadedPickerData.timeline.searchIndexByTimeD(l, true);
        int n2 = loadedPickerData.timeline.searchIndexByTimeD(l2, false);
        double d = 0.0;
        for (int i = n; i <= n2; ++i) {
            long l5 = loadedPickerData.timeline.indexToTimeD(i);
            d = this.computeATROnBar(loadedSymbolData.OpenD, loadedSymbolData.HighD, loadedSymbolData.LowD, loadedSymbolData.CloseD, i);
            this.modifyOHLCData(loadedSymbolData.OpenD, loadedSymbolData.HighD, loadedSymbolData.LowD, loadedSymbolData.CloseD, loadedSymbolData.VolumeD, versatileData, i, l5, dataModifierCallback);
            this.modifyTickData(loadedSymbolData.OpenD, tickEvent, i, l5, dataModifierCallback, d);
            this.modifyTickData(loadedSymbolData.HighD, tickEvent, i, l5, dataModifierCallback, d);
            this.modifyTickData(loadedSymbolData.LowD, tickEvent, i, l5, dataModifierCallback, d);
            this.modifyTickData(loadedSymbolData.CloseD, tickEvent, i, l5, dataModifierCallback, d);
            this.modifyTickData(loadedSymbolData.VolumeD, tickEvent, i, l5, dataModifierCallback, d);
        }
    }

    private void modifyOHLCData(float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4, float[] fArray5, VersatileData versatileData, int n, long l, DataModifierCallback dataModifierCallback) throws TradingException {
        versatileData.time = l;
        versatileData.open = fArray[n];
        versatileData.high = fArray2[n];
        versatileData.low = fArray3[n];
        versatileData.close = fArray4[n];
        versatileData.volume = fArray5[n];
        dataModifierCallback.modifyOHLCData(versatileData);
        fArray[n] = (float)versatileData.open;
        fArray2[n] = (float)versatileData.high;
        fArray3[n] = (float)versatileData.low;
        fArray4[n] = (float)versatileData.close;
        fArray5[n] = (float)versatileData.volume;
    }

    private void modifyTickData(float[] fArray, TickEvent tickEvent, int n, long l, DataModifierCallback dataModifierCallback, double d) throws TradingException {
        tickEvent.setTime(l);
        tickEvent.setAsk((double)fArray[n]);
        tickEvent.setBid((double)fArray[n]);
        dataModifierCallback.modifyData(tickEvent, d);
        fArray[n] = (float)tickEvent.getAsk();
    }

    private double computeATROnBar(float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4, int n) throws TradingException {
        int n2 = 14;
        if (n - n2 + 1 < 0) {
            return 0.0;
        }
        double d = 0.0;
        for (int i = n - n2 + 1; i <= n; ++i) {
            double d2 = fArray2[i] - fArray3[i];
            double d3 = i - 1 >= 0 ? (double)Math.abs(fArray2[i] - fArray4[i - 1]) : 0.0;
            double d4 = i - 1 >= 0 ? (double)Math.abs(fArray3[i] - fArray4[i - 1]) : 0.0;
            double d5 = Math.max(d2, Math.max(d3, d4));
            d += d5;
        }
        return d / (double)n2;
    }
}

