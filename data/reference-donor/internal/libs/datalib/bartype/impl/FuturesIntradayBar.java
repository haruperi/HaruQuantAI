/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.bartype.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.data.DataException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FuturesIntradayBar
extends BarType {
    public static final Logger Log = LoggerFactory.getLogger((String)"FxIntradayBar");

    public FuturesIntradayBar() {
        super(2, "Intraday");
    }

    @Override
    public void processTickImplementation(TickEvent tickEvent, BarTypeStatus barTypeStatus, int n) throws DataException {
        long l;
        barTypeStatus.barTime = l = tickEvent.getTime();
        barTypeStatus.status = tickEvent.isBarOpen() ? 1 : 2;
    }

    @Override
    public BarType clone(String string) {
        return new FuturesIntradayBar();
    }

    @Override
    public BarType clone() {
        return new FuturesIntradayBar();
    }

    @Override
    public boolean isTickBar() {
        return false;
    }

    @Override
    public String checkCanBeComputedFrom(String string) throws DataException {
        return null;
    }

    @Override
    public String getBaseTF() {
        return "Intraday";
    }

    @Override
    public String getTickTF() {
        return "Intraday";
    }

    @Override
    public long estimateStartDate(int n, long l) {
        return 0L;
    }

    @Override
    public boolean checkTimeframeIsSupported(String string) {
        return string.toUpperCase().equals("INTRADAY");
    }

    @Override
    public int getPeriodInMS() {
        return 0;
    }
}

