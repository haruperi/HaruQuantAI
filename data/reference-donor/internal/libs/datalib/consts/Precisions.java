/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.datalib.consts;

import com.strategyquant.lib.L;

public class Precisions {
    private String[] langs = new String[]{L.tsq((String)"Selected timeframe only (fastest)"), L.tsq((String)"1 minute data tick simulation (slow)"), L.tsq((String)"Real Tick - custom spread (slowest)"), L.tsq((String)"Real Tick - real spread (slowest)"), L.tsq((String)"Trade On Bar Open")};
    public static final int SelectedTF = 1;
    public static final int BaseTF = 2;
    public static final int TickCustomSpread = 3;
    public static final int TickRealSpread = 4;
    public static final int OpenPrices = 5;
    public static final String PRECISION_SELECTED_TF = "Selected timeframe only (fastest)";
    public static final String PRECISION_BASE_TF = "1 minute data tick simulation (slow)";
    public static final String PRECISION_TICK_CUSTOM_SPREADS = "Real Tick - custom spread (slowest)";
    public static final String PRECISION_TICK_REAL_SPREADS = "Real Tick - real spread (slowest)";
    public static final String PRECISION_OPEN_PRICES = "Trade On Bar Open";

    public static String toString(int n) {
        switch (n) {
            case 1: {
                return PRECISION_SELECTED_TF;
            }
            case 2: {
                return PRECISION_BASE_TF;
            }
            case 3: {
                return PRECISION_TICK_CUSTOM_SPREADS;
            }
            case 4: {
                return PRECISION_TICK_REAL_SPREADS;
            }
            case 5: {
                return PRECISION_OPEN_PRICES;
            }
        }
        return null;
    }

    public static int getPrecision(String string) throws Exception {
        switch (string) {
            case "Selected timeframe only (fastest)": {
                return 1;
            }
            case "1 minute data tick simulation (slow)": {
                return 2;
            }
            case "Real Tick - custom spread (slowest)": {
                return 3;
            }
            case "Real Tick - real spread (slowest)": {
                return 4;
            }
            case "Trade On Bar Open": {
                return 5;
            }
            case "Real Tick precision (slowest)": {
                return 4;
            }
        }
        throw new Exception("Unknown precision type: '" + string + "'");
    }

    public static int getPrecision(int n) throws Exception {
        switch (n) {
            case 1: {
                return 1;
            }
            case 2: {
                return 2;
            }
            case 3: {
                return 3;
            }
            case 4: {
                return 4;
            }
            case 5: {
                return 5;
            }
        }
        throw new Exception("Unknown precision type: '" + n + "'");
    }
}

