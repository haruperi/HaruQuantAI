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

public class SessionOption
extends TradingOption {
    @Parameter(name="Session", defaultValue="No Session", category="Session")
    @Editor(type=40)
    @Help(value="Set trading session. Only for stocks & futures, it has no effect in MetaTrader4/5 engine!!!")
    @ForEngine(value="MC,TS")
    public String Session;

    public SessionOption() {
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
        SessionOption sessionOption = new SessionOption();
        sessionOption.Session = this.Session;
        return sessionOption;
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

