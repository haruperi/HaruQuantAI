/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.jfx.ErrHistoryWillUpdated
 *  com.jfx.ErrUnknownSymbol
 *  com.jfx.Timeframe
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.tradinglib.connection.HistoryData
 *  com.strategyquant.tradinglib.connection.IDataFeed
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.MT4;

import com.jfx.ErrHistoryWillUpdated;
import com.jfx.ErrUnknownSymbol;
import com.jfx.Timeframe;
import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge;
import com.strategyquant.plugin.Connection.impl.MT4.MT4Connection;
import com.strategyquant.tradinglib.connection.HistoryData;
import com.strategyquant.tradinglib.connection.IDataFeed;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4DataFeed
implements IDataFeed {
    public static final Logger Log = LoggerFactory.getLogger((String)"MT4DataFeed");
    private ArrayList<String> availableSymbols;
    private MT4Connection mt4Connection;
    private MT4Bridge mt4Bridge;

    public MT4DataFeed(MT4Connection mt4Connection, MT4Bridge mt4Bridge) {
        this.mt4Connection = mt4Connection;
        this.mt4Bridge = mt4Bridge;
    }

    public void registerSymbol(String symbol) throws Exception {
        if (!this.checkSymbolIsSupported(symbol)) {
            throw new Exception("Symbol " + symbol + " is not supported.");
        }
        this.mt4Bridge.registerSymbol(symbol);
    }

    public boolean checkSymbolIsSupported(String symbol) {
        this.loadAvailableSymbols();
        if (this.availableSymbols == null) {
            Log.error("Cannot load available symbols.");
            return false;
        }
        for (int i = 0; i < this.availableSymbols.size(); ++i) {
            if (!this.availableSymbols.get(i).equals(symbol)) continue;
            return true;
        }
        return false;
    }

    public HistoryData getHistoryData(ChartDef chart, int type, long fromTime, long toTime) {
        HistoryData hd = new HistoryData(chart, type, fromTime, toTime);
        ArrayList<VersatileData> allData = new ArrayList<VersatileData>();
        int i = -1;
        try {
            while (true) {
                long time;
                if ((time = this.mt4Bridge.iTime(chart.getSymbol(), Timeframe.PERIOD_M1, ++i).getTime()) > toTime) {
                    continue;
                }
                if (time >= fromTime) {
                    VersatileData data = new VersatileData();
                    data.time = time;
                    data.open = this.mt4Bridge.iOpen(chart.getSymbol(), Timeframe.PERIOD_M1, i);
                    data.high = this.mt4Bridge.iHigh(chart.getSymbol(), Timeframe.PERIOD_M1, i);
                    data.low = this.mt4Bridge.iLow(chart.getSymbol(), Timeframe.PERIOD_M1, i);
                    data.close = this.mt4Bridge.iClose(chart.getSymbol(), Timeframe.PERIOD_M1, i);
                    data.volume = this.mt4Bridge.iVolume(chart.getSymbol(), Timeframe.PERIOD_M1, i);
                    allData.add(data);
                    continue;
                }
                break;
            }
        }
        catch (ErrHistoryWillUpdated e) {
            allData.remove(allData.size() - 1);
            Log.error("Cannot get historical bar with shift: " + i, (Throwable)e);
        }
        catch (ErrUnknownSymbol e) {
            allData.remove(allData.size() - 1);
            Log.error("Cannot get historical bar. Unknown symbol: " + chart.getSymbol(), (Throwable)e);
        }
        for (int a = allData.size() - 1; a >= 0; --a) {
            hd.addMinuteData(((VersatileData)allData.get((int)a)).time, ((VersatileData)allData.get((int)a)).open, ((VersatileData)allData.get((int)a)).high, ((VersatileData)allData.get((int)a)).low, ((VersatileData)allData.get((int)a)).close, ((VersatileData)allData.get((int)a)).volume);
        }
        return hd;
    }

    private void loadAvailableSymbols() {
        if (this.mt4Bridge.isConnected() && this.availableSymbols == null) {
            this.availableSymbols = this.mt4Bridge.getSymbols();
        }
    }
}

