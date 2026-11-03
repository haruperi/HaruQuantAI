/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtest.BacktestInitStrategy;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataCache;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import java.util.ArrayList;

public class BacktestDataInitializer {
    private ArrayList<ChartSetup> chartSetups;
    private LoadDataProgressEngine progressEngine;
    private ArrayList<ICrossCheck> crossChecks;
    private ILastEventListener lastEventListener;

    public BacktestDataInitializer(LoadDataProgressEngine loadDataProgressEngine, ArrayList<ChartSetup> arrayList, boolean bl, ArrayList<ICrossCheck> arrayList2, ILastEventListener iLastEventListener) {
        this.chartSetups = arrayList;
        this.progressEngine = loadDataProgressEngine;
        if (bl) {
            this.crossChecks = arrayList2;
        }
        this.lastEventListener = iLastEventListener;
    }

    public BacktestDataInitializer(LoadDataProgressEngine loadDataProgressEngine, ArrayList<ChartSetup> arrayList, boolean bl, ArrayList<ICrossCheck> arrayList2) {
        this(loadDataProgressEngine, arrayList, bl, arrayList2, null);
    }

    public long prepareData() throws Exception {
        ChartSetup chartSetup;
        int n;
        long l = System.currentTimeMillis();
        if (this.chartSetups == null || this.chartSetups.size() < 1) {
            return 0L;
        }
        this.progressEngine.printToLog(L.t((String)"Initializing backtest data...", (Object[])new Object[]{true}));
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(L.t((String)"Initializing backtest data...", (Object[])new Object[]{true}));
        }
        if ((n = (chartSetup = this.chartSetups.get(0)).getBacktestEngine()) == 1316847364 || n == -1816889229) {
            this.preparePickerData(chartSetup, this.crossChecks);
        } else {
            this.prepareDataFor("Main test", chartSetup);
            if (this.crossChecks != null && this.crossChecks.size() > 0) {
                for (int i = 0; i < this.crossChecks.size(); ++i) {
                    ChartSetups chartSetups;
                    ICrossCheck iCrossCheck = this.crossChecks.get(i);
                    if (!iCrossCheck.doesRetest() || (chartSetups = iCrossCheck.getChartSetups(chartSetup)) == null) continue;
                    ChartSetups chartSetups2 = chartSetups.getClone();
                    for (int j = 0; j < chartSetups2.size(); ++j) {
                        ChartSetup chartSetup2 = (ChartSetup)chartSetups2.get(j);
                        this.prepareDataFor(iCrossCheck.getName(), chartSetup2);
                    }
                }
            }
        }
        this.progressEngine.printToLog(L.t((String)"All backtest data prepared", (Object[])new Object[]{true}));
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(L.t((String)"All backtest data prepared", (Object[])new Object[]{true}));
        }
        this.progressEngine.printToLog("-----------------------------");
        return System.currentTimeMillis() - l;
    }

    public void preparePickerData(ChartSetup chartSetup, ArrayList<ICrossCheck> arrayList) throws Exception {
        Object object;
        Object object2;
        DataManager.get().refreshDataInfoCache();
        int n = chartSetup.getBacktestEngine();
        String string = chartSetup.getSymbol();
        if (n == -1816889229 && DataManager.isGroupAlias((String)string)) {
            BasketDto basketDto = BasketOfStocksManager.getInstance().getBasket(string);
            if (basketDto == null) {
                throw new Exception(L.t((String)"Group with name '{0}' not found.", (Object[])new Object[]{string}));
            }
            object2 = BasketOfStocksManager.getInstance().getStocks(basketDto.getId().intValue());
            for (int i = 0; i < object2.size(); ++i) {
                object = (StockDto)object2.get(i);
                chartSetup = chartSetup.getClone(object.getTicker());
                chartSetup = StockpickerBacktestEngine.createTempStockGroup(chartSetup);
                this.prepareStockpickerData(chartSetup);
            }
        } else {
            if (n == -1816889229) {
                chartSetup = StockpickerBacktestEngine.createTempStockGroup(chartSetup);
            }
            this.prepareStockpickerData(chartSetup);
        }
        if (n == 1316847364 && arrayList != null && arrayList.size() > 0) {
            for (int i = 0; i < arrayList.size(); ++i) {
                object2 = arrayList.get(i);
                if (!object2.getSettingName().equals("RetestOnAdditionalMarkets")) continue;
                ChartSetups chartSetups = object2.getChartSetups(chartSetup);
                if (chartSetups == null) break;
                object = chartSetups.getClone();
                for (int j = 0; j < ((ArrayList)object).size(); ++j) {
                    ChartSetup chartSetup2 = (ChartSetup)((ArrayList)object).get(j);
                    this.prepareStockpickerData(chartSetup2);
                }
                break;
            }
        }
    }

    public void prepareStockpickerData(ChartSetup chartSetup) throws Exception {
        ChartDef chartDef = chartSetup.getMainChart();
        String string = chartDef.getSymbol();
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string, (boolean)true);
        if (dataInfo == null) {
            throw new DataException(2, "Data for connection 'History' and symbol '" + string + "' cannot be found!");
        }
        int n = dataInfo.basketId;
        BasketDto basketDto = BasketOfStocksManager.getInstance().getBasket(Integer.valueOf(n));
        if (basketDto == null) {
            throw new DataException(2, L.t((String)"Group with id %d doesn't exist", (Object[])new Object[]{n}));
        }
        if (!DataManager.isGroupAlias((String)string)) {
            throw new DataException(2, L.t((String)"Main chart symbol '%s' must be a group alias.", (Object[])new Object[]{string}));
        }
        for (int i = 1; i < chartSetup.getCharts().size(); ++i) {
            ChartDef chartDef2 = chartSetup.getCharts().get(i);
            if (chartDef2.getTimeframe().equals("D1") || chartDef2.getTimeframe().equals("Weekly") || chartDef2.getTimeframe().equals("Monthly")) continue;
            throw new Exception(L.t((String)"Invalid Additional chart %d - %s/%s definition. TF must be one of: %s, %s, %s.", (Object[])new Object[]{i, chartDef2.getSymbol(), chartDef2.getTimeframe(), "D1", "Weekly", "Monthly"}));
        }
        PickerDataCache pickerDataCache = PickerDataCache.getInstance();
        pickerDataCache.loadData(chartSetup, basketDto, this.progressEngine.getProgressEngine(), this.lastEventListener);
    }

    private void prepareDataFor(String string, ChartSetup chartSetup) throws Exception {
        BacktestInitStrategy backtestInitStrategy = new BacktestInitStrategy();
        BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator(chartSetup));
        backtestEngine.setSingleThreaded(true);
        backtestEngine.setStopPauseEngine(this.progressEngine.getProgressEngine());
        SettingsMap settingsMap = new SettingsMap();
        settingsMap.set("BacktestChart", (Object)chartSetup);
        settingsMap.set("MoneyManagement.InitialCapital", (Object)100000.0);
        settingsMap.set("StrategyObject", (Object)backtestInitStrategy);
        settingsMap.set("MinDistance", (Object)0);
        backtestEngine.addSetup(settingsMap);
        backtestEngine.setLoadDataProgressEngine(this.progressEngine);
        this.progressEngine.setParams(string, chartSetup.getCharts().get(0).getSymbol(), chartSetup.getCharts().get(0).getTimeframe());
        backtestEngine.runBacktest("LoadDataStartegy", "LoadDataStrategy", false);
    }
}

