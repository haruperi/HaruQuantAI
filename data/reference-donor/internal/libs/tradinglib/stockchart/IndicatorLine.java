/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.tradinglib.stockchart.ChartKind;

public class IndicatorLine {
    private String line;
    private ChartKind kind;
    private String color;
    private Float[] yValues;
    private boolean showInChart = true;
    private boolean showZeroValues = true;

    public String getLine() {
        return this.line;
    }

    public void setLine(String string) {
        this.line = string;
    }

    public ChartKind getKind() {
        return this.kind;
    }

    public void setKind(ChartKind chartKind) {
        this.kind = chartKind;
    }

    public String getColor() {
        return this.color;
    }

    public void setColor(String string) {
        this.color = string;
    }

    public Float[] getyValues() {
        return this.yValues;
    }

    public void setyValues(Float[] floatArray) {
        this.yValues = floatArray;
    }

    public boolean isShowInChart() {
        return this.showInChart;
    }

    public void setShowInChart(boolean bl) {
        this.showInChart = bl;
    }

    public boolean isShowZeroValues() {
        return this.showZeroValues;
    }

    public void setShowZeroValues(boolean bl) {
        this.showZeroValues = bl;
    }
}

