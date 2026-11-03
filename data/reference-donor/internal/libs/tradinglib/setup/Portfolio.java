/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.IUniqueNameChecker
 */
package com.strategyquant.tradinglib.setup;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.IUniqueNameChecker;
import com.strategyquant.tradinglib.engine.TradingSetup;
import java.util.ArrayList;

public class Portfolio {
    private ArrayList<TradingSetup> tradingSetups = null;

    public Portfolio() {
    }

    public Portfolio(TradingSetup tradingSetup) throws Exception {
        this.add(tradingSetup);
    }

    public String add(TradingSetup tradingSetup) throws Exception {
        String string;
        if (this.tradingSetups == null) {
            this.tradingSetups = new ArrayList();
        }
        if ((string = tradingSetup.getName()) == null) {
            string = tradingSetup.getStrategy().getStrategyName();
        }
        string = SQUtils.generateUniqueName((String)string, (IUniqueNameChecker)new IUniqueNameChecker(){

            public boolean checkNameExist(String string) {
                for (TradingSetup tradingSetup : Portfolio.this.tradingSetups) {
                    if (!tradingSetup.getName().equals(string)) continue;
                    return true;
                }
                return false;
            }
        });
        tradingSetup.setName(string);
        this.tradingSetups.add(tradingSetup);
        tradingSetup.getStrategy().setSetupName(string);
        return string;
    }

    public ArrayList<TradingSetup> getTradingSetups() {
        return this.tradingSetups;
    }

    public TradingSetup getFirstTradingSetup() {
        if (this.tradingSetups == null || this.tradingSetups.size() == 0) {
            return null;
        }
        return this.tradingSetups.get(0);
    }

    public void runChecks() throws TradingException {
        if (this.tradingSetups == null || this.tradingSetups.size() == 0) {
            throw new TradingException("Initialization: PortfolioSetup doesn't contain any trading setups!");
        }
    }

    public void initialize() {
    }

    public void deinitialize() throws Exception {
        for (TradingSetup tradingSetup : this.tradingSetups) {
            tradingSetup.stop();
            tradingSetup.destroy();
        }
    }

    public void clear() {
        this.tradingSetups.clear();
    }

    public void remove(TradingSetup tradingSetup) {
        this.tradingSetups.remove(tradingSetup);
    }
}

