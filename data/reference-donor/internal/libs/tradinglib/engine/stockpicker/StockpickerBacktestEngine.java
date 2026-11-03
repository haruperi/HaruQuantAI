/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.AbstractBacktestEngine;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.stockpicker.PortfolioTrader;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktester;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.log.StockpickerLog;
import com.strategyquant.tradinglib.engine.stockpicker.constants.PickerTriggerTypes;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.signals.CollectedSignals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.Signals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignalComparatorByRevScore;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.parameters.LimitOver;
import com.strategyquant.tradinglib.options.parameters.StockpickerOptions;
import com.strategyquant.tradinglib.options.parameters.StoreChartData;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByTicket;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockpickerBacktestEngine
extends AbstractBacktestEngine {
    public static final Logger Log = LoggerFactory.getLogger(StockpickerBacktestEngine.class);
    public static final String StockpickerPath = SQPaths.userDirPath + "/stockpicker/";
    private Trader tradeController;
    private PortfolioBacktester backtester;
    private PortfolioTrader trader;
    private IBacktestProgressListener backtestProgressListener;
    private StopPauseEngine stopPauseEngine;
    private ILastEventListener lastEventListener;
    private StockpickerLog pickerLog = new StockpickerLog();
    private SettingsMap mainSettings;
    private double initialCapital;
    private int MaxOpenPositionsLong;
    private int MaxOpenPositionsShort;
    private long dayStart;
    private Element elStrategy;
    private String mainSymbol = null;
    DataInfo mainSymbolInfo = null;
    private ChartSetup setup;
    private double slippage;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private double LimitOver;
    private boolean AllowBetterLimitFill;
    private String lastSettingsXml = null;
    private StrategyBase strategy;
    private boolean storeChartData = false;
    private boolean isAlgowizard = false;

    public StockpickerBacktestEngine() {
        this.tradeController = new Trader("TradeController", null);
        this.backtester = new PortfolioBacktester(this.pickerLog);
        this.trader = new PortfolioTrader(this.tradeController, this.pickerLog);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ResultsGroup runBacktest(String string) throws Exception {
        try {
            int n;
            Object object;
            this.checkListeners();
            OrdersList ordersList = null;
            long l = System.currentTimeMillis();
            long l2 = this.setup.getMainChart().getHistoryFrom();
            long l3 = this.setup.getMainChart().getHistoryTo();
            this.pickerLog.init(string, this.mainSymbol, l2, l3);
            Log.debug("Collecting trade signals...");
            this.lastEventListener.setLastEvent(L.t((String)"Collecting trade signals...", (Object[])new Object[0]));
            this.backtester.setStopPauseEngine(this.stopPauseEngine);
            this.backtester.setLastEventListener(this.lastEventListener);
            this.backtester.setStrategyXml(this.elStrategy);
            PickerEntrySignalComparatorByRevScore pickerEntrySignalComparatorByRevScore = new PickerEntrySignalComparatorByRevScore();
            this.backtester.setReducer(3 * this.MaxOpenPositionsLong, 3 * this.MaxOpenPositionsShort, pickerEntrySignalComparatorByRevScore);
            this.backtester.backtest();
            LoadedPickerData loadedPickerData = this.backtester.getPickerData();
            CollectedSignals collectedSignals = this.backtester.getSignals();
            ObjectArrayList<String> objectArrayList = new ObjectArrayList<String>();
            ObjectArrayList<String> objectArrayList2 = this.backtester.getSymbolsBacktested();
            if (!objectArrayList2.isEmpty()) {
                Log.debug("Executing trades based on the signals...");
                this.lastEventListener.setLastEvent(L.t((String)"Executing trades based on the signals...", (Object[])new Object[0]));
                this.trader.onStart(this.initialCapital, this.slippage, this.commission, this.swap, this.LimitOver, this.AllowBetterLimitFill);
                int n2 = 0;
                l2 = SQTime.getDateInMs((long)l2);
                l3 = SQTime.getDateInMs((long)l3);
                int n3 = loadedPickerData.timeline.searchIndexByTimeD(l2, true);
                int n4 = loadedPickerData.timeline.searchIndexByTimeD(l3, false);
                object = new IntOpenHashSet();
                for (int i = n3; i <= n4; ++i) {
                    int n5;
                    Object object2;
                    long l4;
                    Signals signals;
                    n = 50 + (int)((double)i / (double)n4 / 2.0 * 100.0);
                    if (n != n2 && (double)n % 10.0 == 0.0) {
                        this.backtestProgressListener.setProgress(n == 100 ? 95 : n);
                        n2 = n;
                    }
                    if ((signals = (Signals)collectedSignals.get(l4 = loadedPickerData.timeline.indexToTimeD(i))) != null && signals.exitSignalExists()) {
                        int n6;
                        if (signals.longEntrySignalExists()) {
                            object2 = signals.getLongEntrySignals().list();
                            for (n5 = 0; n5 < object2.size(); ++n5) {
                                n6 = ((PickerEntrySignal)object2.get((int)n5)).symbol.hashCode();
                                object.add(n6);
                            }
                        }
                        if (signals.shortEntrySignalExists()) {
                            object2 = signals.getShortEntrySignals().list();
                            for (n5 = 0; n5 < object2.size(); ++n5) {
                                n6 = ((PickerEntrySignal)object2.get((int)n5)).symbol.hashCode();
                                object.add(n6);
                            }
                        }
                        signals.getExitSignals().reduceCount((IntOpenHashSet)object);
                    }
                    if (this.checkStopped()) {
                        throw new TaskStoppedException();
                    }
                    if (this.pickerLog.storeLogs()) {
                        this.pickerLog.print("\n-------------------------------------------");
                        this.pickerLog.print(SQTime.toDateString((long)l4));
                        this.pickerLog.print(signals, this.trader, true);
                    }
                    this.trader.onBar(l4, i, loadedPickerData, signals);
                    if (this.pickerLog.storeLogs()) {
                        this.pickerLog.print(signals, this.trader, false);
                    }
                    object.clear();
                    object2 = this.trader.getOpenPositions();
                    for (n5 = 0; n5 < object2.size(); ++n5) {
                        LiveOrderObj liveOrderObj = (LiveOrderObj)object2.get(n5);
                        object.add(liveOrderObj.getSymbolHash());
                    }
                }
                this.trader.onClose();
                ordersList = this.trader.getHistoryOrders();
                objectArrayList = this.trader.getTradedSymbols();
            }
            n = this.backtester.getTotalTicks();
            double d = (double)(System.currentTimeMillis() - l) / 1000.0;
            ResultsGroup resultsGroup = null;
            resultsGroup = objectArrayList2.isEmpty() || objectArrayList.isEmpty() ? this.emptyRg(string, n, d) : this.createResultsGroup(string, objectArrayList, ordersList, n, d);
            this.checkBadStrategy(resultsGroup);
            if (this.pickerLog.storeLogs) {
                try {
                    object = "// " + String.format("Entry type: %s", PickerTriggerTypes.toString(this.strategy.Stockpicker.entryType)) + "\n// " + String.format("Exit type: %s", PickerTriggerTypes.toString(this.strategy.Stockpicker.exitType)) + "\n// " + String.format("Max open positions Long: %d", this.strategy.Stockpicker.MaxOpenPositionsLong) + "\n// " + String.format("Max open positions Short: %d", this.strategy.Stockpicker.MaxOpenPositionsShort) + "\n//\n// " + String.format("Symbols loaded: %d", this.backtester.getTotalSymbolsLoaded()) + "\n// " + String.format("Symbols backtested: %d", objectArrayList2.size()) + "\n// " + String.format("Symbols traded: %d", objectArrayList.size());
                    String string2 = this.pickerLog.toString((String)object);
                    resultsGroup.specialValues().set(SpecialValues.StockpickerLog, (Object)string2);
                }
                catch (Exception exception) {
                    Log.info("Failed to save StockpickerLog to strategy ResultsGroup...", (Throwable)exception);
                }
            }
            resultsGroup.specialValues().set(SpecialValues.StockpickerStrategy, (Object)true);
            resultsGroup.mainResult().setWorstDailyEquity(this.trader.getWorstDailyEquity());
            resultsGroup.mainResult().setMaxDailyDD(this.trader.getMaxDailyDD());
            resultsGroup.mainResult().setMaxDailyDDPct(this.trader.getMaxDailyDDPct());
            this.updateMaxOpenDD(resultsGroup);
            object = this.backtester.getExplore();
            if (object != null) {
                resultsGroup.specialValues().set(SpecialValues.Explore, object);
            }
            ResultsGroup resultsGroup2 = resultsGroup;
            return resultsGroup2;
        }
        finally {
            if (this.strategy != null && this.strategy.Stockpicker != null) {
                this.strategy.Stockpicker.clear();
            }
            if (this.strategy != null) {
                this.strategy.Stockpicker = null;
            }
            if (this.backtester != null) {
                this.backtester.clear();
            }
        }
    }

    private void checkBadStrategy(ResultsGroup resultsGroup) throws Exception {
        int n;
        int n2;
        if (this.isAlgowizard) {
            return;
        }
        int n3 = resultsGroup.specialValues().getInt("StrategyProblems", 0);
        int n4 = SettingsMap.getInt((Object)this.mainSettings.get("DismissBadStrategies"), (int)0);
        boolean bl = SettingsMap.getBool((Object)this.mainSettings.get("StrategyDismissWarnings"), (boolean)false);
        OrdersList ordersList = resultsGroup.orders();
        if (ordersList.size() < 20 && (n2 = BadStrategyException.setOrThrow(n4, bl, 2)) == 2) {
            n3 |= n2;
        }
        int n5 = 0;
        int n6 = 0;
        int n7 = 0;
        int n8 = 0;
        int n9 = 0;
        for (n = 0; n < ordersList.size(); ++n) {
            long l;
            Order order = ordersList.get(n);
            ++n6;
            if (!order.isFilledOrder()) continue;
            ++n5;
            if (order.PL == 0.0f) {
                ++n7;
            }
            if ((l = order.CloseTime - order.OpenTime) == 0L && order.OpenPrice == order.ClosePrice) {
                ++n8;
            }
            if (order.BarsInTrade != 0) continue;
            ++n9;
        }
        if (n5 == 0 && (n2 = BadStrategyException.setOrThrow(n4, bl, 1)) == 1) {
            n3 |= n2;
        }
        if ((double)n5 < (double)n6 * 0.1) {
            n3 |= BadStrategyException.setOrThrow(n4, bl, 256);
        }
        if ((n = n5 / 10) > 100) {
            n = 100;
        }
        if (n7 > n) {
            n3 |= BadStrategyException.setOrThrow(n4, bl, 4);
        }
        if (n8 > n) {
            n3 |= BadStrategyException.setOrThrow(n4, bl, 16);
        }
        if (n9 > n) {
            n3 |= BadStrategyException.setOrThrow(n4, bl, 8);
        }
        if ((n = n5 / 20) > 50) {
            n = 50;
        }
        resultsGroup.specialValues().set("StrategyProblems", (Object)n3);
    }

    private void updateMaxOpenDD(ResultsGroup resultsGroup) {
        try {
            SQStats sQStats = resultsGroup.portfolio().statsOrNull((byte)0, (byte)10, (byte)127);
            sQStats.set("OpenDrawdown", this.trader.getMaxOpenDrawdown());
            sQStats.set("OpenDrawdownPct", this.trader.getMaxOpenDrawdownPct());
            this.recalculateReturnOpenDDRatio(sQStats);
        }
        catch (Exception exception) {
            Log.error("Error while updating OpenDrawdown/OpenDrawdownPct stats...", (Throwable)exception);
        }
    }

    private void recalculateReturnOpenDDRatio(SQStats sQStats) {
        try {
            double d = sQStats.getDouble("NetProfit");
            double d2 = Math.abs(sQStats.getDouble("OpenDrawdown"));
            int n = sQStats.getInt("NumberOfTrades");
            if (n == 0) {
                sQStats.set("ReturnOpenDDRatio", 0.0);
                return;
            }
            if (d2 == 0.0) {
                if (d == 0.0) {
                    sQStats.set("ReturnOpenDDRatio", 0.0);
                } else {
                    sQStats.set("ReturnOpenDDRatio", 10.0);
                }
                return;
            }
            sQStats.set("ReturnOpenDDRatio", SQUtils.round2((double)SQUtils.safeDivide((double)d, (double)d2)));
        }
        catch (Exception exception) {
            Log.error("Error while recalculating ReturnOpenDDRatio...", (Throwable)exception);
        }
    }

    private void checkListeners() {
        if (this.lastEventListener == null) {
            this.setLastEventListener(new ILastEventListener(){

                @Override
                public void setLastEvent(String string) {
                }
            });
        }
        if (this.backtestProgressListener == null) {
            this.registerProgressListener(new IBacktestProgressListener(){

                @Override
                public void setProgress(int n) {
                }

                @Override
                public void increaseProgressStep() {
                }
            });
        }
    }

    private ResultsGroup emptyRg(String string, int n, double d) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(string);
        SettingsMap settingsMap = this.mainSettings;
        resultsGroup.symbols().add(this.mainSymbol, this.mainSymbolInfo.instrument, this.mainSymbolInfo.symbolInfo);
        Result result = new Result(this.mainSymbol, resultsGroup, settingsMap);
        result.setString(SpecialValues.Symbol, this.mainSymbol);
        result.setString(SpecialValues.Timeframe, "D1");
        resultsGroup.addSubresult(this.mainSymbol, settingsMap, result);
        StrategyBase strategyBase = StrategyBase.getStrategy(settingsMap);
        resultsGroup.portfolio().addStrategyXml(strategyBase.getStrategyXml());
        resultsGroup.portfolio().addStrategy(strategyBase);
        ChartSetup chartSetup = (ChartSetup)this.mainSettings.get("BacktestChart");
        ChartDef chartDef = chartSetup.getMainChart();
        resultsGroup.specialValues().set(SpecialValues.HistoryFrom, (Object)chartDef.getHistoryFrom());
        resultsGroup.specialValues().set(SpecialValues.HistoryTo, (Object)chartDef.getHistoryTo());
        resultsGroup.specialValues().set(SpecialValues.Precision, (Object)chartSetup.getTestPrecision());
        resultsGroup.specialValues().set(SpecialValues.BacktestDuration, (Object)d);
        resultsGroup.specialValues().set(SpecialValues.TotalTicks, (Object)n);
        resultsGroup.specialValues().set(SpecialValues.LastModified, (Object)System.currentTimeMillis());
        resultsGroup.specialValues().set(SpecialValues.Complexity, (Object)0);
        resultsGroup.setOOSSettings((OutOfSample)this.mainSettings.get("OutOfSample"));
        resultsGroup.computeAllStats();
        return resultsGroup;
    }

    private ResultsGroup createResultsGroup(String string, ObjectArrayList<String> objectArrayList, OrdersList ordersList, int n, double d) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(string);
        resultsGroup.setLastSettings(this.lastSettingsXml);
        SettingsMap settingsMap = this.mainSettings;
        resultsGroup.symbols().add(this.mainSymbol, this.mainSymbolInfo.instrument, this.mainSymbolInfo.symbolInfo);
        Result result = new Result(this.mainSymbol, resultsGroup, this.mainSettings);
        result.setString(SpecialValues.Symbol, this.mainSymbol);
        result.setString(SpecialValues.Timeframe, "D1");
        resultsGroup.addSubresult(this.mainSymbol, settingsMap, result);
        ordersList.sort(new OrderComparatorByTicket());
        this.recognizeOOS(ordersList, this.mainSettings.get("OutOfSample"), string);
        resultsGroup.orders().addAll(ordersList);
        ordersList.clear();
        if (resultsGroup.getResultKeys().size() > 1) {
            resultsGroup.createPortfolioResult();
        }
        StrategyBase strategyBase = StrategyBase.getStrategy(settingsMap);
        Element element = strategyBase.getStrategyXml();
        this.modifyStrategyXml(element);
        resultsGroup.portfolio().addStrategyXml(element);
        resultsGroup.portfolio().addStrategy(strategyBase);
        ChartSetup chartSetup = (ChartSetup)this.mainSettings.get("BacktestChart");
        ChartDef chartDef = chartSetup.getMainChart();
        resultsGroup.specialValues().set(SpecialValues.HistoryFrom, (Object)chartDef.getHistoryFrom());
        resultsGroup.specialValues().set(SpecialValues.HistoryTo, (Object)chartDef.getHistoryTo());
        resultsGroup.specialValues().set(SpecialValues.Precision, (Object)chartSetup.getTestPrecision());
        resultsGroup.specialValues().set(SpecialValues.BacktestDuration, (Object)d);
        resultsGroup.specialValues().set(SpecialValues.TotalTicks, (Object)n);
        resultsGroup.specialValues().set(SpecialValues.LastModified, (Object)System.currentTimeMillis());
        resultsGroup.specialValues().set(SpecialValues.Complexity, (Object)0);
        resultsGroup.setOOSSettings((OutOfSample)this.mainSettings.get("OutOfSample"));
        resultsGroup.computeAllStats();
        resultsGroup.mainResult().copyStats(resultsGroup.portfolio());
        if (this.storeChartData) {
            LoadedPickerData loadedPickerData = this.backtester.getPickerData();
            Stockpicker stockpicker = this.strategy.Stockpicker;
            result.addTradingChartsData(loadedPickerData, stockpicker, resultsGroup.orders(), this.isAlgowizard);
        }
        resultsGroup.specialValues().set("StrategyProblems", (Object)this.strategy.getStrategyProblems());
        return resultsGroup;
    }

    private void modifyStrategyXml(Element element) {
        if (this.isAlgowizard) {
            return;
        }
        try {
            Element element2 = element.getChild("Strategy");
            element2.setAttribute("entryTriggeredAt", PickerTriggerTypes.getKey(this.strategy.Stockpicker.entryType));
            element2.setAttribute("exitTriggeredAt", PickerTriggerTypes.getKey(this.strategy.Stockpicker.exitType));
            List list = element2.getChild("Rules").getChild("Events").getChildren("Event");
            for (int i = 0; i < list.size(); ++i) {
                Element element3 = (Element)list.get(i);
                List list2 = element3.getChildren("Rule");
                for (int j = 0; j < list2.size(); ++j) {
                    Object object;
                    String string;
                    Element element4;
                    int n;
                    String string2;
                    Element element5 = (Element)list2.get(j);
                    String string3 = element5.getAttributeValue("type");
                    if (string3.equals("StockpickerEntryExit")) {
                        string2 = element5.getAttributeValue("name");
                        n = string2.equalsIgnoreCase("Long") ? 1 : -1;
                        element4 = element5.getChildren("Exit").iterator();
                        if (!element4.hasNext() || (string = (object = (Element)element4.next()).getAttributeValue("atEndOfDay")) == null) continue;
                        string = "false";
                        if (n == 1) {
                            if (this.strategy.Stockpicker.eodLong != 10) {
                                string = "true";
                            }
                        } else if (this.strategy.Stockpicker.eodShort != 10) {
                            string = "true";
                        }
                        object.setAttribute("atEndOfDay", string);
                        continue;
                    }
                    if (!string3.equals("StockpickerPS") || this.strategy.Stockpicker.isSingleAssetStrategy()) continue;
                    string2 = element5.getAttributeValue("name");
                    n = string2.equalsIgnoreCase("Position Score Long") ? 1 : -1;
                    element4 = element5.getChild("Value");
                    object = element4.getChildren("Item").iterator();
                    while (object.hasNext()) {
                        string = (Element)object.next();
                        List list3 = string.getChildren("Param");
                        Element element6 = (Element)list3.get(0);
                        Element element7 = (Element)list3.get(1);
                        String string4 = element6.getAttributeValue("name");
                        if (!string4.equals("MaxOpenPositions")) continue;
                        if (n == 1) {
                            element7.setText(this.strategy.Stockpicker.MaxOpenPositionsLong + "");
                            continue;
                        }
                        element7.setText(this.strategy.Stockpicker.MaxOpenPositionsShort + "");
                    }
                }
            }
        }
        catch (Exception exception) {
            throw new Error("Error while modifying strategy xml - " + exception.getMessage(), exception);
        }
    }

    public static String createBasketName(String string) {
        if (string.startsWith("[") && string.endsWith("]")) {
            return string;
        }
        return "[" + string + "]";
    }

    private void recognizeOOS(OrdersList ordersList, Object object, String string) throws Exception {
        OutOfSample outOfSample = null;
        if (object != null) {
            outOfSample = (OutOfSample)object;
        }
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            order.Ticket = i + 1;
            order.SetupName = string;
            order.SampleType = outOfSample == null ? (byte)11 : outOfSample.getSampleType(order);
        }
    }

    @Override
    public void addSetup(SettingsMap settingsMap) throws Exception {
        Serializable serializable;
        this.mainSettings = settingsMap;
        this.isAlgowizard = settingsMap.getBoolean("IsAlgoWizard", false);
        if (!settingsMap.containsKey("BacktestChart") || !(settingsMap.get("BacktestChart") instanceof ChartSetup)) {
            throw new TradingException("Setting 'SettingsKeys.BacktestChart' is not set or has incorrect value! It must be an instance of ChartSetup object.");
        }
        double d = this.getMinDistance(settingsMap);
        this.strategy = StrategyBase.getStrategy(settingsMap);
        if (this.strategy.wasUsed()) {
            this.strategy = this.strategy.clone();
        }
        this.strategy.isAlgoWizard = this.isAlgowizard;
        if (settingsMap.containsKey("TradingOptions") && settingsMap.get("TradingOptions") instanceof TradingOptions) {
            serializable = (TradingOptions)settingsMap.get("TradingOptions");
            this.strategy.setTradingOptions((ArrayList<TradingOption>)serializable);
        }
        serializable = (ChartSetup)settingsMap.get("BacktestChart");
        serializable.setMinDistance(d);
        ChartDef chartDef = serializable.getMainChart();
        this.setup = serializable;
        this.mainSymbol = chartDef.getSymbol();
        this.mainSymbolInfo = DataManager.getDataInfo((String)"History", (String)this.mainSymbol, (boolean)true);
        if (this.mainSymbolInfo == null) {
            throw new TradingException(String.format("Symbol with name '%s' doesn't exist.", this.mainSymbol));
        }
        if (this.mainSymbolInfo.originalSymbol != null) {
            this.mainSymbol = this.mainSymbolInfo.originalSymbol;
        }
        this.dayStart = SQTime.correctDayStart((long)chartDef.getHistoryFrom());
        this.strategy.setSettings(settingsMap);
        this.strategy.callOnInit();
        if (!this.strategy.isStockpicker()) {
            throw new TradingException(String.format("Strategy '%s' is NOT Stockpicker strategy.", this.strategy.getStrategyName()));
        }
        if (this.strategy.Stockpicker.isSingleAssetStrategy()) {
            this.strategy.Stockpicker.MaxOpenPositionsLong = 1;
            this.strategy.Stockpicker.MaxOpenPositionsShort = 1;
        }
        this.MaxOpenPositionsLong = this.strategy.Stockpicker.MaxOpenPositionsLong;
        this.MaxOpenPositionsShort = this.strategy.Stockpicker.MaxOpenPositionsShort;
        this.trader.setMaxOpenPos(this.strategy.Stockpicker.MaxOpenPositionsLong, this.strategy.Stockpicker.MaxOpenPositionsShort);
        this.initialCapital = (Double)settingsMap.get("MoneyManagement.InitialCapital");
        this.slippage = 0.0;
        if (settingsMap.containsKey("Slippage") && settingsMap.get("Slippage") instanceof Double || settingsMap.get("Slippage") instanceof Integer) {
            this.slippage = settingsMap.getDouble("Slippage");
        }
        if (settingsMap.containsKey("Commission") && settingsMap.get("Commission") instanceof CommissionsMethod) {
            this.commission = (CommissionsMethod)settingsMap.get("Commission");
        }
        if (settingsMap.containsKey("Swap") && settingsMap.get("Swap") instanceof SwapMethod) {
            this.swap = (SwapMethod)settingsMap.get("Swap");
        }
        this.tradeController.setStrategy(this.strategy);
        this.backtester.addSetup(settingsMap);
        this.backtester.setStrategy(this.strategy);
        StockpickerOptions stockpickerOptions = this.strategy.getStockpickerOptions();
        this.pickerLog.storeLogs(stockpickerOptions != null ? stockpickerOptions.storeLogs() : true);
        this.AllowBetterLimitFill = stockpickerOptions != null ? stockpickerOptions.allowBetterLimitFill() : false;
        this.LimitOver = 0.0;
        TradingOption[] tradingOptionArray = this.strategy.getTradingOptions();
        if (tradingOptionArray != null) {
            for (int i = 0; i < tradingOptionArray.length; ++i) {
                TradingOption tradingOption = tradingOptionArray[i];
                if (!MainApp.isBacktestNode() && tradingOption instanceof StoreChartData) {
                    this.storeChartData = ((StoreChartData)tradingOption).StoreChartData;
                    continue;
                }
                if (!(tradingOption instanceof LimitOver)) continue;
                this.LimitOver = ((LimitOver)tradingOption).LimitOver;
            }
        }
        this.backtester.storeChartData(this.storeChartData);
        this.backtester.setDataModifierCallback(this.dataModifierCallback);
    }

    private double getMinDistance(SettingsMap settingsMap) throws TradingException {
        if (settingsMap.containsKey("MinDistance")) {
            try {
                return (Double)settingsMap.get("MinDistance");
            }
            catch (ClassCastException classCastException) {
                try {
                    return ((Integer)settingsMap.get("MinDistance")).intValue();
                }
                catch (ClassCastException classCastException2) {
                }
            }
        } else {
            return 0.0;
        }
        throw new TradingException("Setting 'TradingSetup.MinimumDistance was set, but it has incorrect value! It must be an int or double number!");
    }

    private boolean checkStopped() {
        return this.stopPauseEngine.isStopped();
    }

    @Override
    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
        this.backtester.registerProgressListener(iBacktestProgressListener);
        this.trader.registerProgressListener(iBacktestProgressListener);
    }

    @Override
    public void setStopPauseEngine(StopPauseEngine stopPauseEngine) {
        this.stopPauseEngine = stopPauseEngine;
    }

    public void setLastEventListener(ILastEventListener iLastEventListener) {
        this.lastEventListener = iLastEventListener;
    }

    public void addStrategyXml(Element element) {
        this.elStrategy = element;
    }

    public static ChartSetup createTempStockGroup(ChartSetup chartSetup) throws Exception {
        String string = chartSetup.getMainChart().getSymbol();
        String string2 = null;
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        if (dataInfo == null) {
            throw new Exception(L.t((String)"Data for connection '%s' and symbol '%s' cannot be found!", (Object[])new Object[]{"History", string}));
        }
        string2 = StockpickerBacktestEngine.createBasketName(string);
        int n = Math.abs(string2.hashCode()) * -1;
        BasketDto basketDto = BasketOfStocksManager.getInstance().getBasket(Integer.valueOf(n));
        if (basketDto == null) {
            basketDto = BasketOfStocksManager.getInstance().createCustomGroup(string2, n, dataInfo.symbol, true, null);
        }
        if ((dataInfo = DataManager.getDataInfo((String)"History", (String)string2)) == null) {
            DataManager.addCustomData((String)"History", (String)string2, (int)n, null);
        }
        return chartSetup.getClone(string2);
    }

    @Override
    public void setLastSettings(String string) {
        this.lastSettingsXml = string;
    }

    @Override
    public int getEngineId() {
        return 0;
    }

    @Override
    public BacktestEngine runBacktest() throws Exception {
        ResultsGroup resultsGroup = this.runBacktest("StockpickerBacktest");
        BacktestEngine backtestEngine = new BacktestEngine(null);
        backtestEngine.resultsGroup = resultsGroup;
        return backtestEngine;
    }

    @Override
    public double getGlobalATR() {
        return 0.0;
    }

    @Override
    public BacktestEngine runBacktest(String string, String string2, boolean bl) throws Exception {
        ResultsGroup resultsGroup = this.runBacktest(string);
        BacktestEngine backtestEngine = new BacktestEngine(null);
        backtestEngine.resultsGroup = resultsGroup;
        return backtestEngine;
    }
}

