/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.strategy.StrategiesList;

public class TradingUtils {
    public static StrategyBase getStrategy(SettingsMap settingsMap) throws TradingException {
        if (settingsMap.containsKey("StrategyObject")) {
            if (!(settingsMap.get("StrategyObject") instanceof StrategyBase)) {
                throw new TradingException("Setting 'TradingSetup.StrategyObject was set, but it has incorrect value! It must be an instance of StrategyBase object.");
            }
            return (StrategyBase)settingsMap.get("StrategyObject");
        }
        if (settingsMap.containsKey("StrategyClass")) {
            if (!(settingsMap.get("StrategyClass") instanceof String)) {
                throw new TradingException("Setting 'TradingSetup.StrategyClass was set, but it has incorrect value! It must be a string with name of existing strategy.");
            }
            String string = (String)settingsMap.get("StrategyClass");
            try {
                return StrategiesList.create(string);
            }
            catch (NonexistingCustomClassException nonexistingCustomClassException) {
                throw new TradingException("Cannot create an instance of '" + string + "' class.");
            }
        }
        throw new TradingException("Setting 'TradingSetup.StrategyClass' is not set.");
    }
}

