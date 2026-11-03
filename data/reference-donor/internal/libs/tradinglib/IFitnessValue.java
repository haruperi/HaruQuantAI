/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

public interface IFitnessValue {
    default public double transformToFitnessRange(double d, double d2, double d3, double d4, byte by) {
        double d5 = 1.0;
        if (by == 3) {
            double d6 = Math.abs(d - d2);
            double d7 = d2 / 100.0;
            double d8 = d6 / d7;
            d5 = 1.0 / (1.0 + d8 / 100.0);
            return d5;
        }
        if (d <= 0.0) {
            if (d3 == 0.0) {
                d5 = 1.0;
            }
            if (d != 0.0) {
                d5 = d3 < -8000.0 ? 1.0 - 1200.0 / (Math.abs(d) + 4000.0) : 1.0 - 0.3 / (Math.abs(d) / (Math.abs(d3) / 10.0) + 1.0);
            }
        } else {
            if (by == 1 && d3 == 0.0 && d4 == 1.0 && d <= 1.0 && d >= 0.0) {
                return d;
            }
            d5 = d4 > 8000.0 ? 2800.0 / (d + 4000.0) : 0.7 / (1.0 + d / (d4 / 10.0));
        }
        if (d5 > 1.0) {
            d5 = 1.0;
        }
        if (d5 < 0.0) {
            d5 = 0.0;
        }
        if (by == 1) {
            return 1.0 - d5;
        }
        return d5;
    }
}

