/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine;

public class TradingSetupStatus {
    public static final int Paused = 0;
    public static final int Running = 1;
    public static final int Stopped = 2;

    public static String toString(int n) {
        switch (n) {
            case 0: {
                return "Paused";
            }
            case 1: {
                return "Running";
            }
            case 2: {
                return "Stopped";
            }
        }
        return "Undefined";
    }
}

