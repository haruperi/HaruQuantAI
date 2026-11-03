/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

public class IndicatorLevel {
    public static final String PATTERN_SOLID = "";
    public static final String PATTERN_DOT = "1,1";
    private String color;
    private double value;
    private String pattern;

    public String getColor() {
        return this.color;
    }

    public void setColor(String string) {
        this.color = string;
    }

    public double getValue() {
        return this.value;
    }

    public void setValue(double d) {
        this.value = d;
    }

    public String getPattern() {
        return this.pattern;
    }

    public void setPattern(String string) {
        this.pattern = string;
    }
}

