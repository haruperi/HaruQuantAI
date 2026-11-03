/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.IDataBuffer
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.backtest.BacktestTradingSetupRunnable;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.ReservedBars;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.simulator.Engines;
import java.util.ArrayList;
import java.util.List;

public class BacktestTradingSetup
extends TradingSetup {
    private BacktestTradingSetupRunnable backtestRunnable;

    public BacktestTradingSetup(BacktestEngine backtestEngine, ChartSetup chartSetup, SettingsMap settingsMap, StrategyBase strategyBase) {
        super(null, backtestEngine.getEngineId(), chartSetup, settingsMap, strategyBase);
        this.recognizeUserDefinedStartingBar(settingsMap);
        this.setTradingType(1);
    }

    private void recognizeUserDefinedStartingBar(SettingsMap settingsMap) {
        this.indyStartingBar = 0;
        if (Engines.isTradestationEngine(this.getEngineId()) && settingsMap != null) {
            int n;
            this.indyStartingBar = settingsMap.getInt("StartingBar", 0);
            if (this.indyStartingBar < 0) {
                this.indyStartingBar = 0;
            }
            if ((n = settingsMap.getInt("ReservedBars", 0)) == 0) {
                n = this.tryRecognizeReservedBarsFromTradingOptions(settingsMap);
            }
            this.indyStartingBar += n;
        }
    }

    private int tryRecognizeReservedBarsFromTradingOptions(SettingsMap settingsMap) {
        ArrayList arrayList = (ArrayList)settingsMap.get("TradingOptions");
        if (arrayList != null) {
            for (int i = 0; i < arrayList.size(); ++i) {
                TradingOption tradingOption = (TradingOption)arrayList.get(i);
                if (!(tradingOption instanceof ReservedBars)) continue;
                ReservedBars reservedBars = (ReservedBars)tradingOption;
                return reservedBars.ReservedBars;
            }
        }
        return 0;
    }

    public void initRunnable(IDataBuffer iDataBuffer) {
        this.backtestRunnable = new BacktestTradingSetupRunnable(this, iDataBuffer, this.usePreparedData);
    }

    public void processEvent(TickEvent tickEvent, boolean bl) throws Exception {
        this.backtestRunnable.runCalled(tickEvent, bl);
    }

    void setTradingEngine(TradingEngine tradingEngine) {
        this.tradingEngine = tradingEngine;
    }

    @Override
    public void setBarEventType(int n) {
        super.setBarEventType(n);
        this.backtestRunnable.setBarEventType(n);
    }

    public BarUpdateInfo getBarUpdateInfo() {
        return this.backtestRunnable.getBarUpdateInfo();
    }

    public void initTradingOptions() throws Exception {
        if (this.settings.containsKey("TradingOptions") && this.settings.get("TradingOptions") instanceof TradingOptions) {
            TradingOptions tradingOptions = (TradingOptions)this.settings.get("TradingOptions");
            BacktestTradingSetup.setTradingOptionsSettings(this.settings, tradingOptions);
        }
        this.initInternalSettings();
    }

    public static void setTradingOptionsSettings(SettingsMap settingsMap, TradingOptions tradingOptions) throws Exception {
        if (tradingOptions == null || settingsMap == null) {
            return;
        }
        for (TradingOption tradingOption : tradingOptions) {
            String string = tradingOption.getClass().getSimpleName();
            List<String> list = tradingOption.getParametersList();
            for (String string2 : list) {
                String string3 = list.size() > 1 || !string.equals(string2) ? String.format("%s.%s", string, string2) : string2;
                settingsMap.set(string3, tradingOption.getParameterValue(string2));
            }
        }
    }

    public String getChartsHash() {
        StringBuilder stringBuilder = new StringBuilder(0);
        return stringBuilder.toString();
    }
}

