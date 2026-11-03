/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import java.util.TreeMap;

@ForEngine(value="MT5")
public class MarketOpenSession
extends TradingOption {
    @Parameter(name="MarketOpenSession", defaultValue="No Session", category="Session")
    @Editor(type=40)
    @Help(value="Set trading session. This setting has no effect in MetaTrader platform, only in SQX!")
    @ForEngine(value="MT5")
    public String MarketOpenSession;

    public MarketOpenSession() {
        this.inbuild = true;
    }

    @Override
    public TreeMap<String, String> getCustomOptions() {
        TreeMap<String, String> treeMap = new TreeMap<String, String>();
        for (Session session : SessionManager.getSessions()) {
            String string = session.getSessionName();
            treeMap.put(string, string);
        }
        return treeMap;
    }

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) {
        return true;
    }

    public TradingOption clone() {
        MarketOpenSession marketOpenSession = new MarketOpenSession();
        marketOpenSession.MarketOpenSession = this.MarketOpenSession;
        return marketOpenSession;
    }

    @Override
    public TradingOption getClone() throws CloneNotSupportedException {
        return this.clone();
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }
}

