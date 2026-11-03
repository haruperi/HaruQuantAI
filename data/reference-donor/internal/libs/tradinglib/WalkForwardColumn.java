/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.table.TableColumn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class WalkForwardColumn
extends TableColumn {
    private static final Logger Log = LoggerFactory.getLogger(WalkForwardColumn.class);
    private byte valueType = (byte)-1;
    public static final String WFScoreStatsColumn = "WFScore";

    public byte getValueType() {
        return this.valueType;
    }

    public WalkForwardColumn(String string, String string2, String string3, byte by) {
        super(string2, string3);
        this.statsValueName = string;
        this.valueType = by;
    }

    public abstract double compute(WalkForwardResult var1);

    public synchronized void compute(WalkForwardResult walkForwardResult, SQStats sQStats) {
        double d = this.compute(walkForwardResult);
        sQStats.set(this.statsValueName, d);
    }
}

