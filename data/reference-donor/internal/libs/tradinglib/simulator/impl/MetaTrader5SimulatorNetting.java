/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.session.SessionStatus
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.MetaTraderSimulatorNetting;

public class MetaTrader5SimulatorNetting
extends MetaTraderSimulatorNetting {
    private byte executionType;
    private SessionStatus marketOpenSessionStatus = new SessionStatus();

    public MetaTrader5SimulatorNetting(byte by) {
        this.executionType = by;
    }

    @Override
    public ITradingSimulator clone() {
        MetaTrader5SimulatorNetting metaTrader5SimulatorNetting = new MetaTrader5SimulatorNetting(this.executionType);
        metaTrader5SimulatorNetting.setTestPrecision(this.getTestPrecision());
        return metaTrader5SimulatorNetting;
    }

    @Override
    protected boolean checkPriceLevelCorrectness(int n, double d, double d2) {
        return !(n == 5 || n == 4 ? (this.executionType == 4 ? d > d2 : d >= d2) : (this.executionType == 4 ? d < d2 : d <= d2));
    }

    @Override
    public boolean fillAtRealAskBidPrice() {
        return this.getTestPrecision() == 3 || this.getTestPrecision() == 4;
    }

    @Override
    protected double getSLPTFilledPrice(double d, double d2) {
        return this.getTestPrecision() == 3 || this.getTestPrecision() == 4 ? d : d2;
    }

    @Override
    public int getEngineId() {
        return 1441180233;
    }

    @Override
    public boolean IsMarketOpen() {
        if (this.marketOpenSession == null) {
            return true;
        }
        long l = this.tickData.getTime();
        String string = SQTime.toDateMinuteString((long)l);
        this.marketOpenSession.checkTimeIsInSession(l, this.marketOpenSessionStatus, null);
        Log.debug("MT sim check marketopen - time: {}, market open: {}", (Object)string, (Object)this.marketOpenSessionStatus.isInSession);
        return this.marketOpenSessionStatus.isInSession;
    }
}

