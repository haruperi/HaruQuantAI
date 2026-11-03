/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;

public abstract class MonteCarloRetest
extends ParametersTableItem
implements ISQCloneable<MonteCarloRetest> {
    private final int type;
    protected SettingsMap settings;

    public MonteCarloRetest(int n) {
        this.type = n;
    }

    public int getType() {
        return this.type;
    }

    public void modifySettings(IRandomGenerator iRandomGenerator, SettingsMap settingsMap) throws Exception {
    }

    public void modifyData(IRandomGenerator iRandomGenerator, TickEvent tickEvent, double d) {
    }

    public abstract MonteCarloRetest getClone() throws Exception;

    public void initSettings(SettingsMap settingsMap) {
        this.settings = this.settings;
    }

    public void modifyOHLCData(IRandomGenerator iRandomGenerator, VersatileData versatileData, double d) {
    }
}

