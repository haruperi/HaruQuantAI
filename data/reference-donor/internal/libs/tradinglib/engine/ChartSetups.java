/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.ChartSetup;
import java.util.ArrayList;

public class ChartSetups
extends ArrayList<ChartSetup>
implements ISQCloneable<ChartSetups> {
    public ChartSetups() {
    }

    public ChartSetups(String string, String string2, String string3, long l, long l2, double d, String string4) throws DataException {
        ChartDef chartDef = new ChartDef(string, string2, string3, l, l2, d, string4);
        ChartSetup chartSetup = new ChartSetup();
        chartSetup.addChart(chartDef);
        this.add(chartSetup);
    }

    public ChartSetups(ChartSetup chartSetup) {
        this.add(chartSetup);
    }

    public ChartSetup getMainSetup() {
        return (ChartSetup)this.get(0);
    }

    public ChartSetups getClone() {
        ChartSetups chartSetups = new ChartSetups();
        for (int i = 0; i < this.size(); ++i) {
            chartSetups.add(((ChartSetup)this.get(i)).getClone());
        }
        return chartSetups;
    }

    public ChartSetups getClone(long l, long l2) {
        ChartSetups chartSetups = new ChartSetups();
        for (int i = 0; i < this.size(); ++i) {
            chartSetups.add(((ChartSetup)this.get(i)).getClone(l, l2));
        }
        return chartSetups;
    }
}

