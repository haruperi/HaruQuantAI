/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.backtester;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.BacktestData;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktestJobResult;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.log.StockpickerLog;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.signals.Signals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignal;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Comparator;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioBacktestJob {
    public static final Logger Log = LoggerFactory.getLogger(PortfolioBacktestJob.class);
    private final Element elStrategy;
    private final String uniqueId;
    private final int maxEntrySignalsLong;
    private final int maxEntrySignalsShort;
    private StopPauseEngine stopPauseEngine;
    private ILastEventListener lastEventListener;
    private StrategyBase strategy;
    private String symbol;
    private BacktestData data;
    private long dateFrom;
    private long dateTo;
    private StockDto si;
    private final Comparator<PickerEntrySignal> entrySignalComparatorByScore;
    private StockpickerLog pickerLog;

    public PortfolioBacktestJob(String string, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener, StrategyBase strategyBase, BacktestData backtestData, Element element, String string2, long l, long l2, StockDto stockDto, int n, int n2, Comparator<PickerEntrySignal> comparator, StockpickerLog stockpickerLog) {
        this.symbol = string;
        this.stopPauseEngine = stopPauseEngine;
        this.lastEventListener = iLastEventListener;
        this.strategy = strategyBase;
        this.data = backtestData;
        this.elStrategy = element;
        this.uniqueId = string2;
        this.dateFrom = l;
        this.dateTo = l2;
        this.si = stockDto;
        this.maxEntrySignalsLong = n;
        this.maxEntrySignalsShort = n2;
        this.entrySignalComparatorByScore = comparator;
        this.pickerLog = stockpickerLog;
    }

    public PortfolioBacktestJobResult call() throws Exception {
        try {
            long l = this.dateFrom;
            long l2 = this.dateTo;
            this.lastEventListener.setLastEvent(L.t((String)"Collecting trading signals for symbol '%s'", (Object[])new Object[]{this.symbol}));
            this.data.init(this.symbol);
            this.strategy.Stockpicker.setData(this.data);
            LoadedStockGroupData loadedStockGroupData = this.data.getStockGroupData();
            LoadedSymbolData loadedSymbolData = loadedStockGroupData.getSymbolData(this.symbol);
            long l3 = this.data.getPickerData().timeline.indexToTimeD(loadedSymbolData.getRealDataIndexStartD());
            long l4 = this.data.getPickerData().timeline.indexToTimeD(loadedSymbolData.getRealDataIndexEndD());
            if (l3 > l) {
                l = l3;
            }
            if (l4 < l2) {
                l2 = l4;
            }
            long l5 = this.si.getDateFrom();
            long l6 = this.si.getDateTo();
            boolean bl = false;
            if (l5 != -1L && l5 > l2) {
                Log.debug(String.format("Backtest SKIPPED!!! Symbol '%s' was listed %s later than backtest period %s - %s.", this.symbol, SQTime.toDateString((long)l5), SQTime.toDateString((long)this.dateFrom), SQTime.toDateString((long)this.dateTo)));
                if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
                    this.pickerLog.print(String.format("Backtest SKIPPED!!! Symbol '%s' was listed %s later than backtest period %s - %s.", this.symbol, SQTime.toDateString((long)l5), SQTime.toDateString((long)l), SQTime.toDateString((long)this.dateTo)));
                }
                return null;
            }
            if (l6 != -1L && l6 < l) {
                Log.debug(String.format("Backtest SKIPPED!!! Symbol '%s' was delisted %s before backtest period %s - %s.", this.symbol, SQTime.toDateString((long)l6), SQTime.toDateString((long)this.dateFrom), SQTime.toDateString((long)this.dateTo)));
                if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
                    this.pickerLog.print(String.format("Backtest SKIPPED!!! Symbol '%s' was delisted %s before backtest period %s - %s.", this.symbol, SQTime.toDateString((long)l6), SQTime.toDateString((long)this.dateFrom), SQTime.toDateString((long)this.dateTo)));
                }
                return null;
            }
            if (l5 != -1L && l5 > l) {
                l = l5;
            }
            if (l6 != -1L && l6 < l2) {
                l2 = SQTime.addDays((long)l6, (int)1);
                bl = true;
            }
            if (l > l2) {
                Log.debug(String.format("Backtest SKIPPED!!! Symbol '%s' has invalid date range %s - %s, start date must be smaller than end date.", this.symbol, SQTime.toDateString((long)l), SQTime.toDateString((long)l2)));
                if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
                    this.pickerLog.print(String.format("Backtest SKIPPED!!! Symbol '%s' has invalid date range %s - %s, start date must be smaller than end date.", this.symbol, SQTime.toDateString((long)l), SQTime.toDateString((long)l2)));
                }
                return null;
            }
            l = SQTime.getDateInMs((long)l);
            l2 = SQTime.getDateInMs((long)l2);
            Log.debug(String.format("Backtesting symbol %s from %s to %s...", this.symbol, SQTime.toDateString((long)l), SQTime.toDateString((long)l2)));
            if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
                this.pickerLog.print(String.format("Backtesting symbol %s from %s to %s...", this.symbol, SQTime.toDateString((long)l), SQTime.toDateString((long)l2)));
            }
            int n = this.data.getPickerData().timeline.searchIndexByTimeD(l, true);
            int n2 = this.data.getPickerData().timeline.searchIndexByTimeD(l2, false);
            int n3 = 0;
            for (int i = n; i <= n2; ++i) {
                if (!loadedSymbolData.dataExistsD(i)) continue;
                if (this.checkStopped()) {
                    throw new TaskStoppedException();
                }
                boolean bl2 = i == n2;
                ++n3;
                this.evaluateBar(i, bl2, bl);
            }
            return new PortfolioBacktestJobResult(this.symbol, n3);
        }
        catch (TaskStoppedException taskStoppedException) {
            throw taskStoppedException;
        }
        catch (Exception exception) {
            this.saveBacktestError(exception);
            Log.error("Error while running backtest for symbol " + this.symbol, (Throwable)exception);
            if (this.pickerLog.storeLogs() && Stockpicker.isDebugModeEnabled()) {
                this.pickerLog.print("Error while running backtest for symbol " + this.symbol + " - " + exception.getMessage());
            }
            if (exception.getMessage().contains("because \"this.Indicators\" is null")) {
                throw new Exception(L.t((String)"Error while running backtest for symbol %s - %s - Most probably indicator used outside TA-Lib library.", (Object[])new Object[]{this.symbol, exception.getMessage()}));
            }
            throw new Exception(L.t((String)"Error while running backtest for symbol %s - %s", (Object[])new Object[]{this.symbol, exception.getMessage()}));
        }
    }

    private void evaluateBar(int n, boolean bl, boolean bl2) throws Exception {
        this.data.setCurrentBar(n);
        try {
            if (bl && bl2) {
                this.data.Signals(this.data.getTime(0), true).addExitSignal(new PickerExitSignal(this.symbol, 0, 60));
                return;
            }
            this.strategy.evaluateEntryExit((byte)15);
            this.strategy.evaluateEntryExit((byte)5);
            this.strategy.evaluateEntryExit((byte)10);
            if (bl) {
                this.data.Signals(this.data.getTime(0), true).addExitSignal(new PickerExitSignal(this.symbol, 0, 4));
            }
        }
        catch (Exception exception) {
            if (exception instanceof TradingException && ((TradingException)exception).getErrorCode() == 55) {
                if (Log.isDebugEnabled()) {
                    String string = SQTime.toDateString((long)this.strategy.Stockpicker.TimeCurrent());
                    Log.debug(String.format("SKIPPED evaluating entry/exit signals on bar %s for symbol %s - %s.", string, this.symbol, exception.getMessage()), (Throwable)exception);
                }
            }
            String string = SQTime.toDateString((long)this.strategy.Stockpicker.TimeCurrent());
            Log.info(String.format("Failed to evaluate entry/exit signals on bar %s for symbol %s - %s.", string, this.symbol, exception.getMessage()), (Throwable)exception);
            throw new Exception(L.t((String)"Failed to evaluate entry/exit signals on bar %s for symbol %s - %s.", (Object[])new Object[]{string, this.symbol, exception.getMessage()}), exception);
        }
        Signals signals = this.data.Signals(this.data.getTime(0), false);
        if (signals != null) {
            signals.consolidateEntryExitSignals(this.maxEntrySignalsLong, this.maxEntrySignalsShort, this.entrySignalComparatorByScore);
        }
        if ((signals = this.data.Signals(this.data.getTime(-1), false)) != null) {
            signals.consolidateEntryExitSignals(this.maxEntrySignalsLong, this.maxEntrySignalsShort, this.entrySignalComparatorByScore);
        }
    }

    private boolean checkStopped() {
        return this.stopPauseEngine.isStopped();
    }

    private void saveBacktestError(Exception exception) {
        if (MainApp.isRelease()) {
            return;
        }
        if (this.elStrategy == null) {
            return;
        }
        String string = MainApp.getDataPath() + "/tests/stockpickergen/" + this.uniqueId + ".sqx";
        File file = new File(string);
        if (file.exists()) {
            string = MainApp.getDataPath() + "/tests/stockpickergen/" + this.uniqueId + ".sqx.sqx";
        }
        if ((file = new File(string)).exists()) {
            return;
        }
        try {
            String string2 = XMLUtil.xmlToString((Element)this.elStrategy);
            ZipOutputStream zipOutputStream = new ZipOutputStream(new FileOutputStream(file));
            ZipEntry zipEntry = new ZipEntry("strategy_Portfolio.xml");
            zipOutputStream.putNextEntry(zipEntry);
            byte[] byArray = string2.getBytes();
            zipOutputStream.write(byArray, 0, byArray.length);
            zipOutputStream.closeEntry();
            zipOutputStream.close();
        }
        catch (IOException iOException) {
            iOException.printStackTrace();
        }
        SQUtils.stringToFile((File)new File(string + ".txt"), (String)SQUtils.getStackTrace((Throwable)exception));
    }
}

