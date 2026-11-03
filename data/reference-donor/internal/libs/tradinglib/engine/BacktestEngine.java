/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TaskStoppedException
 *  it.unimi.dsi.fastutil.ints.Int2ReferenceOpenHashMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.backtest.BacktestDataFeed;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.engine.AbstractBacktestEngine;
import com.strategyquant.tradinglib.engine.BacktestTradingSetup;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.exception.StrategyStoppedException;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime;
import com.strategyquant.tradinglib.setup.Portfolio;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.strategy.TraderUtils;
import it.unimi.dsi.fastutil.ints.Int2ReferenceOpenHashMap;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestEngine
extends AbstractBacktestEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestEngine");
    private static final String KEY_SEPARATOR = "/";
    private Portfolio portfolio = new Portfolio();
    private SettingsMap stopwatchData;
    private TradingEngine tradingEngine;
    private BacktestDataFeed backtestDataFeed;
    private ITradingSimulator defaultTradingSimulator;
    private HashMap<String, ITradingSimulator> tradingSimulators = new HashMap();
    public ResultsGroup resultsGroup = null;
    private int dismissBadStrategies = 0;
    private boolean warningsBadStrategies = false;
    private OutOfSample outOfSampleSettings = null;
    public static final AtomicLong backtestsCount = new AtomicLong(0L);
    private boolean isAlgowizard = false;

    public BacktestEngine(ITradingSimulator iTradingSimulator) {
        this.defaultTradingSimulator = iTradingSimulator;
    }

    @Override
    public void addSetup(SettingsMap settingsMap) throws Exception {
        this._addSetup(settingsMap, new String[0]);
    }

    private String _addSetup(SettingsMap settingsMap, String ... stringArray) throws Exception {
        Object object;
        Serializable serializable;
        if (!settingsMap.containsKey("BacktestChart") || !(settingsMap.get("BacktestChart") instanceof ChartSetup)) {
            throw new TradingException("Setting 'SettingsKeys.BacktestChart' is not set or has incorrect value! It must be an instance of ChartSetup object.");
        }
        settingsMap.set("ApplyExitsAtTheEndOfRule", (Object)this.defaultTradingSimulator.getApplyExitsAtTheEndOfRule());
        double d = this.getMinDistance(settingsMap);
        StrategyBase strategyBase = StrategyBase.getStrategy(settingsMap);
        if (strategyBase.wasUsed()) {
            strategyBase = strategyBase.clone();
        }
        this.isAlgowizard = settingsMap.getBoolean("IsAlgoWizard", false);
        if (settingsMap.containsKey("TradingOptions") && settingsMap.get("TradingOptions") instanceof TradingOptions) {
            serializable = (TradingOptions)settingsMap.get("TradingOptions");
            object = strategyBase.variables().get("Day_Trade_On");
            if (object != null && ((Variable)object).getValueAsInt() == 1) {
                for (int i = 0; i < ((ArrayList)serializable).size(); ++i) {
                    TradingOption tradingOption = (TradingOption)((ArrayList)serializable).get(i);
                    if (!tradingOption.getClass().getSimpleName().equals("ExitAtEndOfDay")) continue;
                    tradingOption.setParameterValue("ExitAtEndOfDay", "true");
                    tradingOption.setParameterValue("EODExitTime", "0");
                    break;
                }
            }
            strategyBase.setTradingOptions((ArrayList<TradingOption>)serializable);
        }
        if (settingsMap.containsKey("ATM") && (serializable = (ATM)settingsMap.get("ATM")) instanceof ATM) {
            strategyBase.setATM((ATM)serializable);
        }
        serializable = (ChartSetup)settingsMap.get("BacktestChart");
        ((ChartSetup)serializable).setMinDistance(d);
        if (stringArray.length == 0) {
            stringArray = new String[]{((ChartSetup)serializable).getCharts().get(0).getConnectionName()};
            object = stringArray[0];
        } else {
            object = stringArray[0];
        }
        strategyBase.setTradeControllers((String)object, this.getTradeControllers(stringArray, settingsMap));
        BacktestTradingSetup backtestTradingSetup = new BacktestTradingSetup(this, (ChartSetup)serializable, settingsMap, strategyBase);
        if (settingsMap.containsKey("DismissBadStrategies")) {
            this.dismissBadStrategies = settingsMap.getInt("DismissBadStrategies");
        }
        if (settingsMap.containsKey("StrategyDismissWarnings")) {
            this.warningsBadStrategies = settingsMap.getBoolean("StrategyDismissWarnings");
        }
        this.outOfSampleSettings = (OutOfSample)settingsMap.get("OutOfSample");
        return this.portfolio.add(backtestTradingSetup);
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

    private Trader[] getTradeControllers(String[] stringArray, SettingsMap settingsMap) throws DataException, TradingException {
        Trader[] traderArray = new Trader[stringArray.length];
        for (int i = 0; i < stringArray.length; ++i) {
            String string = stringArray[i];
            traderArray[i] = new Trader(string, this.getTradingSimulator(string, settingsMap));
        }
        return traderArray;
    }

    private IExecutionEngine getTradingSimulator(String string, SettingsMap settingsMap) throws TradingException {
        if (!this.tradingSimulators.containsKey(string)) {
            ITradingSimulator iTradingSimulator = this.defaultTradingSimulator.clone();
            iTradingSimulator.setConnection(string);
            iTradingSimulator.initSettings(settingsMap);
            this.tradingSimulators.put(string, iTradingSimulator);
        }
        return this.tradingSimulators.get(string);
    }

    @Override
    public BacktestEngine runBacktest() throws Exception {
        return this.runBacktest(null, null, false);
    }

    public BacktestEngine runBacktest(boolean bl) throws Exception {
        return this.runBacktest(null, null, bl);
    }

    @Override
    public BacktestEngine runBacktest(String string, String string2, boolean bl) throws Exception {
        return this.runBacktest(string, string2, bl, false);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public BacktestEngine runBacktest(String string, String string2, boolean bl, boolean bl2) throws Exception {
        block10: {
            long l = System.currentTimeMillis();
            this.stopwatchData = new SettingsMap();
            try {
                this.initializeBacktest();
                this.backtestDataFeed.start();
                if (bl || this.loadDataProgressEngine == null) {
                    long l2 = System.currentTimeMillis();
                    this.computeResults(string, string2, l2 - l, bl2);
                    this.initGlobalATR();
                    if (Log.isDebugEnabled()) {
                        Log.debug("Backtest finished in : {} ms.", (Object)(l2 - l));
                        Log.debug("Stats computation finished in : {} ms.", (Object)(System.currentTimeMillis() - l2));
                    }
                    this.stopwatchData.set("TotalRunTime", (Object)(System.currentTimeMillis() - l));
                }
            }
            catch (Exception exception) {
                if (exception instanceof TaskStoppedException) {
                    Log.info("Task stopped");
                    throw exception;
                }
                if (exception instanceof StrategyStoppedException) {
                    Log.info("Strategy stopped manually with reason: " + exception.getMessage());
                    break block10;
                }
                throw exception;
            }
            finally {
                this.destroyRemainingObjects();
                this.portfolio.deinitialize();
                this.transferSpecialValuesToResultsGroup();
                if (this.tradingEngine != null) {
                    this.tradingEngine.deinitialize();
                }
                backtestsCount.incrementAndGet();
            }
        }
        return this;
    }

    private void transferSpecialValuesToResultsGroup() {
        if (this.resultsGroup == null || this.portfolio == null) {
            return;
        }
        TradingSetup tradingSetup = this.portfolio.getFirstTradingSetup();
        if (tradingSetup == null) {
            return;
        }
        StrategyBase strategyBase = tradingSetup.getStrategy();
        if (strategyBase == null) {
            return;
        }
        SettingsMap settingsMap = strategyBase.getSpecialValues();
        if (settingsMap == null) {
            return;
        }
        for (String string : settingsMap.getAllKeys()) {
            Object object;
            if (string == null || (object = settingsMap.get(string)) == null) continue;
            this.resultsGroup.specialValues().set(string, object);
        }
    }

    private void initGlobalATR() {
        TradingSetup tradingSetup = this.portfolio.getTradingSetups().get(0);
        this.globalATR = tradingSetup.getGlobalATR();
    }

    public ResultsGroup getResults() {
        return this.resultsGroup;
    }

    private void computeResults(String string, String string2, long l, boolean bl) throws Exception {
        TradingSetup tradingSetup;
        if (this.resultsGroup != null) {
            return;
        }
        SettingsMap settingsMap = this.portfolio.getFirstTradingSetup().getSettings();
        StrategyBase strategyBase = this.portfolio.getFirstTradingSetup().getStrategy();
        if (string == null) {
            string = (String)settingsMap.get("ResultGroupName");
        }
        if (string == null) {
            string = (String)settingsMap.get("StrategyName");
        }
        if (string == null) {
            string = strategyBase.getStrategyName();
        }
        this.resultsGroup = new ResultsGroup(string);
        this.resultsGroup.setLastSettings(this.lastSettingsXml);
        if (strategyBase.Explore != null) {
            this.resultsGroup.specialValues().set(SpecialValues.Explore, (Object)strategyBase.Explore);
        }
        OrdersList ordersList = TraderUtils.getHistoryOrders(strategyBase.Trader("History"));
        if (bl) {
            ordersList.removeEndOfTest();
        }
        ordersList.sort(new OrderComparatorByOpenTime());
        long l2 = -1L;
        int n = 0;
        if (settingsMap.containsKey("StrategyCheckDate")) {
            l2 = settingsMap.getLong("StrategyCheckDate");
        }
        if (l2 > 0L) {
            n = (int)((double)this.portfolio.getFirstTradingSetup().getMarketData().Chart(0).Bars() * 0.3);
        }
        if (BadStrategyException.check(this.dismissBadStrategies, 1) && ordersList.size() == 0) {
            this.destroyRemainingObjects();
            throw new BadStrategyException(1);
        }
        Int2ReferenceOpenHashMap int2ReferenceOpenHashMap = new Int2ReferenceOpenHashMap();
        double d = 0.0;
        SettingsMap settingsMap2 = null;
        Element element = null;
        int n2 = 0;
        ArrayList<TradingSetup> arrayList = this.portfolio.getTradingSetups();
        for (int i = 0; i < arrayList.size(); ++i) {
            String string3;
            Object object;
            Object object2;
            tradingSetup = arrayList.get(i);
            String string4 = null;
            String string5 = tradingSetup.getName();
            SettingsMap settingsMap3 = tradingSetup.getSettings();
            if (i == 0 && string2 != null) {
                string4 = string2;
            } else {
                if (i == 0) {
                    object2 = tradingSetup.getChartSetup().getCharts().get(0).getSymbol();
                    String string6 = tradingSetup.getChartSetup().getCharts().get(0).getTimeframe();
                    string4 = "Main: " + (String)object2 + KEY_SEPARATOR + string6;
                }
                if (string4 == null) {
                    string4 = tradingSetup.getName();
                }
            }
            object2 = tradingSetup.getStrategy();
            n2 += ((StrategyBase)object2).getAmbiguousTrades();
            int n3 = 0;
            if (object2 != null) {
                n3 = ((StrategyBase)object2).getStrategyProblems();
            }
            d += settingsMap3.getDouble("MoneyManagement.InitialCapital");
            settingsMap3.set("StrategyDismissSettings", (Object)tradingSetup.getDismissBadStrategies());
            settingsMap3.set("StrategyDismissWarnings", (Object)tradingSetup.getWarningsBadStrategies());
            ChartSetup chartSetup = (ChartSetup)settingsMap3.get("BacktestChart");
            int n4 = chartSetup.getTestPrecision();
            settingsMap3.set("BacktestPrecision", (Object)n4);
            this.resultsGroup.addSubresult(string4, settingsMap3);
            int n5 = string4.hashCode();
            int2ReferenceOpenHashMap.clear();
            for (int j = 0; j < ordersList.size(); ++j) {
                object = ordersList.get(j);
                if (((Order)object).SetupName.hashCode() == n5 && !int2ReferenceOpenHashMap.containsKey(((Order)object).Symbol.hashCode())) {
                    int2ReferenceOpenHashMap.put(((Order)object).Symbol.hashCode(), (Object)((Order)object).Symbol);
                }
                if (n5 != string5.hashCode() && ((Order)object).SetupName.hashCode() == string5.hashCode()) {
                    ((Order)object).SetupName = string4;
                }
                if (n <= 0 || ((Order)object).BarsInTrade <= n) continue;
                n3 |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 64);
            }
            if (ordersList.size() == 0 && !int2ReferenceOpenHashMap.containsKey((string3 = tradingSetup.getChartSetup().getCharts().get(0).getSymbol()).hashCode())) {
                int2ReferenceOpenHashMap.put(string3.hashCode(), (Object)string3);
            }
            HashMap<String, InstrumentInfo> hashMap = tradingSetup.getInstrumentsInfoMap();
            for (String string7 : hashMap.keySet()) {
                InstrumentInfo instrumentInfo = hashMap.get(string7);
                this.resultsGroup.symbols().add(string7, instrumentInfo.instrument, instrumentInfo);
            }
            for (String string7 : int2ReferenceOpenHashMap.values()) {
                this.resultsGroup.addResultSymbol(string4, string7);
            }
            if (settingsMap2 == null) {
                settingsMap2 = tradingSetup.getSettings();
            }
            object = this.resultsGroup.subResult(string4);
            if (tradingSetup.getSettings().getBoolean("StoreChartData", false)) {
                ((Result)((Object)object)).addTradingChartsData(tradingSetup, ordersList, this.isAlgowizard);
            }
            ((Result)((Object)object)).setWorstDailyEquity(TraderUtils.getWorstDailyEquity(tradingSetup.getStrategy().Trader("History")));
            element = tradingSetup.getStrategy().getStrategyXml();
            if (element != null) {
                ((Result)((Object)object)).addStrategyXml(element);
            }
            ((Result)((Object)object)).setStrategyProblems(n3);
        }
        settingsMap = this.resultsGroup.portfolio().getSettings();
        settingsMap.setIfNotExists("MoneyManagement.InitialCapital", (Object)d);
        if (settingsMap2 != null) {
            settingsMap.setIfNotExists("OutOfSample", settingsMap2.get("OutOfSample"));
        }
        if (element != null) {
            this.resultsGroup.portfolio().addStrategyXml(element);
        }
        ChartSetup chartSetup = (ChartSetup)settingsMap2.get("BacktestChart");
        tradingSetup = chartSetup.getMainChart();
        this.resultsGroup.subResult(string2).setString(SpecialValues.Symbol, chartSetup.getSymbol());
        this.resultsGroup.subResult(string2).setString(SpecialValues.Timeframe, chartSetup.getTimeframe());
        this.resultsGroup.specialValues().set(SpecialValues.HistoryFrom, (Object)tradingSetup.getHistoryFrom());
        this.resultsGroup.specialValues().set(SpecialValues.HistoryTo, (Object)tradingSetup.getHistoryTo());
        this.resultsGroup.specialValues().set(SpecialValues.Precision, (Object)chartSetup.getTestPrecision());
        this.resultsGroup.specialValues().set(SpecialValues.BacktestDuration, (Object)SQUtils.round((double)((double)l / 1000.0), (int)2));
        this.resultsGroup.specialValues().set(SpecialValues.TotalTicks, (Object)this.backtestDataFeed.getTotalTicks());
        this.resultsGroup.specialValues().set(SpecialValues.LastModified, (Object)System.currentTimeMillis());
        this.resultsGroup.specialValues().set(SpecialValues.AmbiguousTrades, (Object)n2);
        this.resultsGroup.specialValues().set(SpecialValues.Complexity, (Object)this.computeDegreesOfFreedom(element));
        this.resultsGroup.orders().addAll(ordersList);
        ordersList.clear();
        this.recognizeOOS(settingsMap.get("OutOfSample"));
        this.resultsGroup.setOOSSettings((OutOfSample)settingsMap.get("OutOfSample"));
        this.resultsGroup.computeAllStats();
        this.destroyRemainingObjects();
    }

    private int computeDegreesOfFreedom(Element element) {
        if (element == null) {
            return 0;
        }
        try {
            StrategyBase strategyBase = StrategyBase.createXmlStrategy(element.clone().detach());
            strategyBase.transformToVariables(true, ParametersSettings.AllParamTypes);
            Variables variables = strategyBase.variables();
            int n = 0;
            for (Variable variable : variables) {
                byte by = variable.getInternalType();
                String string = variable.getName();
                if (string.contains("EntrySignal") || string.contains("ExitSignal") || string.contains("ReplaceExistingOrders") || string.startsWith("Magic") || by == 3 || by == 0 || by == 2) continue;
                ++n;
            }
            int n2 = this.countConditionsInStrategy(element);
            return n + n2;
        }
        catch (Exception exception) {
            Log.error("Cannot compute degrees of freedom: ", (Throwable)exception);
            return 0;
        }
    }

    private int countConditionsInStrategy(Element element) {
        List list = element.getChildren();
        int n = 0;
        if (list != null && list.size() > 0) {
            for (int i = 0; i < list.size(); ++i) {
                Element element2 = (Element)list.get(i);
                if (element2.getName().equals("Item")) {
                    String string = element2.getAttributeValue("returnType");
                    String string2 = element2.getAttributeValue("key");
                    if (!(string == null || !string.equals("boolean") || string2.equals("BooleanVariable") || string2.equals("Not") || string2.equals("Boolean") || string2.equals("MarketPositionIsLong") || string2.equals("MarketPositionIsShort"))) {
                        ++n;
                    }
                }
                if (element2.getName().equals("CustomBlocks")) continue;
                n += this.countConditionsInStrategy(element2);
            }
            return n;
        }
        return 0;
    }

    private void printKeys(String string, String[] stringArray) {
        String string2 = "";
        for (String string3 : stringArray) {
            string2 = string2 + string3 + ",";
        }
        Log.info(string + " - All keys: " + string2);
    }

    private void destroyRemainingObjects() {
        if (this.portfolio != null) {
            for (TradingSetup tradingSetup : this.portfolio.getTradingSetups()) {
                tradingSetup.getStrategy().destroyHistoryTrades();
            }
        }
    }

    private void recognizeOOS(Object object) throws Exception {
        OutOfSample outOfSample = null;
        if (object != null) {
            outOfSample = (OutOfSample)object;
        }
        for (int i = 0; i < this.resultsGroup.orders().size(); ++i) {
            Order order = this.resultsGroup.orders().get(i);
            order.SampleType = outOfSample == null ? (byte)11 : outOfSample.getSampleType(order);
        }
    }

    private void initializeBacktest() throws Exception {
        ConnectionManager connectionManager = new ConnectionManager();
        this.tradingEngine = new TradingEngine(connectionManager);
        this.backtestDataFeed = new BacktestDataFeed(this.defaultTradingSimulator.getTestPrecision(), connectionManager, this.defaultTradingSimulator, this.getSimulatorsAsArray());
        this.backtestDataFeed.setDataModifierCallback(this.dataModifierCallback);
        this.backtestDataFeed.setStopPauseEngine(this.stopPauseEngine);
        this.backtestDataFeed.setLoadDataProgressEngine(this.loadDataProgressEngine);
        this.initTradingSetups();
        this.runChecks();
        this.portfolio.initialize();
        this.initializeDataFeedEngine();
        for (TradingSetup tradingSetup : this.portfolio.getTradingSetups()) {
            tradingSetup.start(this.singleThreaded);
        }
    }

    private ITradingSimulator[] getSimulatorsAsArray() {
        Collection<ITradingSimulator> collection = this.tradingSimulators.values();
        ITradingSimulator[] iTradingSimulatorArray = new ITradingSimulator[collection.size()];
        int n = 0;
        for (ITradingSimulator iTradingSimulator : collection) {
            iTradingSimulatorArray[n++] = iTradingSimulator;
        }
        return iTradingSimulatorArray;
    }

    private void initTradingSetups() throws Exception {
        for (TradingSetup tradingSetup : this.portfolio.getTradingSetups()) {
            BacktestTradingSetup backtestTradingSetup = (BacktestTradingSetup)tradingSetup;
            backtestTradingSetup.setTradingEngine(this.tradingEngine);
            backtestTradingSetup.setUsePreparedData(this.usePreparedData);
            backtestTradingSetup.initRunnable(null);
            backtestTradingSetup.setProgressListener(this.backtestProgressListener);
            backtestTradingSetup.initTradingOptions();
        }
    }

    private void initializeDataFeedEngine() throws Exception {
        long l = System.currentTimeMillis();
        this.backtestDataFeed.initialize(this.portfolio, this.defaultTradingSimulator, this.outOfSampleSettings);
        this.stopwatchData.set("LoadDataTime", (Object)(System.currentTimeMillis() - l));
    }

    protected void runChecks() throws TradingException {
        if (this.portfolio == null) {
            throw new TradingException("Initialization: PortfolioSetup cannot be null!");
        }
        this.portfolio.runChecks();
    }

    @Override
    public int getEngineId() {
        return this.defaultTradingSimulator.getEngineId();
    }

    public ArrayList<TradingSetup> getTradingSetups() {
        return this.portfolio.getTradingSetups();
    }

    @Override
    public double getGlobalATR() {
        return this.globalATR;
    }

    public MarketData getMarketData() throws Exception {
        block8: {
            try {
                this.stopwatchData = new SettingsMap();
                this.initializeBacktest();
                MarketData marketData = this.backtestDataFeed.getMarketData();
                return marketData;
            }
            catch (Exception exception) {
                if (exception instanceof TaskStoppedException) {
                    Log.info("Task stopped");
                    throw exception;
                }
                if (exception instanceof StrategyStoppedException) {
                    Log.info("Strategy stopped manually with reason: " + exception.getMessage());
                    break block8;
                }
                throw exception;
            }
            finally {
                this.destroyRemainingObjects();
                this.portfolio.deinitialize();
                if (this.tradingEngine != null) {
                    this.tradingEngine.deinitialize();
                }
                backtestsCount.incrementAndGet();
            }
        }
        return null;
    }
}

