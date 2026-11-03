/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TaskStoppedException
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.symbols;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.StopPauseEngine;

public class SymbolDataLoader {
    public LoadedSymbolData load(DataInfo dataInfo, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        LoadedSymbolData loadedSymbolData = new LoadedSymbolData(pickerDataTimeline.SizeD(), pickerDataTimeline.SizeW(), pickerDataTimeline.SizeM());
        this._load(dataInfo, pickerDataTimeline, stopPauseEngine, loadedSymbolData, "D1");
        this._load(dataInfo, pickerDataTimeline, stopPauseEngine, loadedSymbolData, "Weekly");
        this._load(dataInfo, pickerDataTimeline, stopPauseEngine, loadedSymbolData, "Monthly");
        return loadedSymbolData;
    }

    private void _load(DataInfo dataInfo, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine, LoadedSymbolData loadedSymbolData, String string) throws Exception {
        try (IDataLoader iDataLoader = null;){
            iDataLoader = DataManager.getDataLoader((ChartDef)new ChartDef("History", dataInfo.symbol, string, pickerDataTimeline.dateFrom(), pickerDataTimeline.dateTo(), dataInfo.symbolInfo.defaultSpread, "No Session"), (int)1);
            iDataLoader.open();
            VersatileData versatileData = new VersatileData();
            block15: while (iDataLoader.hasNextTick()) {
                iDataLoader.getNextTick(versatileData);
                if (stopPauseEngine.isStopped()) {
                    throw new TaskStoppedException();
                }
                long l = SQTime.getDateInMs((long)versatileData.time);
                switch (string) {
                    case "D1": {
                        if (!pickerDataTimeline.containsTimeD(l)) continue block15;
                        int n = pickerDataTimeline.timeToIndexD(l);
                        if (loadedSymbolData.getRealDataIndexStartD() < 0) {
                            loadedSymbolData.setRealDataIndexStartD(n);
                        }
                        loadedSymbolData.setRealDataIndexEndD(n);
                        loadedSymbolData.OpenD[n] = (float)versatileData.open;
                        loadedSymbolData.HighD[n] = (float)versatileData.high;
                        loadedSymbolData.LowD[n] = (float)versatileData.low;
                        loadedSymbolData.CloseD[n] = (float)versatileData.close;
                        loadedSymbolData.VolumeD[n] = (float)versatileData.volume;
                        continue block15;
                    }
                    case "Weekly": {
                        if (!pickerDataTimeline.containsTimeW(l)) continue block15;
                        int n = pickerDataTimeline.timeToIndexW(l);
                        if (loadedSymbolData.getRealDataIndexStartW() < 0) {
                            loadedSymbolData.setRealDataIndexStartW(n);
                        }
                        loadedSymbolData.setRealDataIndexEndW(n);
                        loadedSymbolData.OpenW[n] = (float)versatileData.open;
                        loadedSymbolData.HighW[n] = (float)versatileData.high;
                        loadedSymbolData.LowW[n] = (float)versatileData.low;
                        loadedSymbolData.CloseW[n] = (float)versatileData.close;
                        loadedSymbolData.VolumeW[n] = (float)versatileData.volume;
                        continue block15;
                    }
                    case "Monthly": {
                        if (!pickerDataTimeline.containsTimeM(l)) continue block15;
                        int n = pickerDataTimeline.timeToIndexM(l);
                        if (loadedSymbolData.getRealDataIndexStartM() < 0) {
                            loadedSymbolData.setRealDataIndexStartM(n);
                        }
                        loadedSymbolData.setRealDataIndexEndM(n);
                        loadedSymbolData.OpenM[n] = (float)versatileData.open;
                        loadedSymbolData.HighM[n] = (float)versatileData.high;
                        loadedSymbolData.LowM[n] = (float)versatileData.low;
                        loadedSymbolData.CloseM[n] = (float)versatileData.close;
                        loadedSymbolData.VolumeM[n] = (float)versatileData.volume;
                        continue block15;
                    }
                }
                throw new Exception(L.t((String)"Invalid timeframe %s.", (Object[])new Object[]{string}));
            }
            this.fillGaps(string, loadedSymbolData);
            iDataLoader.close();
        }
    }

    private void fillGaps(String string, LoadedSymbolData loadedSymbolData) {
        float f = -1.0f;
        float f2 = -1.0f;
        float f3 = -1.0f;
        float f4 = -1.0f;
        float f5 = -1.0f;
        switch (string) {
            case "D1": {
                for (int i = loadedSymbolData.getRealDataIndexStartD(); i <= loadedSymbolData.getRealDataIndexEndD(); ++i) {
                    if (loadedSymbolData.OpenD[i] == 0.0f) {
                        if (f < 0.0f) continue;
                        loadedSymbolData.OpenD[i] = f;
                        loadedSymbolData.HighD[i] = f2;
                        loadedSymbolData.LowD[i] = f3;
                        loadedSymbolData.CloseD[i] = f4;
                        loadedSymbolData.VolumeD[i] = f5;
                        continue;
                    }
                    f = loadedSymbolData.OpenD[i];
                    f2 = loadedSymbolData.HighD[i];
                    f3 = loadedSymbolData.LowD[i];
                    f4 = loadedSymbolData.CloseD[i];
                    f5 = loadedSymbolData.VolumeD[i];
                }
                break;
            }
            case "Weekly": {
                for (int i = loadedSymbolData.getRealDataIndexStartW(); i <= loadedSymbolData.getRealDataIndexEndW(); ++i) {
                    if (loadedSymbolData.OpenW[i] == 0.0f) {
                        if (f < 0.0f) continue;
                        loadedSymbolData.OpenW[i] = f;
                        loadedSymbolData.HighW[i] = f2;
                        loadedSymbolData.LowW[i] = f3;
                        loadedSymbolData.CloseW[i] = f4;
                        loadedSymbolData.VolumeW[i] = f5;
                        continue;
                    }
                    f = loadedSymbolData.OpenW[i];
                    f2 = loadedSymbolData.HighW[i];
                    f3 = loadedSymbolData.LowW[i];
                    f4 = loadedSymbolData.CloseW[i];
                    f5 = loadedSymbolData.VolumeW[i];
                }
                break;
            }
            case "Monthly": {
                for (int i = loadedSymbolData.getRealDataIndexStartM(); i <= loadedSymbolData.getRealDataIndexEndM(); ++i) {
                    if (loadedSymbolData.OpenM[i] == 0.0f) {
                        if (f < 0.0f) continue;
                        loadedSymbolData.OpenM[i] = f;
                        loadedSymbolData.HighM[i] = f2;
                        loadedSymbolData.LowM[i] = f3;
                        loadedSymbolData.CloseM[i] = f4;
                        loadedSymbolData.VolumeM[i] = f5;
                        continue;
                    }
                    f = loadedSymbolData.OpenM[i];
                    f2 = loadedSymbolData.HighM[i];
                    f3 = loadedSymbolData.LowM[i];
                    f4 = loadedSymbolData.CloseM[i];
                    f5 = loadedSymbolData.VolumeM[i];
                }
                break;
            }
        }
    }
}

