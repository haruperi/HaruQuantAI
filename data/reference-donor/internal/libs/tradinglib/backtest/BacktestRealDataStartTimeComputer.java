/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.bartype.BarType
 *  com.strategyquant.datalib.bartype.BarTypeFactory
 *  com.strategyquant.datalib.bartype.BarTypeStatus
 *  com.strategyquant.datalib.bartype.impl.FuturesTimeBar
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.session.SessionStatus
 *  com.strategyquant.lib.IStopPauseStatus
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.bartype.impl.FuturesTimeBar;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.lib.IStopPauseStatus;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.StartDataInfo;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestRealDataStartTimeComputer {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestDataFeedEngine");
    private ChartDef chartDef;
    private ITradingSimulator tradingSimulator;
    private BarType barType;
    private final BarTypeStatus barTypeStatus = new BarTypeStatus();
    private int totalBars;
    private int minimumReservedBars;
    private int preferredReservedBars;
    public TimeDataSeries Time;

    public BacktestRealDataStartTimeComputer(int n, ChartDef chartDef, ITradingSimulator iTradingSimulator) {
        this.chartDef = chartDef;
        this.tradingSimulator = iTradingSimulator;
        ReservedBarsType reservedBarsType = iTradingSimulator.getReservedBarsType();
        this.minimumReservedBars = Math.max(reservedBarsType.minimumReservedBars, n);
        this.preferredReservedBars = reservedBarsType.preferredReservedBars;
        Log.debug("Reserved Bars Type: LOAD_BACK - minimum: " + this.minimumReservedBars + ", preferred: " + this.preferredReservedBars);
        this.Time = new TimeDataSeries();
    }

    public void computeRealDataStartTime(StartDataInfo startDataInfo, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        Session session = SessionManager.getSession((String)this.chartDef.getSession()).clone();
        ChartDef chartDef = new ChartDef(this.chartDef.getConnectionName(), this.chartDef.getSymbol(), this.chartDef.getTimeframe(), SQTime.toLong((int)1000, (int)1, (int)1), this.chartDef.getHistoryTo(), this.chartDef.getSpread(), this.chartDef.getSession());
        IDataLoader iDataLoader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, (IStopPauseStatus)(loadDataProgressEngine != null ? loadDataProgressEngine.getProgressEngine() : null));
        iDataLoader.open();
        this.goThroughBars(iDataLoader, session);
        iDataLoader.close();
        if (this.Time.size() == this.minimumReservedBars) {
            startDataInfo.realDataStartTime = this.Time.get(this.minimumReservedBars - 1);
            startDataInfo.realDataEndTime = this.Time.get(0);
            startDataInfo.reservedBars = this.minimumReservedBars;
        } else if (this.Time.size() < this.preferredReservedBars) {
            startDataInfo.realDataStartTime = this.Time.get(this.Time.size() - 1);
            startDataInfo.realDataEndTime = this.Time.get(1);
            startDataInfo.reservedBars = this.Time.size() - 1;
        } else {
            startDataInfo.realDataStartTime = this.Time.get(this.preferredReservedBars);
            startDataInfo.realDataEndTime = this.Time.get(1);
            startDataInfo.reservedBars = this.preferredReservedBars;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Unable to fully structure code
     */
    private void goThroughBars(IDataLoader var1_1, Session var2_2) throws Exception {
        var3_3 = this.tradingSimulator.getTickSimulator();
        var4_4 = new VersatileData();
        var5_5 = new TickEvent();
        var6_6 = new TickEvent();
        var7_7 = new ChartData(null, this.chartDef, 0, this.tradingSimulator.getEngineId());
        var8_8 = new SessionStatus();
        this.barType = BarTypeFactory.getBarType((String)this.chartDef.getTimeframe(), (int)this.chartDef.getBarTimeType()).clone();
        var9_9 = null;
        try {
            var9_9 = DataManager.getDataInfo((String)"History", (String)var7_7.Symbol).timeframe;
        }
        catch (Exception var10_10) {
            BacktestRealDataStartTimeComputer.Log.error("Cannot get original data timeframe");
        }
        if (this.barType instanceof FuturesTimeBar) {
            if (this.tradingSimulator.getEngineId() == -659455871 || this.tradingSimulator.getEngineId() == 395961824 || this.tradingSimulator.getEngineId() == 1441180233) {
                ((FuturesTimeBar)this.barType).MetaTraderEngineUsed = true;
            } else if (var9_9 != null && var9_9.equals(var7_7.Timeframe)) {
                ((FuturesTimeBar)this.barType).LoadAsIs = true;
            }
        }
        this.totalBars = 0;
        try {
            block7: while (true) {
                if (!var1_1.hasNextTick()) {
                    return;
                }
                var1_1.getNextTick(var4_4);
                var2_2.checkTimeIsInSession(var4_4.time, var8_8, var7_7.Timeframe);
                if (!var8_8.isInSession) continue;
                if (var4_4.type == 1) {
                    var6_6.set(var4_4.time, var4_4.connectionHash, var4_4.symbolHash, var4_4.bid, var4_4.ask, var4_4.volume, var8_8.sessionStartTime, var8_8.sessionEndTime, false, false);
                    if (!this.processTick(var7_7, var6_6)) continue;
                    return;
                }
                var3_3.init(var4_4);
                do {
                    if (var3_3.getNextTick(var5_5)) ** break;
                    continue block7;
                    var5_5.setSessionStartTime(var8_8.sessionStartTime);
                    var5_5.setSessionEndTime(var8_8.sessionEndTime);
                    var6_6.set(var5_5);
                } while (!this.processTick(var7_7, var6_6));
                break;
            }
            return;
        }
        finally {
            var7_7.destroy();
        }
    }

    private boolean processTick(ChartData chartData, TickEvent tickEvent) throws Exception {
        this.barType.processTick(tickEvent, this.barTypeStatus, 1);
        if (this.barTypeStatus.status == 0) {
            return false;
        }
        if (this.barTypeStatus.status != 1) {
            return false;
        }
        long l = this.barTypeStatus.barTime;
        ++this.totalBars;
        this.Time.add(tickEvent.getTime());
        int n = this.Time.size();
        return l >= this.chartDef.getHistoryFrom() && this.totalBars >= this.minimumReservedBars;
    }

    public void destroy() {
        if (this.Time != null) {
            this.Time.destroy();
            this.Time = null;
        }
    }
}

