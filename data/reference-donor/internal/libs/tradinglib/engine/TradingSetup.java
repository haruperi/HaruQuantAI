/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.utils.SQUUID
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.utils.SQUUID;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.setup.TradingSetupRunnable;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingSetup {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradingSetup");
    protected SettingsMap settings;
    protected ChartSetup chartSetup;
    protected StrategyBase strategy;
    protected TradingSetupRunnable runnable = new TradingSetupRunnable(this, this.usePreparedData);
    protected TradingEngine tradingEngine;
    protected int tradingType = 0;
    private MarketData MarketData;
    private volatile boolean inInit = false;
    private int reservedBars = 50;
    private int status = 0;
    private final int setupId;
    private int numberOfStartingBars = 0;
    private String setupName;
    private int userDefinedStartingBar;
    private int engineId;
    private long strategyCheckDate = -1L;
    private int dismissBadStrategies = 0;
    private boolean warningsBadStrategies = false;
    private IBacktestProgressListener backtestProgressListener = null;
    private MarketData loadedMarketData;
    protected boolean usePreparedData = true;
    private double globalATR = -1.0;
    private int barEventType;
    protected int indyStartingBar = 0;

    TradingSetup(TradingEngine tradingEngine, int n, ChartSetup chartSetup, SettingsMap settingsMap, StrategyBase strategyBase) {
        this.settings = this.createDefaultSettingsMap(settingsMap);
        this.tradingEngine = tradingEngine;
        this.engineId = n;
        this.chartSetup = chartSetup;
        this.strategy = strategyBase;
        if (chartSetup != null) {
            chartSetup.setUsed();
        }
        strategyBase.setSettings(this.settings);
        String string = SQUUID.randomUUID();
        this.setupId = string.hashCode();
        if (strategyBase != null) {
            this.setupName = strategyBase.getStrategyName();
        }
        this.initInternalSettings();
    }

    protected void initInternalSettings() {
        this.userDefinedStartingBar = 0;
        if (this.settings != null) {
            this.userDefinedStartingBar = this.settings.getInt("StartingBar", 0);
            if (this.userDefinedStartingBar < 0) {
                this.userDefinedStartingBar = 0;
            }
            int n = this.settings.getInt("ReservedBars", 0);
            this.userDefinedStartingBar += this.engineId == 56756755 || this.engineId == 938213070 ? n : 0;
            this.indyStartingBar = this.userDefinedStartingBar;
        }
        if (this.settings.containsKey("StrategyCheckDate")) {
            this.strategyCheckDate = this.settings.getLong("StrategyCheckDate");
        }
        if (this.settings.containsKey("DismissBadStrategies")) {
            this.dismissBadStrategies = this.settings.getInt("DismissBadStrategies");
        } else if (this.settings.containsKey("StrategyDismissSettings")) {
            this.dismissBadStrategies = this.settings.getInt("StrategyDismissSettings");
        }
        if (this.settings.containsKey("StrategyDismissWarnings")) {
            this.warningsBadStrategies = this.settings.getBoolean("StrategyDismissWarnings");
        }
    }

    public String getName() {
        return this.setupName;
    }

    public void setName(String string) {
        this.setupName = string;
    }

    void setTradingType(int n) {
        this.tradingType = n;
    }

    public void initDefaultValues() {
    }

    private SettingsMap createDefaultSettingsMap(SettingsMap settingsMap) {
        if (settingsMap == null) {
            settingsMap = new SettingsMap();
        }
        settingsMap.setIfNotExists("BacktestPrecision", (Object)1);
        settingsMap.setIfNotExists("Slippage", (Object)0);
        settingsMap.setIfNotExists("MinDistance", (Object)0);
        settingsMap.setIfNotExists("MoneyManagement.InitialCapital", (Object)10000.0);
        return settingsMap;
    }

    public void start(boolean bl) throws Exception {
        if (this.usePreparedData) {
            this.MarketData = this.loadedMarketData.cloneToPrepared(this, this.chartSetup, this.indyStartingBar);
            if (this.strategy != null) {
                this.MarketData.setPerformanceParams(this.strategy.hasOnTickRule(), this.strategy.hasDailyDataBlock(), this.strategy.hasWeeklyDataBlock(), this.strategy.hasMonthlyDataBlock());
            }
        } else {
            this.MarketData = new MarketData(this, this.chartSetup, 0);
        }
        this.inInit = true;
        this.strategy.callOnInit(this);
        this.inInit = false;
        if (this.tradingType == 0) {
            this.runChecks();
            this.registerConnectionSymbols();
            Log.debug("Before loading history data, MarketData.getMainChartBars() = " + this.MarketData.Chart((int)0).Time.size());
            this.requestHistoryData(TradingEngine.getLiveEngine().getConnectionManager());
            Log.debug("After loading history data, MarketData.getMainChartBars() = " + this.MarketData.Chart((int)0).Time.size());
            this.numberOfStartingBars = this.MarketData.Chart((int)0).Time.size();
            if (this.numberOfStartingBars > 0 && Log.isDebugEnabled()) {
                Log.debug("Last bar time: {}", (Object)SQTime.toDateMinuteString((long)this.MarketData.Chart(0).Time(0)));
            }
        }
        this.status = 1;
        if (!bl) {
            // empty if block
        }
    }

    private void requestHistoryData(ConnectionManager connectionManager) throws Exception {
        this.MarketData.requestHistoryData(connectionManager, this.reservedBars);
    }

    private void registerConnectionSymbols() throws Exception {
        this.chartSetup.registerConnectionSymbols(this.tradingEngine.getConnectionManager());
    }

    public void stop() throws Exception {
        this.runnable.stopRunner();
        if (this.strategy != null) {
            this.strategy.Deinitialize();
            this.strategy.destroy();
        }
        this.status = 2;
    }

    public ChartSetup getChartSetup() {
        return this.chartSetup;
    }

    public TradingEngine getTradingEngine() {
        return this.tradingEngine;
    }

    public void runChecks() throws Exception {
        if (this.tradingEngine == null) {
            throw new TradingException("Canot call TradingSetup.runChecks() before initializing TradingSetup.tradingEngine !");
        }
        this.chartSetup.runChecks(this.tradingEngine.getConnectionManager());
    }

    public MarketData getMarketData() {
        return this.MarketData;
    }

    public boolean isInInit() {
        return this.inInit;
    }

    public boolean callStrategyOnBarUpdate(BarUpdateInfo barUpdateInfo, int n) throws Exception {
        if (!barUpdateInfo.updatedMainChart) {
            return true;
        }
        this.strategy.UpdatedChart = barUpdateInfo.updatedChart;
        this.strategy.MultipleChartsUpdated = barUpdateInfo.multipleChartsUpdated;
        this.strategy.UpdateEventType = n;
        this.strategy.updateTradeControllers();
        this.strategy.checkBadStrategy();
        this.strategy.updateJobProgress();
        boolean bl = false;
        if (this.chartSetup.getTestPrecision() == 5) {
            bl = n == 2;
        } else if (this.strategy.getEventType() == 4) {
            if (this.barEventType == 2) {
                if (n != 3) {
                    bl = true;
                }
            } else if (n == 3) {
                bl = true;
            }
        } else if (this.strategy.getEventType() == 6) {
            bl = true;
        } else if (this.strategy.getEventType() == n) {
            bl = true;
        }
        if (bl) {
            if (n == 3) {
                if (this.userDefinedStartingBar <= 0) {
                    // empty if block
                }
                this.reservedBars = 0;
                boolean bl2 = true;
                for (int i = 0; i < this.MarketData.getChartsCount(); ++i) {
                    ChartData chartData = this.MarketData.Chart(i);
                    if (chartData.Bars() > this.userDefinedStartingBar) continue;
                    bl2 = false;
                }
                if (bl2) {
                    ChartData chartData = this.MarketData.Chart(0);
                    this.strategy.OnBarUpdate();
                    if (this.globalATR < 0.0) {
                        this.globalATR = this.computeATR(chartData);
                    }
                    return true;
                }
            } else {
                ChartData chartData = this.MarketData.Chart(0);
                if (chartData.Bars() > this.reservedBars + this.userDefinedStartingBar) {
                    chartData.setCurrentBar(this.reservedBars, this.userDefinedStartingBar);
                    this.strategy.OnBarUpdate();
                    if (this.globalATR < 0.0) {
                        this.globalATR = this.computeATR(chartData);
                    }
                    return true;
                }
            }
        }
        return true;
    }

    public void callOptionsOnTick(TickEvent tickEvent) throws Exception {
        this.strategy.callOptionsOnTick(tickEvent);
    }

    public void callExitEOD(TickEvent tickEvent) throws Exception {
        this.strategy.callExitEOD(tickEvent);
    }

    public Exception getTradingException() {
        return this.runnable.getTradingException();
    }

    public boolean isRunning() {
        return this.runnable.isAlive();
    }

    public void setReservedBars(int n) {
        this.reservedBars = n;
    }

    public int getReservedBars() {
        return this.reservedBars;
    }

    public StrategyBase getStrategy() {
        return this.strategy;
    }

    public int getStatus() {
        return this.status;
    }

    public int getSetupId() {
        return this.setupId;
    }

    public int getStartingBars() {
        return this.numberOfStartingBars;
    }

    public HashMap<String, InstrumentInfo> getInstrumentsInfoMap() {
        HashMap<String, InstrumentInfo> hashMap = new HashMap<String, InstrumentInfo>();
        for (ChartDef chartDef : this.getChartSetup().getCharts()) {
            if (hashMap.containsKey(chartDef.getSymbol())) continue;
            hashMap.put(chartDef.getSymbol(), chartDef.getSymbolInfo());
        }
        return hashMap;
    }

    public SettingsMap getSettings() {
        return this.settings;
    }

    public void destroy() {
        if (this.MarketData != null) {
            this.MarketData.destroy();
        }
    }

    public int getEngineId() {
        return this.engineId;
    }

    public long getStrategyCheckDate() {
        return this.strategyCheckDate;
    }

    public int getDismissBadStrategies() {
        return this.dismissBadStrategies;
    }

    public boolean getWarningsBadStrategies() {
        return this.warningsBadStrategies;
    }

    public void setProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }

    public void notifyAboutProgress(int n) {
        if (this.backtestProgressListener != null) {
            this.backtestProgressListener.setProgress(n);
        }
    }

    public void setLoadedMarketData(MarketData marketData) {
        this.loadedMarketData = marketData;
    }

    public void setUsePreparedData(boolean bl) {
        this.usePreparedData = bl;
    }

    public double getGlobalATR() {
        return this.globalATR;
    }

    private double computeATR(ChartData chartData) throws TradingException {
        if (chartData.High.size() <= 20) {
            return 0.0;
        }
        double d = 0.0;
        for (int i = 0; i < 19; ++i) {
            d = this.computeATROnBar(i, d, chartData);
        }
        return d;
    }

    private double computeATROnBar(int n, double d, ChartData chartData) throws TradingException {
        int n2 = 14;
        int n3 = 18 - n;
        double d2 = chartData.High.get(n3) - chartData.Low.get(n3);
        if (n == 0) {
            return d2;
        }
        double d3 = chartData.Close.get(n3 + 1);
        d2 = Math.max(Math.abs(chartData.Low.get(n3) - d3), Math.max(d2, Math.abs(chartData.High.get(n3) - d3)));
        return ((double)(Math.min(n + 1, n2) - 1) * d + d2) / (double)Math.min(n + 1, n2);
    }

    public void setBarEventType(int n) {
        this.barEventType = n;
        this.runnable.setBarEventType(n);
    }

    public int getBarEventType() {
        return this.barEventType;
    }

    public int getIndyStartingBar() {
        return this.indyStartingBar;
    }
}

