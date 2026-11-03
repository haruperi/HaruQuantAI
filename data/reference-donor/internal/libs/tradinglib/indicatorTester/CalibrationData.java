/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.indicatorTester;

public class CalibrationData {
    public boolean disabled = false;
    public String values = null;

    public CalibrationData(boolean bl) {
        this.disabled = bl;
    }

    public CalibrationData(String string) {
        this.values = string;
    }
}

