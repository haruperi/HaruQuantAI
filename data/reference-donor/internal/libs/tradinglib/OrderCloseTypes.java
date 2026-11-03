/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;

public class OrderCloseTypes {
    public static final byte Manual = 1;
    public static final byte SL = 2;
    public static final byte PT = 3;
    public static final byte EndTest = 4;
    public static final byte EOD = 5;
    public static final byte Expired = 6;
    public static final byte Reversed = 7;
    public static final byte Deleted = 8;
    public static final byte Replaced = 9;
    public static final byte OCA = 11;
    public static final byte Commission = 12;
    public static final byte EOD_TIME = 13;
    public static final byte EOF = 14;
    public static final byte EOF_TIME = 16;
    public static final byte EOR = 17;
    public static final byte NETTING_CONTROL_ORDER = 18;
    public static final byte ExitAfterXBars = 19;
    public static final byte MoveSL2BE = 20;
    public static final byte TrailingStop = 21;
    public static final byte ExitSignal = 22;
    public static final byte EOD_NEXT_OPEN = 55;
    public static final byte Delisted = 60;

    public static String toString(byte by) {
        switch (by) {
            case 1: {
                return L.tsq((String)"Manual");
            }
            case 2: {
                return L.tsq((String)"SL");
            }
            case 3: {
                return L.tsq((String)"PT");
            }
            case 4: {
                return L.tsq((String)"EndTest");
            }
            case 5: {
                return L.tsq((String)"End Of Day");
            }
            case 55: {
                return L.tsq((String)"End Of Day (Next Market Open)");
            }
            case 6: {
                return L.tsq((String)"Expired");
            }
            case 7: {
                return L.tsq((String)"Reversed");
            }
            case 8: {
                return L.tsq((String)"Deleted");
            }
            case 9: {
                return L.tsq((String)"Replaced");
            }
            case 11: {
                return L.tsq((String)"OCA");
            }
            case 12: {
                return L.tsq((String)"Commission");
            }
            case 13: {
                return L.tsq((String)"End Of Day (Time)");
            }
            case 14: {
                return L.tsq((String)"End Of Friday");
            }
            case 16: {
                return L.tsq((String)"End Of Friday (Time)");
            }
            case 17: {
                return L.tsq((String)"End Of Range");
            }
            case 18: {
                return L.tsq((String)"Control order");
            }
            case 19: {
                return L.tsq((String)"Exit After X Bars");
            }
            case 20: {
                return L.tsq((String)"MoveSL2BE");
            }
            case 21: {
                return L.tsq((String)"TrailingStop");
            }
            case 22: {
                return L.tsq((String)"Exit Signal");
            }
            case 60: {
                return L.tsq((String)"Delisted");
            }
        }
        return "Unknown";
    }

    public static boolean wasRealized(byte by) {
        return by != 6;
    }

    public static byte parseMT4(String string) {
        switch (string) {
            case "close": {
                return 1;
            }
            case "close at stop": {
                return 4;
            }
            case "t/p": {
                return 3;
            }
            case "s/l": {
                return 2;
            }
            case "delete": {
                return 1;
            }
        }
        return 0;
    }

    public static byte parseMT5(String string) {
        if (string.startsWith("end of test")) {
            return 4;
        }
        if (string.startsWith("sl")) {
            return 2;
        }
        if (string.startsWith("tp")) {
            return 3;
        }
        return 1;
    }
}

