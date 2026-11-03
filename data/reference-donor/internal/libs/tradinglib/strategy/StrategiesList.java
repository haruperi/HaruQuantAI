/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.StrategyBase;

public class StrategiesList
extends CustomClasses<StrategyBase> {
    private static StrategiesList instance;

    static StrategiesList get() {
        if (instance == null) {
            instance = new StrategiesList();
        }
        return instance;
    }

    private StrategiesList() {
        this.setDirName("Strategies");
        this.setExpectedClassType(StrategyBase.class);
        this.loadAvailableClasses();
    }

    public static StrategyBase create(String string) throws NonexistingCustomClassException {
        return StrategiesList.get()._create(string);
    }

    private StrategyBase _create(String string) throws NonexistingCustomClassException {
        for (StrategyBase strategyBase : this.getAvailableClasses()) {
            if (!strategyBase.getClass().getSimpleName().equals(string)) continue;
            try {
                StrategyBase strategyBase2 = strategyBase.newInstance();
                return strategyBase2;
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance of a strategy '" + string + "'", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }
}

