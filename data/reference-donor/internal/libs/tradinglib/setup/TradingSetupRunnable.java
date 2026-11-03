/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.IDataBuffer
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.setup;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingSetupRunnable
extends Thread {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradingSetupRunnable");
    private static final int RUNSTATUS_BEFORESTART = 0;
    private static final int RUNSTATUS_RUNNING = 1;
    private static final int RUNSTATUS_STOPPING = 2;
    private static final int RUNSTATUS_STOPPED = 3;
    private static final int RUNSTATUS_FINISHED = 4;
    private static final int RUNSTATUS_EXCEPTION = 5;
    private static final long MAX_STOPPING_TIME = 2000L;
    protected TradingSetup tradingSetup;
    protected IDataBuffer dataBuffer;
    protected final BarUpdateInfo updateInfo = new BarUpdateInfo();
    protected long lastIndex;
    private Exception tradingException = null;
    StampedLock exceptionStampedLock = new StampedLock();
    private int runStatus = 0;
    StampedLock runStatusStampedLock = new StampedLock();
    private MarketData marketData = null;
    private boolean usePreparedData = true;
    private int barUpdateEventType;

    public TradingSetupRunnable(TradingSetup tradingSetup, boolean bl) {
        this.tradingSetup = tradingSetup;
        this.usePreparedData = bl;
        this.barUpdateEventType = tradingSetup.getBarEventType();
        this.lastIndex = -1L;
    }

    public void runUnused() {
        if (this.getRunStatus() != 0) {
            this.setTradingException(new Exception("Cannot restart this runner after it was finished or interrupted !"));
            return;
        }
        try {
            int n;
            this.setRunStatus(1);
            this.dataBuffer = this.tradingSetup.getTradingEngine().getConnectionManager().getDataBuffer();
            TickEvent tickEvent = new TickEvent();
            do {
                long l;
                if ((l = this.dataBuffer.getOne(this.lastIndex, tickEvent)) == -1L) continue;
                this.runOneCycle(tickEvent, true);
                this.lastIndex = l;
            } while ((n = this.getRunStatusUnlocked()) != 2);
            this.setRunStatus(3);
            if (n != 3) {
                this.setRunStatus(4);
            }
        }
        catch (Exception exception) {
            this.setRunStatus(5);
            this.setTradingException(exception);
        }
    }

    public void stopRunner() throws Exception {
        long l;
        if (this.getRunStatus() != 1) {
            return;
        }
        this.setRunStatus(2);
        long l2 = System.currentTimeMillis();
        while (true) {
            int n;
            if ((n = this.getRunStatus()) == 3 || n == 4 || n == 5) {
                return;
            }
            l = System.currentTimeMillis();
            if (l - l2 > 2000L) break;
            try {
                TradingSetupRunnable.sleep(10L);
            }
            catch (InterruptedException interruptedException) {}
        }
        this.interrupt();
        l2 = System.currentTimeMillis();
        while (true) {
            if (this.isInterrupted()) {
                this.setRunStatus(3);
                return;
            }
            l = System.currentTimeMillis();
            if (l - l2 > 2000L) break;
            try {
                TradingSetupRunnable.sleep(10L);
            }
            catch (InterruptedException interruptedException) {}
        }
        throw new Exception("Cannot stop runner !");
    }

    private void setRunStatus(int n) {
        this.runStatus = n;
    }

    public int getRunStatus() {
        return this.runStatus;
    }

    public int getRunStatusUnlocked() {
        return this.runStatus;
    }

    private void setTradingException(Exception exception) {
        this.tradingException = exception;
    }

    public Exception getTradingException() {
        return this.tradingException;
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    protected void runOneCycle(TickEvent tickEvent, boolean bl) throws Exception {
        if (this.barUpdateEventType == 3) {
            if (!this.usePreparedData) throw new Exception("Not implemented!");
            this.processReceivedTickOnClosePrepared(tickEvent, bl);
            return;
        } else if (this.usePreparedData) {
            this.processReceivedTickPrepared(tickEvent, bl);
            return;
        } else {
            this.processReceivedTickRealtime(tickEvent);
        }
    }

    private void processReceivedTickOnClosePrepared(TickEvent tickEvent, boolean bl) throws Exception {
        if (this.marketData == null) {
            this.marketData = this.tradingSetup.getMarketData();
        }
        boolean bl2 = false;
        this.updateInfo.updatedChart = -1;
        this.updateInfo.updatedMainChart = false;
        this.updateInfo.multipleChartsUpdated = false;
        this.updateInfo.eventType = 1;
        if (this.marketData.findTickInData(tickEvent, this.updateInfo, 3, true, false)) {
            if (bl && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 3)) {
                bl2 = true;
            }
            if (this.marketData.isNextDay(tickEvent)) {
                this.tradingSetup.callExitEOD(tickEvent);
            }
        }
        this.tradingSetup.callOptionsOnTick(tickEvent);
        this.marketData.findTickInData(tickEvent, this.updateInfo, 2, false, false);
        if (!bl2 && this.updateInfo.eventType != 1) {
            if (bl) {
                this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 4);
            }
            bl2 = true;
        }
    }

    private void processReceivedTickPrepared(TickEvent tickEvent, boolean bl) throws Exception {
        if (this.marketData == null) {
            this.marketData = this.tradingSetup.getMarketData();
        }
        boolean bl2 = false;
        this.updateInfo.updatedChart = -1;
        this.updateInfo.updatedMainChart = false;
        this.updateInfo.multipleChartsUpdated = false;
        this.updateInfo.eventType = 1;
        this.tradingSetup.callOptionsOnTick(tickEvent);
        if (this.marketData.findTickInData(tickEvent, this.updateInfo, 2, false) && bl && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 2)) {
            bl2 = true;
        }
        if (!bl2 && this.updateInfo.eventType != 1) {
            if (bl) {
                this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 4);
            }
            bl2 = true;
        }
    }

    private void processReceivedTickWithCloseEvent(TickEvent tickEvent) throws Exception {
        MarketData marketData = this.tradingSetup.getMarketData();
        boolean bl = false;
        this.updateInfo.updatedChart = -1;
        this.updateInfo.multipleChartsUpdated = false;
        this.updateInfo.eventType = 1;
        this.tradingSetup.callOptionsOnTick(tickEvent);
        if (marketData.findTickInData(tickEvent, this.updateInfo, 3, true) && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 3)) {
            bl = true;
        }
        if (marketData.findTickInData(tickEvent, this.updateInfo, 2, true) && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 2)) {
            bl = true;
        }
        if (!bl && this.updateInfo.eventType != 1) {
            this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 4);
            bl = true;
        }
    }

    private void processReceivedTickRealtime(TickEvent tickEvent) throws Exception {
        MarketData marketData = this.tradingSetup.getMarketData();
        boolean bl = false;
        this.updateInfo.updatedChart = -1;
        this.updateInfo.updatedMainChart = false;
        this.updateInfo.multipleChartsUpdated = false;
        this.updateInfo.eventType = 1;
        this.tradingSetup.callOptionsOnTick(tickEvent);
        if (marketData.processTick(tickEvent, this.updateInfo, 3) && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 3)) {
            bl = true;
        }
        if (marketData.processTick(tickEvent, this.updateInfo, 2) && this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 2)) {
            bl = true;
        }
        if (!bl && this.updateInfo.eventType != 1) {
            this.tradingSetup.callStrategyOnBarUpdate(this.updateInfo, 4);
            bl = true;
        }
    }

    public void setBarEventType(int n) {
        this.barUpdateEventType = n;
    }
}

