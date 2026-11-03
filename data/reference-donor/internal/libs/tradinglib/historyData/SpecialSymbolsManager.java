/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.historyData.DownloadHistorySymbolJob;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.util.LinkedList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SpecialSymbolsManager {
    public static final Logger Log = LoggerFactory.getLogger(SpecialSymbolsManager.class);
    private static final String DEFAULT_CONNECTION = "History";
    private static final String SPY_SYMBOL = "SPY_benchmark.D";

    public static void updateAll() throws Exception {
        try {
            Object object;
            String string;
            boolean bl;
            boolean bl2 = bl = MainApp.runInConsole() && !MainApp.CLIWebServeActive;
            if (bl) {
                return;
            }
            DataInfo dataInfo = DataManager.getDataInfo((String)DEFAULT_CONNECTION, (String)SPY_SYMBOL);
            if (dataInfo == null) {
                string = "SPY_benchmark";
                if (!InstrumentManager.checkInstrumentExists((String)string, (boolean)true)) {
                    InstrumentManager.addInstrument((String)string, (String)"History data instrument", (double)1.0, (double)0.01, (double)0.01, (double)0.0, (double)0.0, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)5);
                }
                object = new LinkedList();
                dataInfo = new DataInfo();
                dataInfo.timeframe = "D1";
                dataInfo.barTimeType = 1;
                dataInfo.timezone = "Exchange";
                dataInfo.connection = DEFAULT_CONNECTION;
                dataInfo.symbol = SPY_SYMBOL;
                dataInfo.source = 5;
                dataInfo.instrument = string;
                dataInfo.uSymbol = SPY_SYMBOL;
                dataInfo.uSymbolName = SPY_SYMBOL;
                dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo((String)string);
                object.add(dataInfo);
                DataManager.addDataInBatch((String)DEFAULT_CONNECTION, (List)object, null);
            }
            string = HistoryDataManager.get().getStockTicker("SPY.D");
            string.setTicker(SPY_SYMBOL);
            object = "internal_download_SPY_benchmark.D";
            DownloadHistorySymbolJob downloadHistorySymbolJob = new DownloadHistorySymbolJob((String)object, dataInfo, TickerKind.STOCK, (TickerDto)string);
            downloadHistorySymbolJob.setForceFlush(true);
            downloadHistorySymbolJob.setProgressListener((DataManagerProgressListener)DataManagerDataProgress.get().createListener(dataInfo.symbol, "sqEquityData/updateDataAction"));
            SQGrid.getGridClient().executeOnGrid((String)object, (GridJob)downloadHistorySymbolJob);
        }
        catch (Exception exception) {
            Log.error("Error while initialization of SPY_benchmark.D", (Throwable)exception);
        }
    }

    public static boolean isSpecial(String string) {
        return SPY_SYMBOL.equals(string);
    }

    public static boolean isSpecial(DataInfo dataInfo) {
        return SpecialSymbolsManager.isSpecial(dataInfo.symbol);
    }
}

