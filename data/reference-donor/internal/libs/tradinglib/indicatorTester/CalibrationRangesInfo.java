/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONObject
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.indicatorTester.CalibrationConfig;
import com.strategyquant.lib.SQUtils;
import org.json.JSONObject;

public class CalibrationRangesInfo {
    public static int maxSteps = -1;
    public String symbol;
    public String timeframe;
    public double maxValue;
    public double minValue;

    public CalibrationRangesInfo() {
    }

    public CalibrationRangesInfo(String string, String string2) {
        this.symbol = string;
        this.timeframe = string2;
    }

    public CalibrationRangesInfo(String string, String string2, double d, double d2) {
        this.symbol = string;
        this.timeframe = string2;
        this.minValue = d;
        this.maxValue = d2;
    }

    public JSONObject toJSON() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("symbol", (Object)this.symbol);
        jSONObject.put("timeframe", (Object)this.timeframe);
        jSONObject.put("minValue", this.minValue);
        jSONObject.put("maxValue", this.maxValue);
        if (maxSteps > 0) {
            jSONObject.put("step", this.getStep(this.minValue, this.maxValue));
        }
        return jSONObject;
    }

    public void fixValues() {
        double d = Math.abs(this.maxValue - this.minValue);
        if (CalibrationConfig.disableRounding) {
            this.minValue = this.floor(this.minValue, d / 100.0);
            this.maxValue = this.ceil(this.maxValue, d / 100.0);
        } else {
            this.minValue = this.floor(this.minValue, d);
            this.maxValue = this.ceil(this.maxValue, d);
        }
    }

    private double getStep(double d, double d2) {
        double d3 = (d2 - d) / (double)maxSteps;
        int n = SQUtils.getDecimalPlaces((double)d);
        int n2 = SQUtils.getDecimalPlaces((double)d2);
        int n3 = SQUtils.getDecimalPlaces((double)d3);
        if (n3 <= n || n3 <= n2) {
            return SQUtils.round((double)d3, (int)n3);
        }
        int n4 = 0;
        n4 = d3 > 100.0 ? 0 : (d3 > 10.0 ? 1 : (d3 > 1.0 ? 2 : (d3 > 0.1 ? 3 : (d3 > 0.01 ? 4 : 5))));
        n4 = maxSteps > 100 ? n4 + 1 : n4;
        n4 = Math.min(n4, 5);
        return Math.max(1.0 / Math.pow(10.0, n4), SQUtils.round((double)d3, (int)n4));
    }

    private double ceil(double d, double d2) {
        double d3 = Math.abs(d);
        double d4 = Math.abs(d2);
        if (d3 / 100000.0 > 1.0 && d4 / 100000.0 > 1.0) {
            return (int)(Math.ceil(d / 10000.0) * 10000.0);
        }
        if (d3 / 10000.0 > 1.0 && d4 / 10000.0 > 1.0) {
            return (int)(Math.ceil(d / 1000.0) * 1000.0);
        }
        if (d3 / 1000.0 > 1.0 && d4 / 1000.0 > 1.0) {
            return (int)(Math.ceil(d / 100.0) * 100.0);
        }
        if (d3 / 100.0 > 1.0 && d4 / 100.0 > 1.0) {
            return (int)(Math.ceil(d / 10.0) * 10.0);
        }
        if (d3 / 10.0 > 1.0 && d4 / 10.0 > 1.0) {
            return (int)(Math.ceil(d / 1.0) * 1.0);
        }
        if (d3 / 1.0 > 1.0 && d4 / 1.0 > 1.0) {
            return SQUtils.round((double)(Math.ceil(d / 0.1) * 0.1), (int)1);
        }
        if (d3 / 0.1 > 1.0 && d4 / 0.1 > 1.0) {
            return SQUtils.round((double)(Math.ceil(d / 0.01) * 0.01), (int)2);
        }
        if (d3 / 0.01 > 1.0 && d4 / 0.01 > 1.0) {
            return SQUtils.round((double)(Math.ceil(d / 0.001) * 0.001), (int)3);
        }
        if (d3 / 0.001 > 1.0 && d4 / 0.001 > 1.0) {
            return SQUtils.round((double)(Math.ceil(d / 1.0E-4) * 1.0E-4), (int)4);
        }
        if (d3 / 1.0E-4 > 1.0 && d4 / 1.0E-4 > 1.0) {
            return SQUtils.round((double)(Math.ceil(d / 1.0E-5) * 1.0E-5), (int)5);
        }
        return SQUtils.round((double)d, (int)5);
    }

    private double floor(double d, double d2) {
        double d3 = Math.abs(d);
        double d4 = Math.abs(d2);
        if (d3 / 100000.0 > 1.0 && d4 / 100000.0 > 1.0) {
            return (int)(Math.floor(d / 10000.0) * 10000.0);
        }
        if (d3 / 10000.0 > 1.0 && d4 / 10000.0 > 1.0) {
            return (int)(Math.floor(d / 1000.0) * 1000.0);
        }
        if (d3 / 1000.0 > 1.0 && d4 / 1000.0 > 1.0) {
            return (int)(Math.floor(d / 100.0) * 100.0);
        }
        if (d3 / 100.0 > 1.0 && d4 / 100.0 > 1.0) {
            return (int)(Math.floor(d / 10.0) * 10.0);
        }
        if (d3 / 10.0 > 1.0 && d4 / 10.0 > 1.0) {
            return (int)(Math.floor(d / 1.0) * 1.0);
        }
        if (d3 / 1.0 > 1.0 && d4 / 1.0 > 1.0) {
            return SQUtils.round((double)(Math.floor(d / 0.1) * 0.1), (int)1);
        }
        if (d3 / 0.1 > 1.0 && d4 / 0.1 > 1.0) {
            return SQUtils.round((double)(Math.floor(d / 0.01) * 0.01), (int)2);
        }
        if (d3 / 0.01 > 1.0 && d4 / 0.01 > 1.0) {
            return SQUtils.round((double)(Math.floor(d / 0.001) * 0.001), (int)3);
        }
        if (d3 / 0.001 > 1.0 && d4 / 0.001 > 1.0) {
            return SQUtils.round((double)(Math.floor(d / 1.0E-4) * 1.0E-4), (int)4);
        }
        if (d3 / 1.0E-4 > 1.0 && d4 / 1.0E-4 > 1.0) {
            return SQUtils.round((double)(Math.floor(d / 1.0E-5) * 1.0E-5), (int)5);
        }
        return SQUtils.round((double)d, (int)5);
    }
}

