/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;

public abstract class RobustnessTestMethod
extends ParametersTableItem {
    private final int type;

    public RobustnessTestMethod(int n) {
        this.type = n;
    }

    public int getType() {
        return this.type;
    }

    public void modifyTrades(IRandomGenerator iRandomGenerator, OrdersList ordersList) throws Exception {
    }

    public void modifySettings(IRandomGenerator iRandomGenerator, SettingsMap settingsMap) throws Exception {
    }

    public void modifyData(IRandomGenerator iRandomGenerator, TickEvent tickEvent) {
    }
}

