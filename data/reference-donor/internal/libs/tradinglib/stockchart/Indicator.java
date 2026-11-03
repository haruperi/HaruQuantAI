/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.tradinglib.stockchart.IndicatorLevel;
import com.strategyquant.tradinglib.stockchart.IndicatorLine;

public class Indicator {
    private String title;
    private boolean subChart;
    private IndicatorLine[] lines;
    private IndicatorLevel[] levels;

    public IndicatorLevel[] getLevels() {
        return this.levels;
    }

    public void setLevels(IndicatorLevel[] indicatorLevelArray) {
        this.levels = indicatorLevelArray;
    }

    public String getTitle() {
        return this.title;
    }

    public void setTitle(String string) {
        this.title = string;
    }

    public boolean isSubChart() {
        return this.subChart;
    }

    public void setSubChart(boolean bl) {
        this.subChart = bl;
    }

    public IndicatorLine[] getLines() {
        return this.lines;
    }

    public void setLines(IndicatorLine[] indicatorLineArray) {
        this.lines = indicatorLineArray;
    }
}

