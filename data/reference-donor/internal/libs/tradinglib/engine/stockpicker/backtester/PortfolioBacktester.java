/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.time.SQTimeOld
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.backtester;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.BacktestData;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktestJob;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktestJobResult;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.log.StockpickerLog;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataModifier;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.signals.CollectedSignals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import com.strategyquant.tradinglib.explore.Explore;
import com.strategyquant.tradinglib.options.parameters.BrokerOption;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.robustnesstests.DataModifierCallback;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioBacktester {
    public static final Logger Log = LoggerFactory.getLogger(PortfolioBacktester.class);
    private ObjectArrayList<String> symbolsBacktested = new ObjectArrayList();
    private StopPauseEngine stopPauseEngine;
    private ILastEventListener lastEventListener;
    private StrategyBase strategy;
    private int lastIndex;
    private Element elStrategy;
    private IBacktestProgressListener backtestProgressListener;
    private BasketDto dto;
    private ChartSetup chartSetup;
    private LoadedPickerData loadedPickerData;
    private CollectedSignals signals = new CollectedSignals();
    private int totalTicks;
    private SettingsMap mainSettings;
    private int maxEntrySignalsLong;
    private int maxEntrySignalsShort;
    private Comparator<PickerEntrySignal> entrySignalComparatorByScore;
    double total;
    double processed;
    private int progress;
    private int lastProgress = 0;
    private boolean storeChartData = false;
    private StockpickerLog pickerLog;
    protected DataModifierCallback dataModifierCallback;

    public PortfolioBacktester(StockpickerLog stockpickerLog) {
        this.pickerLog = stockpickerLog;
    }

    public void backtest() throws Exception {
        long l = System.currentTimeMillis();
        this.beforeStart();
        Log.debug("Running on grid...");
        this.runBacktests();
        Log.debug("Finished running on grid...");
        long l2 = System.currentTimeMillis() - l;
        String string = SQTimeOld.formatDateTime((long)((int)(l2 / 1000L)));
        Log.debug("Collecting trading signals done in {}", (Object)string);
    }

    public void beforeStart() throws Exception {
        this.backtestProgressListener.setProgress(1);
        this.loadSettings(this.strategy.getSettings());
        this.loadData();
        this.backtestProgressListener.setProgress(25);
    }

    private void loadSettings(SettingsMap settingsMap) throws Exception {
        this.chartSetup = (ChartSetup)settingsMap.get("BacktestChart");
        ChartDef chartDef = this.chartSetup.getMainChart();
        String string = chartDef.getSymbol();
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string, (boolean)true);
        if (dataInfo == null) {
            throw new DataException(2, "Data for connection 'History' and symbol '" + string + "' cannot be found!");
        }
        int n = dataInfo.basketId;
        this.dto = BasketOfStocksManager.getInstance().getBasket(Integer.valueOf(n));
        if (this.dto == null) {
            throw new DataException(2, String.format("Group with id %d doesn't exist", n));
        }
        if (!DataManager.isGroupAlias((String)string)) {
            throw new DataException(2, String.format("Main chart symbol '%s' must be a group alias.", string));
        }
        for (int i = 1; i < this.chartSetup.getCharts().size(); ++i) {
            ChartDef chartDef2 = this.chartSetup.getCharts().get(i);
            if (chartDef2.getTimeframe().equals("D1") || chartDef2.getTimeframe().equals("Weekly") || chartDef2.getTimeframe().equals("Monthly")) continue;
            throw new Exception(L.t((String)"Invalid Additional chart %d - %s/%s definition. TF must be one of: %s, %s, %s.", (Object[])new Object[]{i, chartDef2.getSymbol(), chartDef2.getTimeframe(), "D1", "Weekly", "Monthly"}));
        }
    }

    public void loadData() throws Exception {
        PickerDataCache pickerDataCache = PickerDataCache.getInstance();
        pickerDataCache.registerProgressListener(this.backtestProgressListener);
        this.loadedPickerData = pickerDataCache.loadData(this.chartSetup, this.dto, this.stopPauseEngine, this.lastEventListener);
        if (this.loadedPickerData.stockGroupData.getSymbolsCount() == 0) {
            throw new Exception(L.t((String)"No data found.", (Object[])new Object[0]));
        }
        this.modifyData();
    }

    private void modifyData() throws TradingException {
        if (this.dataModifierCallback == null) {
            return;
        }
        this.loadedPickerData = this.loadedPickerData.clone();
        long l = this.chartSetup.getMainChart().getHistoryFrom();
        long l2 = this.chartSetup.getMainChart().getHistoryTo();
        PickerDataModifier pickerDataModifier = new PickerDataModifier();
        pickerDataModifier.modifyData(this.loadedPickerData, this.dataModifierCallback, l, l2);
    }

    public void setDataModifierCallback(DataModifierCallback dataModifierCallback) {
        this.dataModifierCallback = dataModifierCallback;
    }

    private void runBacktests() throws Exception {
        this.lastIndex = 0;
        ChartDef chartDef = this.chartSetup.getMainChart();
        long l = chartDef.getHistoryFrom();
        long l2 = chartDef.getHistoryTo();
        List<String> list = this.getBrokerSymbols();
        List list2 = BasketOfStocksManager.getInstance().getStocks(this.dto.getId().intValue(), list);
        this.total = list2.size();
        this.processed = 0.0;
        this.totalTicks = 0;
        BacktestData backtestData = new BacktestData(this.chartSetup, this.loadedPickerData, this.signals);
        String string = UUID.randomUUID().toString().replace("-", "");
        Log.debug("Running stockpicker backtest from {} to {} for {} symbols.", new Object[]{SQTime.toDateString((long)l), SQTime.toDateString((long)l2), this.total});
        if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
            this.pickerLog.print(String.format("\nRunning stockpicker backtest from %s to %s for %d symbols.", SQTime.toDateString((long)l), SQTime.toDateString((long)l2), Double.valueOf(this.total).longValue()));
        }
        int n = 0;
        while ((double)n < this.total) {
            block8: {
                if (this.stopPauseEngine.isStopped()) {
                    throw new TaskStoppedException();
                }
                try {
                    PortfolioBacktestJobResult portfolioBacktestJobResult = this.runOneBacktest(n, list2, l, l2, this.strategy, string, backtestData);
                    this.processed += 1.0;
                    this.progress = (int)(this.processed / this.total / 2.5 * 100.0) + 25;
                    if (this.backtestProgressListener != null && this.progress != this.lastProgress && (double)this.progress % 10.0 == 0.0) {
                        this.backtestProgressListener.setProgress(this.progress);
                        this.lastProgress = this.progress;
                    }
                    if (portfolioBacktestJobResult != null) {
                        this.totalTicks += portfolioBacktestJobResult.totalTicks;
                        if (!this.symbolsBacktested.contains((Object)portfolioBacktestJobResult.symbol)) {
                            this.symbolsBacktested.add((Object)portfolioBacktestJobResult.symbol);
                        }
                    }
                }
                catch (Exception exception) {
                    if (exception instanceof TaskStoppedException) break block8;
                    Log.error("PortfolioBacktester Error {}, Exception ", (Object)exception.getMessage(), (Object)exception);
                    throw exception;
                }
            }
            ++n;
        }
    }

    private List<String> getBrokerSymbols() throws DataException {
        Object object;
        String string = null;
        TradingOption[] tradingOptionArray = this.strategy.getTradingOptions();
        if (tradingOptionArray != null) {
            for (int i = 0; i < tradingOptionArray.length; ++i) {
                object = tradingOptionArray[i];
                if (!(object instanceof BrokerOption)) continue;
                string = ((BrokerOption)object).PickerBroker;
                break;
            }
        }
        if (string == null || string.equals("No filter")) {
            return null;
        }
        ArrayList<String> arrayList = new ArrayList();
        if (MainApp.isBacktestNode()) {
            String[] stringArray;
            object = this.mainSettings.getString("BrokerSymbols", null);
            if (object == null) {
                return null;
            }
            for (String string2 : stringArray = ((String)object).split("\n")) {
                if ((string2 = string2.trim()).trim().isEmpty()) continue;
                arrayList.add(string2);
            }
        } else {
            object = BrokerManager.getInstance().getBroker(string);
            if (object == null) {
                throw new DataException(2, String.format("Broker with name %s doesn't exist", string));
            }
            arrayList = BrokerManager.getInstance().getStocks(object.getId().intValue());
        }
        return arrayList;
    }

    private PortfolioBacktestJobResult runOneBacktest(int n, List<StockDto> list, long l, long l2, StrategyBase strategyBase, String string, BacktestData backtestData) throws Exception {
        PortfolioBacktestJob portfolioBacktestJob = this.createBacktestJob(n, list, l, l2, strategyBase, string, backtestData);
        if (portfolioBacktestJob != null) {
            return portfolioBacktestJob.call();
        }
        return null;
    }

    private PortfolioBacktestJob createBacktestJob(int n, List<StockDto> list, long l, long l2, StrategyBase strategyBase, String string, BacktestData backtestData) throws TradingException {
        StockDto stockDto = list.get(n);
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)stockDto.getTicker(), (boolean)true);
        if (dataInfo == null || dataInfo.rows < 1) {
            Log.debug("Data for symbol '" + stockDto.getTicker() + "' cannot be found!");
            return null;
        }
        String string2 = dataInfo.symbol;
        if (!this.loadedPickerData.symbolDataExists(string2)) {
            Log.debug("Data for symbol '" + string2 + "' not found.");
            return null;
        }
        if (Stockpicker.isDebugModeEnabled()) {
            Log.debug("Collecting trading signals for ticker {}", (Object)string2);
        }
        this.lastEventListener.setLastEvent(L.t((String)"Collecting trading signals for ticker '%s'.", (Object[])new Object[]{string2}));
        strategyBase.setSymbol(string2);
        strategyBase.setInstrumentInfo(dataInfo.symbolInfo);
        if (!this.storeChartData) {
            strategyBase.Stockpicker.TALibIndicators.clear();
        }
        PortfolioBacktestJob portfolioBacktestJob = new PortfolioBacktestJob(string2, this.stopPauseEngine, this.lastEventListener, strategyBase, backtestData, this.elStrategy, string, l, l2, stockDto, this.maxEntrySignalsLong, this.maxEntrySignalsShort, this.entrySignalComparatorByScore, this.pickerLog);
        return portfolioBacktestJob;
    }

    public ObjectArrayList<String> getSymbolsBacktested() {
        return this.symbolsBacktested;
    }

    public void setStopPauseEngine(StopPauseEngine stopPauseEngine) {
        this.stopPauseEngine = stopPauseEngine;
    }

    public void setLastEventListener(ILastEventListener iLastEventListener) {
        this.lastEventListener = iLastEventListener;
    }

    public void addSetup(SettingsMap settingsMap) throws Exception {
        this.mainSettings = settingsMap;
    }

    public void setStrategy(StrategyBase strategyBase) {
        this.strategy = strategyBase;
    }

    public void setStrategyXml(Element element) {
        this.elStrategy = element;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }

    public LoadedPickerData getPickerData() {
        return this.loadedPickerData;
    }

    public LoadedStockGroupData getStockGroupData() {
        return this.loadedPickerData.stockGroupData;
    }

    public int getTotalSymbolsLoaded() {
        return this.loadedPickerData.stockGroupData.getSymbolsCount();
    }

    public CollectedSignals getSignals() {
        return this.signals;
    }

    public Explore getExplore() {
        return this.strategy.Explore;
    }

    public int getTotalTicks() {
        return this.totalTicks * 4;
    }

    public void setReducer(int n, int n2, Comparator<PickerEntrySignal> comparator) {
        this.maxEntrySignalsLong = n;
        this.maxEntrySignalsShort = n2;
        this.entrySignalComparatorByScore = comparator;
    }

    public void storeChartData(boolean bl) {
        this.storeChartData = bl;
    }

    public void clear() {
        if (this.signals != null) {
            this.signals.clear();
        }
        if (this.dataModifierCallback != null) {
            this.loadedPickerData.clear();
            this.loadedPickerData = null;
        }
    }
}

