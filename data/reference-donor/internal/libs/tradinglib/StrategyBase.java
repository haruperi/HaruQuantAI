/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.event.ITradingEvent;
import com.strategyquant.tradinglib.exception.StrategyStoppedException;
import com.strategyquant.tradinglib.explore.Explore;
import com.strategyquant.tradinglib.generator.StrategyGenerator;
import com.strategyquant.tradinglib.indicator.IndicatorsCache;
import com.strategyquant.tradinglib.indicator.IndicatorsObj;
import com.strategyquant.tradinglib.optimization.IStrategyModifier;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import com.strategyquant.tradinglib.options.parameters.StockpickerOptions;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.strategy.StrategiesList;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class StrategyBase
extends ChartData {
    public static final Logger DefaultLog = LoggerFactory.getLogger((String)"StrategyBase");
    private final String reasonNo = "No reason specified";
    protected TradingSetup tradingSetup;
    public int UpdatedChart = -1;
    public boolean MultipleChartsUpdated = false;
    public int UpdateEventType = 0;
    public Trader Trader;
    private int[] tradersMap = null;
    private Trader[] tradersArray = null;
    protected Logger Log = null;
    protected String strategyName;
    private String setupName;
    private SettingsMap settings;
    protected Variables variables = null;
    protected Element xmlStrategy;
    protected TradingOption[] tradingOptions;
    private boolean wasUsed = false;
    private int badStrategyChecks = 0;
    protected int dismissBadStrategies;
    protected boolean warningsBadStrategies;
    private int strategyProblems = 0;
    private long progressUpdateTime = -1L;
    private long progressTotalHistoryFrom;
    private long progressTotalHistoryTo;
    private double progressDiff;
    private int progressLastBarChecked;
    private static IStrategyModifier strategyModifier = null;
    private long strategyCheckDate = -1L;
    protected MoneyManagementMethod globalMMMethod = null;
    private boolean firstCallEvaluateOptions = true;
    private int updateProgressTicks = 0;
    private boolean applyExitsAtTheEndOfRule = false;
    protected TradingOption endOfdayExit;
    private int engine;
    private HashMap<String, Element> cbMap;
    private ATM atm = null;
    public static final int ValueNotDefined = -999999;
    public double accountBalance = -999999.0;
    public double accountEquity = -999999.0;
    public double initialCapital = -999999.0;
    private int ambigouousTrades = -1;
    public boolean isAlgoWizard = false;
    public Stockpicker Stockpicker = null;
    public Explore Explore;
    public final SettingsMap specialValues = new SettingsMap();

    public StrategyBase() {
        this.Log = LoggerFactory.getLogger((String)("Strategy[" + this.getClass().getSimpleName() + "]"));
    }

    @Override
    protected void initializeFromMarketData(MarketData marketData) {
        super.initializeFromMarketData(marketData);
        for (int i = 0; i < this.tradersArray.length; ++i) {
            this.tradersArray[i].initialize(marketData);
        }
        this.badStrategyChecks = 0;
        this.wasUsed = true;
    }

    public void setTradeControllers(String string, Trader[] traderArray) {
        if (this.tradersArray != null) {
            for (int i = 0; i < this.tradersArray.length; ++i) {
                this.tradersArray[i].destroy();
            }
        }
        this.tradersArray = traderArray;
        this.tradersMap = new int[this.tradersArray.length];
        this.initializeTradersMap();
        this.Trader = this.Trader(string);
    }

    protected void initializeTradeControllers() {
        for (int i = 0; i < this.tradersArray.length; ++i) {
            this.tradersArray[i].initialize(this.MarketData);
        }
    }

    public void updateTradeControllers() {
        if (this.MarketData.Chart(0).isUpdated() && (this.MarketData.Chart((int)0).EventType == 2 || this.MarketData.Chart((int)0).EventType == 3)) {
            for (int i = 0; i < this.tradersArray.length; ++i) {
                this.tradersArray[i].eventBarUpdated(this.MarketData.Chart((int)0).EventType);
            }
        }
        if (this.MarketData.Chart((int)0).EventType == 5) {
            throw new IllegalArgumentException("This should't happen - Trade controller will not work correctly if it is not notified on every bar open and close!!! Fix it!");
        }
    }

    public abstract void callOnInit(TradingSetup var1) throws Exception;

    public void callOnInit() throws Exception {
    }

    protected void setUpdateEventType(int n) throws TradingException {
        if (!this.tradingSetup.isInInit()) {
            throw new TradingException("You cannot call Strategy.setEventType() outside the Strategy.onInit() method !");
        }
        if (n == 2 || n == 3 || n == 4 || n == 6) {
            this.requestedEventType = n;
        }
    }

    public int getEventType() {
        return this.requestedEventType;
    }

    public abstract void Initialize() throws Exception;

    public abstract void OnBarUpdate() throws Exception;

    public void Deinitialize() throws Exception {
    }

    public void OnEvent(ITradingEvent iTradingEvent) throws Exception {
    }

    public StrategyBase clone() throws CloneNotSupportedException {
        try {
            Object obj = this.getClass().newInstance();
            return (StrategyBase)obj;
        }
        catch (IllegalAccessException | IllegalArgumentException | InstantiationException | SecurityException exception) {
            DefaultLog.info(String.format("Strategy %s cannot be cloned using its constructor. Does it have a contructor with parameters?", this.getClass().getSimpleName()));
            throw new CloneNotSupportedException(String.format("Strategy cannot be cloned using its constructor. Does it have a contructor with parameters? Reason: %s", exception.getMessage()));
        }
    }

    protected void setReservedBars(int n) throws TradingException {
        if (!this.tradingSetup.isInInit()) {
            throw new TradingException("You cannot call Strategy.setReservedBars() outside the Strategy.onInit() method !");
        }
        this.tradingSetup.setReservedBars(n);
    }

    public boolean hasTrader(String string) {
        int n = string.hashCode();
        for (int i = 0; i < this.tradersMap.length; ++i) {
            if (this.tradersMap[i] != n) continue;
            return true;
        }
        return false;
    }

    public Trader Trader(String string) {
        int n = string.hashCode();
        for (int i = 0; i < this.tradersMap.length; ++i) {
            if (this.tradersMap[i] != n) continue;
            return this.tradersArray[i];
        }
        throw new IllegalArgumentException("Connection '" + string + "' doesn't exist!");
    }

    protected void StopStrategy() throws StrategyStoppedException {
        this.StopStrategy("No reason specified");
    }

    protected void StopStrategy(String string) throws StrategyStoppedException {
        throw new StrategyStoppedException(string);
    }

    public String getStrategyName() {
        if (this.strategyName == null) {
            this.strategyName = this.getClass().getSimpleName().intern();
        }
        return this.strategyName;
    }

    public void setStrategyName(String string) {
        this.strategyName = string;
    }

    public void setSetupName(String string) {
        this.setupName = string.intern();
    }

    public String getSetupName() {
        return this.setupName;
    }

    public void addTrader(String string, Trader trader) {
        if (this.tradersArray != null) {
            for (int i = 0; i < this.tradersMap.length; ++i) {
                if (this.tradersMap[i] != string.hashCode()) continue;
                this.tradersArray[i] = trader;
                return;
            }
        }
        Trader[] traderArray = this.tradersArray == null ? new Trader[1] : new Trader[this.tradersArray.length + 1];
        for (int i = 0; i < this.tradersArray.length; ++i) {
            traderArray[i] = this.tradersArray[i];
        }
        traderArray[this.tradersArray.length] = trader;
        this.tradersArray = traderArray;
        this.initializeTradersMap();
    }

    private void initializeTradersMap() {
        this.tradersMap = new int[this.tradersArray.length];
        for (int i = 0; i < this.tradersArray.length; ++i) {
            Trader trader = this.tradersArray[i];
            trader.setStrategy(this);
            this.tradersMap[i] = trader.getName().hashCode();
        }
    }

    public void setSettings(SettingsMap settingsMap) {
        this.applyExitsAtTheEndOfRule = settingsMap.getBoolean("ApplyExitsAtTheEndOfRule", false);
        this.settings = settingsMap;
        if (this.tradersArray != null) {
            for (int i = 0; i < this.tradersArray.length; ++i) {
                this.tradersArray[i].setSettings(settingsMap);
            }
        }
    }

    public SettingsMap getSettings() {
        return this.settings;
    }

    public StrategyBase newInstance() throws NoSuchMethodException, SecurityException {
        Constructor<?> constructor = this.getClass().getConstructor(new Class[0]);
        StrategyBase strategyBase = (StrategyBase)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
        return strategyBase;
    }

    public Variables variables() {
        if (this.variables == null) {
            this.initVariablesFromClass();
        }
        return this.variables;
    }

    private void initVariablesFromClass() {
        this.variables = new Variables(this);
    }

    public void destroyHistoryTrades() {
        if (this.tradersArray != null) {
            for (int i = 0; i < this.tradersArray.length; ++i) {
                this.tradersArray[i].destroy();
            }
        }
    }

    public IndicatorsCache getIndicatorsCache() {
        return null;
    }

    public double convertPipsToRealPrice(String string, double d) throws TradingException {
        InstrumentInfo instrumentInfo = this.isStockpicker() ? this.SymbolInfo : this.MarketData.getInstrumentInfo(string);
        if (instrumentInfo == null) {
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
            if (dataInfo == null || dataInfo.symbolInfo == null) {
                throw new TradingException(String.format("Instrument info for symbol '%s doens't exist", string));
            }
            instrumentInfo = dataInfo.symbolInfo;
        }
        return SQUtils.round((double)(d * instrumentInfo.tickSize), (int)6);
    }

    public double convertRealPriceToPips(String string, double d) throws TradingException {
        InstrumentInfo instrumentInfo = this.isStockpicker() ? this.SymbolInfo : this.MarketData.getInstrumentInfo(string);
        if (instrumentInfo == null) {
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
            if (dataInfo == null || dataInfo.symbolInfo == null) {
                throw new TradingException(String.format("Instrument info for symbol '%s doesn't exist", string));
            }
            instrumentInfo = dataInfo.symbolInfo;
        }
        return SQUtils.round((double)(d / instrumentInfo.tickSize), (int)2);
    }

    public Element getStrategyXml() {
        return this.xmlStrategy;
    }

    protected void updateStrategyXML(Element element) {
        this.xmlStrategy = element;
    }

    public void setTradingOptions(ArrayList<TradingOption> arrayList) {
        this.tradingOptions = this.transformToPrimitiveArray(arrayList);
    }

    private TradingOption[] transformToPrimitiveArray(ArrayList<TradingOption> arrayList) {
        if (arrayList == null) {
            return null;
        }
        TradingOption[] tradingOptionArray = new TradingOption[arrayList.size()];
        int n = 0;
        for (TradingOption tradingOption : arrayList) {
            tradingOptionArray[n++] = tradingOption;
        }
        return tradingOptionArray;
    }

    protected boolean evaluateOptions() throws Exception {
        if (this.tradingOptions == null || this.tradingOptions.length == 0) {
            return true;
        }
        if (this.firstCallEvaluateOptions) {
            this.firstCallEvaluateOptions = false;
            this.initOptions();
        }
        boolean bl = true;
        for (int i = 0; i < this.tradingOptions.length; ++i) {
            if (this.tradingOptions[i].OnBarUpdate(this)) continue;
            bl = false;
        }
        return bl;
    }

    public void callOptionsOnTick(TickEvent tickEvent) throws Exception {
        if (this.tradingOptions == null || this.tradingOptions.length == 0) {
            return;
        }
        if (this.firstCallEvaluateOptions) {
            this.firstCallEvaluateOptions = false;
            this.initOptions();
        }
        for (int i = 0; i < this.tradingOptions.length; ++i) {
            this.tradingOptions[i].OnTick(this, tickEvent, true);
        }
    }

    private void initOptions() {
        if (this.tradingOptions == null) {
            return;
        }
        int n = 0;
        for (int i = 0; i < this.tradingOptions.length; ++i) {
            if (!this.tradingOptions[i].isUsedInTrading()) {
                this.tradingOptions[i] = null;
                continue;
            }
            ++n;
            if (!this.tradingOptions[i].getClass().getSimpleName().equals("ExitAtEndOfDay")) continue;
            this.endOfdayExit = this.tradingOptions[i];
        }
        if (n != this.tradingOptions.length) {
            TradingOption[] tradingOptionArray = new TradingOption[n];
            int n2 = 0;
            for (int i = 0; i < this.tradingOptions.length; ++i) {
                if (this.tradingOptions[i] == null) continue;
                tradingOptionArray[n2++] = this.tradingOptions[i];
            }
            this.tradingOptions = tradingOptionArray;
        }
    }

    public boolean wasUsed() {
        return this.wasUsed;
    }

    public void checkBadStrategy() throws BadStrategyException, TradingException {
        OrdersList ordersList;
        boolean bl;
        if (this.strategyCheckDate < 0L) {
            this.strategyCheckDate = this.tradingSetup.getStrategyCheckDate();
        }
        if (this.strategyCheckDate <= 0L) {
            return;
        }
        boolean bl2 = bl = this.MarketData.TimeCurrent() > this.strategyCheckDate;
        if (!bl && this.badStrategyChecks % 10 == 0) {
            ++this.badStrategyChecks;
            ordersList = this.Trader.getHistoryOrders();
            if (ordersList != null && ordersList.size() > 200) {
                bl = true;
            }
        }
        if (bl) {
            ordersList = this.Trader.getHistoryOrders();
            this.ambigouousTrades = this.Trader.getAmbiguousTrades();
            if (ordersList != null) {
                this.strategyCheckDate = 0L;
                if (this.checkBadHistoryTrades(ordersList, this.ambigouousTrades)) {
                    return;
                }
            }
            int n = (int)((double)this.MarketData.Chart(0).Bars() * 0.2);
            for (int i = 0; i < this.Trader.getOpenOrdersCount(false); ++i) {
                ILiveOrder iLiveOrder = this.Trader.getOpenOrder(i, false);
                if (!iLiveOrder.isSuccessful() || iLiveOrder.isPendingOrder() || iLiveOrder.getBarsInTrade() <= n) continue;
                this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 64);
            }
        }
    }

    private boolean checkBadHistoryTrades(OrdersList ordersList, int n) throws BadStrategyException, TradingException {
        int n2;
        int n3;
        if (ordersList.size() == 0 && (n3 = BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 1)) == 1) {
            this.strategyProblems |= n3;
            return true;
        }
        if (ordersList.size() < 20 && (n3 = BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 2)) == 2) {
            this.strategyProblems |= n3;
            return true;
        }
        int n4 = 0;
        int n5 = 0;
        int n6 = 0;
        int n7 = 0;
        int n8 = 0;
        for (n2 = 0; n2 < ordersList.size(); ++n2) {
            long l;
            Order order = ordersList.get(n2);
            if (!order.isFilledOrder()) continue;
            ++n5;
            if (order.CloseType == 18) continue;
            ++n4;
            if (order.PL == 0.0f) {
                ++n6;
            }
            if ((l = order.CloseTime - order.OpenTime) == 0L && order.OpenPrice == order.ClosePrice) {
                ++n7;
            }
            if (order.BarsInTrade != 0) continue;
            ++n8;
        }
        if ((double)n4 < (double)n5 * 0.1) {
            this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 256);
        }
        if ((n2 = n4 / 10) > 100) {
            n2 = 100;
        }
        if (n6 > n2) {
            this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 4);
        }
        if (n7 > n2) {
            this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 16);
        }
        if (n8 > n2) {
            this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 8);
        }
        if ((n2 = n4 / 20) > 50) {
            n2 = 50;
        }
        if (n > n2) {
            this.strategyProblems |= BadStrategyException.setOrThrow(this.dismissBadStrategies, this.warningsBadStrategies, 1024);
        }
        return true;
    }

    public static void init() throws Exception {
        if (strategyModifier != null) {
            throw new Exception("StrategyBase.init() called more than once!");
        }
        CustomClassesLoader customClassesLoader = new CustomClassesLoader("Internal");
        while (customClassesLoader.hasNext()) {
            Object object;
            String string = customClassesLoader.getNext();
            if (!string.equals("SQ.Internal.XmlStrategyModifier") || !((object = customClassesLoader.createInstance(string)) instanceof IStrategyModifier)) continue;
            strategyModifier = (IStrategyModifier)object;
        }
        if (strategyModifier == null) {
            throw new Exception("Loading of StrategyModifier class was unsuccessful in StrategyBase.init()!");
        }
    }

    public static void reload() throws Exception {
        strategyModifier = null;
        StrategyBase.init();
    }

    public void transformToVariables(boolean bl) throws Exception {
        this.transformToVariables(bl, null);
    }

    public void transformToVariables(boolean bl, ValuesMap valuesMap) throws Exception {
        throw new Exception("Not implemented in StrategyBase!");
    }

    public void transformToNumbers() throws Exception {
        throw new Exception("Not implemented in StrategyBase!");
    }

    public static StrategyBase createXmlStrategy(Element element) throws Exception {
        return StrategyBase.createXmlStrategy(element, null);
    }

    public static StrategyBase createXmlStrategy(Element element, String string) throws Exception {
        if (strategyModifier == null) {
            throw new Exception("StrategyBase->strategyModifier uninitialized! You have to call StrategyBase.init() during program startup!");
        }
        return strategyModifier.createStrategyFromXml(element, string);
    }

    public static StrategyParamData createStrategyVariation(StrategyBase strategyBase, OptimizationSettings optimizationSettings, short[] sArray) throws Exception {
        if (strategyModifier == null) {
            throw new Exception("StrategyBase->strategyModifier uninitialized! You have to call StrategyBase.init() during program startup!");
        }
        return strategyModifier.createStrategyVariation(strategyBase, optimizationSettings, sArray);
    }

    public boolean isSymmetryEnabled() {
        return false;
    }

    protected void evaluateBeforeActionListeners() throws TradingException {
        if (this.Trader != null) {
            this.Trader.evaluateActionListeners(this.UpdateEventType, this);
        }
    }

    public static IndicatorsObj createIndicatorsObj(int n) throws Exception {
        if (strategyModifier == null) {
            throw new Exception("StrategyBase->strategyModifier uninitialized! You have to call StrategyBase.init() during program startup!");
        }
        String string = "<StrategyFile><Strategy><Variables/></Strategy></StrategyFile>";
        StrategyBase strategyBase = StrategyBase.createXmlStrategy(XMLUtil.stringToElement((String)string));
        strategyBase.setEngine(n);
        return strategyModifier.createIndicatorsObject(strategyBase);
    }

    public int getStrategyProblems() {
        return this.strategyProblems;
    }

    public void setStrategyProblem(int n) {
        this.strategyProblems |= n;
    }

    public void updateJobProgress() throws TradingException {
        if (this.updateProgressTicks < 100) {
            ++this.updateProgressTicks;
            return;
        }
        this.updateProgressTicks = 0;
        long l = 500L;
        long l2 = System.currentTimeMillis();
        if (this.progressUpdateTime < 0L) {
            this.progressUpdateTime = l2 + l;
            ChartDef chartDef = this.tradingSetup.getChartSetup().getCharts().get(0);
            this.progressTotalHistoryFrom = chartDef.getHistoryFrom();
            this.progressTotalHistoryTo = chartDef.getHistoryTo();
            this.progressDiff = this.progressTotalHistoryTo - this.progressTotalHistoryFrom;
            this.progressLastBarChecked = this.MarketData.Chart(0).Bars();
            return;
        }
        if (this.MarketData.Chart(0).Bars() > this.progressLastBarChecked && l2 >= this.progressUpdateTime) {
            long l3 = this.MarketData.TimeCurrent();
            double d = (double)(l3 -= this.progressTotalHistoryFrom) / this.progressDiff * 100.0;
            this.tradingSetup.notifyAboutProgress((int)d);
            this.progressUpdateTime = l2 + l;
        }
    }

    public MoneyManagementMethod getGlobalMMMethod() {
        return this.globalMMMethod;
    }

    public void setGlobalMMMethod(MoneyManagementMethod moneyManagementMethod) {
        this.globalMMMethod = moneyManagementMethod;
    }

    public boolean hasOnTickRule() {
        return true;
    }

    public boolean hasDailyDataBlock() {
        return true;
    }

    public boolean hasWeeklyDataBlock() {
        return true;
    }

    public boolean hasMonthlyDataBlock() {
        return true;
    }

    public static StrategyBase getStrategy(SettingsMap settingsMap) throws TradingException {
        if (settingsMap.containsKey("StrategyObject")) {
            if (!(settingsMap.get("StrategyObject") instanceof StrategyBase)) {
                throw new TradingException("Setting 'TradingSetup.StrategyObject was set, but it has incorrect value! It must be an instance of StrategyBase object.");
            }
            return (StrategyBase)settingsMap.get("StrategyObject");
        }
        if (settingsMap.containsKey("StrategyClass")) {
            if (!(settingsMap.get("StrategyClass") instanceof String)) {
                throw new TradingException("Setting 'TradingSetup.StrategyClass was set, but it has incorrect value! It must be a string with name of existing strategy.");
            }
            String string = (String)settingsMap.get("StrategyClass");
            try {
                return StrategiesList.create(string);
            }
            catch (NonexistingCustomClassException nonexistingCustomClassException) {
                throw new TradingException("Cannot create an instance of '" + string + "' class.");
            }
        }
        throw new TradingException("Setting 'TradingSetup.StrategyClass' is not set.");
    }

    public boolean getApplyExitsAtTheEndOfRule() {
        return this.applyExitsAtTheEndOfRule;
    }

    protected void setEngine(int n) {
        this.engine = n;
    }

    public int getEngine() {
        return this.engine;
    }

    public boolean isEngineDefined() {
        return this.engine != 0;
    }

    public boolean isTradestationEngine() {
        return this.engine == 56756755 || this.engine == 938213070;
    }

    public void callExitEOD(TickEvent tickEvent) throws Exception {
        if (!Engines.isTradestationEngine(this.engine)) {
            return;
        }
        if (this.firstCallEvaluateOptions) {
            this.firstCallEvaluateOptions = false;
            this.initOptions();
        }
        if (this.endOfdayExit == null) {
            return;
        }
        this.endOfdayExit.OnTick(this, tickEvent, false);
    }

    public void customBlocksMapAdd(Element element) {
        String string = element.getAttributeValue("key");
        if (this.cbMap == null) {
            this.cbMap = new HashMap();
        }
        this.cbMap.put(string, element);
    }

    public Element customBlocksMapGet(String string) {
        if (this.cbMap == null) {
            return null;
        }
        return this.cbMap.get(string);
    }

    public void addBlocksToXML(Element element) {
        StrategyGenerator.addBlocksToXML(element, this.cbMap);
    }

    public void setATM(ATM aTM) throws Exception {
        int n = aTM.getType();
        if (n == 0) {
            this.atm = null;
            this.updateStrategyXML(ATM.setSourceAndEnable(this.getStrategyXml(), null, false));
        } else if (n == 2) {
            this.atm = aTM;
            this.updateStrategyXML(ATM.setConfigATMToStrategy(aTM, this.getStrategyXml(), true));
        } else {
            this.atm = ATM.createFromStrategy(this.getStrategyXml());
            this.updateStrategyXML(ATM.setSourceAndEnable(this.getStrategyXml(), "strategy", this.atm != null && this.atm.isUsed()));
        }
    }

    public ATM getATM() {
        return this.atm;
    }

    public abstract double getATRValue(ChartData var1, int var2, int var3) throws TradingException;

    public double getInitialBalance() {
        return this.initialCapital != -999999.0 ? this.initialCapital : (Double)this.settings.get("MoneyManagement.InitialCapital");
    }

    public double getAccountBalance() {
        return this.accountBalance != -999999.0 ? this.accountBalance : this.Trader.getAccountBalance();
    }

    public double getAccountEquity() {
        return this.accountEquity != -999999.0 ? this.accountEquity : this.Trader.getAccountEquity();
    }

    public boolean isStockpicker() {
        return this.Stockpicker != null;
    }

    public void evaluateEntryExit(byte by) throws Exception {
    }

    public StockpickerOptions getStockpickerOptions() {
        StockpickerOptions stockpickerOptions = null;
        if (this.tradingOptions != null) {
            for (int i = 0; i < this.tradingOptions.length; ++i) {
                TradingOption tradingOption = this.tradingOptions[i];
                if (!tradingOption.getClass().getSimpleName().equals("StockpickerOptions")) continue;
                stockpickerOptions = (StockpickerOptions)tradingOption;
                break;
            }
        }
        return stockpickerOptions;
    }

    public int getAmbiguousTrades() {
        return this.ambigouousTrades;
    }

    public TradingOption[] getTradingOptions() {
        return this.tradingOptions;
    }

    public SettingsMap getSpecialValues() {
        return this.specialValues;
    }
}

