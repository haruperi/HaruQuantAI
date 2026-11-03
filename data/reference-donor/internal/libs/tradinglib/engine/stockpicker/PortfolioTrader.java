/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.TradeSizeSmallerThanOneException;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.StockBroker;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.log.StockpickerLog;
import com.strategyquant.tradinglib.engine.stockpicker.constants.PickerTriggerTypes;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.signals.Signals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignals;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioTrader {
    public static final Logger Log = LoggerFactory.getLogger(StockpickerBacktestEngine.class);
    public StockBroker broker;
    private int maxPosLong = 0;
    private int maxPosShort = 0;
    private TickEvent tick = new TickEvent();
    private MoneyManagementMethod mmMethod = null;
    private boolean mmMethodInitialized = false;
    private Trader tradeController = null;
    IBacktestProgressListener backtestProgressListener;
    private StockpickerLog pickerLog;

    public PortfolioTrader(Trader trader, StockpickerLog stockpickerLog) {
        this.tradeController = trader;
        this.pickerLog = stockpickerLog;
        this.broker = new StockBroker(trader, stockpickerLog);
    }

    public void setMaxOpenPos(int n, int n2) {
        this.maxPosLong = n;
        this.maxPosShort = n2;
    }

    private boolean checkMaxOpenPositions(int n) {
        if (n == 1) {
            return this.broker.openPosCount(n) < this.maxPosLong;
        }
        return this.broker.openPosCount(n) < this.maxPosShort;
    }

    public String printOpenTrades(boolean bl) {
        return this.broker.printOpenTrades(bl);
    }

    public void printOpenTrades(StringBuilder stringBuilder, boolean bl) {
        this.broker.printOpenTrades(stringBuilder, bl);
    }

    public int openPosCount(boolean bl) {
        return this.broker.openPosCount(bl);
    }

    public void onStart(double d, double d2, CommissionsMethod commissionsMethod, SwapMethod swapMethod, double d3, boolean bl) {
        this.broker.onStart(d, d2, commissionsMethod, swapMethod, d3, bl);
    }

    public void onClose() {
        this.broker.onClose();
    }

    public OrdersList getHistoryOrders() {
        return this.broker.getHistoryOrders();
    }

    public double getAccountBalance() {
        return this.broker.getAccountBalance();
    }

    public double getAccountEquity() {
        return this.broker.getAccountEquity();
    }

    public ObjectArrayList<String> getTradedSymbols() {
        return this.broker.getTradedSymbols();
    }

    public void onBar(long l, int n, LoadedPickerData loadedPickerData, Signals signals) throws Exception {
        try {
            IntOpenHashSet intOpenHashSet;
            byte by;
            byte by2;
            block13: {
                block12: {
                    block11: {
                        block10: {
                            this.broker.resetStats();
                            StrategyBase strategyBase = this.tradeController.getStrategy();
                            by2 = strategyBase.Stockpicker.entryType;
                            by = strategyBase.Stockpicker.exitType;
                            PickerTriggerTypes pickerTriggerTypes = new PickerTriggerTypes();
                            intOpenHashSet = new IntOpenHashSet();
                            this.onTick(loadedPickerData, l, n, by2, by, StockBroker.TickBeforeBarOpen);
                            if (by == 15) break block10;
                            if (by != 5) break block11;
                        }
                        this.evalExiSignals(loadedPickerData, l, n, signals, true, by2, by, intOpenHashSet);
                    }
                    if (by2 == 15) break block12;
                    if (by2 != 5) break block13;
                }
                this.evalEntrySignals(loadedPickerData, l, n, signals, true, intOpenHashSet);
            }
            this.onTick(loadedPickerData, l, n, by2, by, StockBroker.TickOnBarOpen);
            if (by == 10) {
                this.evalExiSignals(loadedPickerData, l, n, signals, false, by2, by, intOpenHashSet);
            }
            if (by2 == 10) {
                this.evalEntrySignals(loadedPickerData, l, n, signals, false, intOpenHashSet);
            }
            this.onTick(loadedPickerData, l, n, by2, by, StockBroker.TickOnBarClose);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Error on bar %s - %s", (Object[])new Object[]{SQTime.toDateString((long)l), exception.getMessage()}), exception);
        }
    }

    private void evalExiSignals(LoadedPickerData loadedPickerData, long l, int n, Signals signals, boolean bl, byte by, byte by2, IntOpenHashSet intOpenHashSet) {
        if (signals == null || !signals.exitSignalExists()) {
            return;
        }
        PickerExitSignals pickerExitSignals = signals.getExitSignals();
        for (int i = 0; i < pickerExitSignals.size(); ++i) {
            PickerExitSignal pickerExitSignal = (PickerExitSignal)pickerExitSignals.get(i);
            LoadedSymbolData loadedSymbolData = loadedPickerData.stockGroupData.getSymbolData(pickerExitSignal.symbol);
            if (loadedSymbolData == null) {
                if (!Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Missing %s data ...", pickerExitSignal.symbol));
                continue;
            }
            if (pickerExitSignal.closeType == 4 && by == by2) {
                intOpenHashSet.add(pickerExitSignal.symbol.hashCode());
            }
            this.closeOrder(pickerExitSignal.symbol, pickerExitSignal.direction, pickerExitSignal.closeType, l, n, bl, loadedSymbolData);
        }
    }

    private void evalEntrySignals(LoadedPickerData loadedPickerData, long l, int n, Signals signals, boolean bl, IntOpenHashSet intOpenHashSet) throws Exception {
        if (signals == null) {
            return;
        }
        PickerEntrySignals pickerEntrySignals = signals.getLongEntrySignals();
        PickerEntrySignals pickerEntrySignals2 = signals.getShortEntrySignals();
        if (pickerEntrySignals != null) {
            this.evalEntrySignals(loadedPickerData, l, n, bl, pickerEntrySignals.list(), pickerEntrySignals2 == null ? null : pickerEntrySignals2.list(), intOpenHashSet);
        }
        if (pickerEntrySignals2 != null) {
            this.evalEntrySignals(loadedPickerData, l, n, bl, pickerEntrySignals2.list(), pickerEntrySignals == null ? null : pickerEntrySignals.list(), intOpenHashSet);
        }
    }

    private void evalEntrySignals(LoadedPickerData loadedPickerData, long l, int n, boolean bl, ObjectArrayList<PickerEntrySignal> objectArrayList, ObjectArrayList<PickerEntrySignal> objectArrayList2, IntOpenHashSet intOpenHashSet) throws Exception {
        for (int i = 0; i < objectArrayList.size(); ++i) {
            double d;
            PickerEntrySignal pickerEntrySignal = (PickerEntrySignal)objectArrayList.get(i);
            String string = pickerEntrySignal.symbol;
            byte by = pickerEntrySignal.getDirection();
            int n2 = by == 1 ? this.maxPosLong : this.maxPosShort;
            if (intOpenHashSet.contains(pickerEntrySignal.symbol.hashCode())) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format("Exit signal 'End Test', do not open a new position for symbol %s.", string));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Exit signal 'End Test', do not open a new position for symbol %s.", string));
                continue;
            }
            if (!this.checkMaxOpenPositions(pickerEntrySignal.getDirection())) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format(String.format("Maximum number of open trades (orders/positions) for %s is reached %d.", Directions.typeToString(by), n2), new Object[0]));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) break;
                Log.debug(String.format("Maximum number of open trades (orders/positions) for %s is reached %d.", Directions.typeToString(by), n2));
                break;
            }
            if (!this.checkOppositeSignals(string, objectArrayList2)) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format("%s Signal for symbol %s skipped - Strategy generated two opposite signals.", Directions.typeToString(by), string));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug("%s Signal for symbol %s skipped - Strategy generated two opposite signals.", (Object)Directions.typeToString(by), (Object)string);
                continue;
            }
            if (this.checkOpenPositionsExists(string)) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format("Order with symbol %s already exists, cannot open another one. Only one trade (order/position) per symbol is allowed.", string));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug("Order with symbol %s already exists, cannot open another one. Only one trade (order/position) per symbol is allowed.", (Object)string);
                continue;
            }
            if (!this.checkOpenSlot(string, bl)) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format("Order with symbol %s was closed on SL/PT during the day, cannot open a new position on Open.", string));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug("Order with symbol %s was closed on SL/PT during the day, cannot open a new position on Open.", (Object)string);
                continue;
            }
            LoadedSymbolData loadedSymbolData = loadedPickerData.stockGroupData.getSymbolData(string);
            if (loadedSymbolData == null) {
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Missing %s data ...", string));
                continue;
            }
            try {
                d = this.computeTradeSize(string, this.broker.getAccountBalance(), pickerEntrySignal);
            }
            catch (TradeSizeSmallerThanOneException tradeSizeSmallerThanOneException) {
                if (this.pickerLog.storeLogs()) {
                    this.pickerLog.print(String.format("Not enough money to open position %s - %s", string, tradeSizeSmallerThanOneException.getMessage()));
                }
                if (!this.pickerLog.storeLogs() || !Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Not enough money to open position %s - %s", string, tradeSizeSmallerThanOneException.getMessage()));
                continue;
            }
            this.submitOrder(pickerEntrySignal.type, string, d, pickerEntrySignal.price, pickerEntrySignal.sl, pickerEntrySignal.pt, pickerEntrySignal.slptValidFrom, pickerEntrySignal.barsValid, pickerEntrySignal.exitAfterBars, pickerEntrySignal.eod, l, n, bl, loadedSymbolData);
        }
    }

    private boolean checkOpenSlot(String string, boolean bl) {
        if (bl) {
            ObjectArrayList<LiveOrderObj> objectArrayList = this.broker.statsClosedPositions;
            for (int i = 0; i < objectArrayList.size(); ++i) {
                byte by;
                LiveOrderObj liveOrderObj = (LiveOrderObj)objectArrayList.get(i);
                if (!liveOrderObj.getSymbol().equals(string) || (by = liveOrderObj.getCloseType()) != 2 && by != 3) continue;
                return false;
            }
        }
        return true;
    }

    private boolean checkOppositeSignals(String string, ObjectArrayList<PickerEntrySignal> objectArrayList) {
        if (objectArrayList != null) {
            for (int i = 0; i < objectArrayList.size(); ++i) {
                if (!((PickerEntrySignal)objectArrayList.get((int)i)).symbol.equals(string)) continue;
                return false;
            }
        }
        return true;
    }

    private void onTick(LoadedPickerData loadedPickerData, long l, int n, byte by, byte by2, int n2) throws TradingException {
        if (n2 != StockBroker.TickBeforeBarOpen && n2 != StockBroker.TickOnBarOpen && n2 != StockBroker.TickOnBarClose) {
            throw new TradingException("Stockpicker.onTick(), invalid onTick sequence " + n2);
        }
        boolean bl = n2 == StockBroker.TickBeforeBarOpen || n2 == StockBroker.TickOnBarOpen;
        boolean bl2 = n2 == StockBroker.TickOnBarClose;
        ObjectArrayList<LiveOrderObj> objectArrayList = this.broker.getOpenPositions();
        int n3 = objectArrayList.size();
        for (int i = n3 - 1; i >= 0; --i) {
            boolean bl3;
            double d;
            LiveOrderObj liveOrderObj = (LiveOrderObj)objectArrayList.get(i);
            String string = liveOrderObj.getSymbol();
            LoadedSymbolData loadedSymbolData = loadedPickerData.stockGroupData.getSymbolData(string);
            if (loadedSymbolData == null) {
                if (!Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Missing %s data ...", string));
                continue;
            }
            double d2 = d = bl ? (double)loadedSymbolData.OpenD(n) : (double)loadedSymbolData.CloseD(n);
            if (d == 0.0) {
                if (!Stockpicker.isDebugModeEnabled()) continue;
                Log.debug(String.format("Missing %s data on bar %s...gap or end of data ?!", string, SQTime.toDateString((long)l)));
                continue;
            }
            double d3 = loadedSymbolData.CloseD(n - 1);
            double d4 = -1.0;
            double d5 = -1.0;
            if (n2 == StockBroker.TickBeforeBarOpen) {
                d5 = loadedSymbolData.OpenD(n);
                d4 = loadedSymbolData.OpenD(n);
            } else if (n2 == StockBroker.TickOnBarOpen) {
                d5 = loadedSymbolData.HighD(n);
                d4 = loadedSymbolData.LowD(n);
            } else if (n2 == StockBroker.TickOnBarClose) {
                if (by == 10 && l == liveOrderObj.getOriginalOpenTime()) {
                    d5 = loadedSymbolData.CloseD(n);
                    d4 = loadedSymbolData.CloseD(n);
                } else {
                    d5 = loadedSymbolData.HighD(n);
                    d4 = loadedSymbolData.LowD(n);
                }
            }
            d3 = -1.0;
            this.tick.set(l, 0, string.hashCode(), d, d, 0.0, 0L, 0L, bl, !bl);
            this.broker.onTick(this.tick, d3, d5, d4, by, by2, n2);
            boolean bl4 = bl3 = loadedSymbolData.getRealDataIndexEndD() == n;
            if (!bl2 || !bl3) continue;
            this.closeOrder(string, (byte)liveOrderObj.getDirection(), (byte)4, l, n, bl, loadedSymbolData);
        }
    }

    private double computeTradeSize(String string, double d, PickerEntrySignal pickerEntrySignal) throws Exception {
        SettingsMap settingsMap;
        StrategyBase strategyBase = this.tradeController.getStrategy();
        double d2 = 1.0;
        if (!this.mmMethodInitialized) {
            this.mmMethodInitialized = true;
            settingsMap = strategyBase.getSettings();
            if (settingsMap.getBoolean("MoneyManagement.UseFromStrategy", false)) {
                this.mmMethod = strategyBase.getGlobalMMMethod();
            }
            if (this.mmMethod == null) {
                this.mmMethod = (MoneyManagementMethod)settingsMap.get("MoneyManagement.Method");
            }
        }
        if (this.mmMethod != null) {
            settingsMap = DataManager.getDataInfo((String)"History", (String)string, (boolean)true);
            InstrumentInfo instrumentInfo = settingsMap.symbolInfo;
            strategyBase.accountBalance = this.broker.getAccountBalance();
            strategyBase.accountEquity = this.broker.getAccountEquity();
            double d3 = pickerEntrySignal.sl;
            if (d3 == -9.9999999E7) {
                d3 = 0.0;
            }
            int n = strategyBase.Stockpicker.getMaxOpenPositions();
            if (strategyBase.Stockpicker.isSingleAssetStrategy()) {
                n = 1;
            }
            this.mmMethod.setMaxOpenPositions(n);
            d2 = this.mmMethod.computeTradeSize(strategyBase, string, pickerEntrySignal.type, pickerEntrySignal.price, d3, instrumentInfo.tickSize, instrumentInfo.pointValue);
        }
        return d2;
    }

    private LiveOrderObj submitOrder(byte by, String string, double d, double d2, double d3, double d4, int n, int n2, int n3, byte by2, long l, int n4, boolean bl, LoadedSymbolData loadedSymbolData) throws TradingException {
        double d5;
        if (loadedSymbolData == null) {
            if (Stockpicker.isDebugModeEnabled()) {
                Log.debug(String.format("Missing %s data ...", string));
            }
            return null;
        }
        double d6 = d5 = bl ? (double)loadedSymbolData.OpenD(n4) : (double)loadedSymbolData.CloseD(n4);
        if (d5 == 0.0) {
            if (Stockpicker.isDebugModeEnabled()) {
                Log.debug(String.format("Missing %s data on bar %s...gap or end of data ?!", string, SQTime.toDateString((long)l)));
            }
            return null;
        }
        this.tick.set(l, 0, string.hashCode(), d5, d5, 0.0, 0L, 0L, bl, !bl);
        this.broker.setCurrentTick(this.tick);
        StrategyBase strategyBase = this.tradeController.getStrategy();
        return this.broker.open(by, string, d, d2, d3, d4, n, n2, n3, by2, bl, strategyBase.Stockpicker.entryType == 15);
    }

    public void closeOrder(String string, byte by, byte by2, long l, int n, boolean bl, LoadedSymbolData loadedSymbolData) {
        double d;
        if (loadedSymbolData == null) {
            if (Stockpicker.isDebugModeEnabled()) {
                Log.debug(String.format("Missing %s data ...", string));
            }
            return;
        }
        double d2 = d = bl ? (double)loadedSymbolData.OpenD(n) : (double)loadedSymbolData.CloseD(n);
        if (d == 0.0) {
            if (Stockpicker.isDebugModeEnabled()) {
                Log.debug(String.format("Missing %s data on bar %s...gap or end of data ?!", string, SQTime.toDateString((long)l)));
            }
            return;
        }
        this.tick.set(l, 0, string.hashCode(), d, d, 0.0, 0L, 0L, bl, !bl);
        this.broker.setCurrentTick(this.tick);
        this.broker.close(string, by, by2);
    }

    public boolean checkOpenPositionsExists(String string) {
        ObjectArrayList<LiveOrderObj> objectArrayList = this.broker.getOpenPositions();
        for (int i = 0; i < objectArrayList.size(); ++i) {
            LiveOrderObj liveOrderObj = (LiveOrderObj)objectArrayList.get(i);
            if (!liveOrderObj.getSymbol().equals(string)) continue;
            return true;
        }
        return false;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }

    public ObjectArrayList<LiveOrderObj> getOpenPositions() {
        return this.broker.getOpenPositions();
    }

    public Long2FloatRBTreeMap getWorstDailyEquity() {
        return this.broker.getWorstDailyEquity();
    }

    public Long2FloatRBTreeMap getMaxDailyDD() {
        return this.broker.getMaxDailyDDValues();
    }

    public Long2FloatRBTreeMap getMaxDailyDDPct() {
        return this.broker.getMaxDailyDDPctValues();
    }

    public double getMaxOpenDrawdown() {
        return this.broker.getMaxOpenDrawdown();
    }

    public double getMaxOpenDrawdownPct() {
        return this.broker.getMaxOpenDrawdownPct();
    }
}

