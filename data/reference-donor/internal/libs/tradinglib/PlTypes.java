/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;

public class PlTypes {
    public static final byte Money = 10;
    public static final byte Percent = 20;
    public static final byte Pips = 30;
    public static final byte OpenMoney = 40;
    public static final byte OpenPercent = 50;
    public static final byte Ticks = 30;

    public static String print(byte by) {
        switch (by) {
            case 30: {
                return "pips";
            }
            case 20: 
            case 50: {
                return "%";
            }
        }
        return "$";
    }

    public static String printPL(double d, byte by) {
        String string = SQUtils.d2String((double)d, (int)2) + "";
        switch (by) {
            case 30: {
                return string + " pips";
            }
            case 20: 
            case 50: {
                return string + " %";
            }
            case 10: 
            case 40: {
                return "$" + string;
            }
        }
        return string;
    }

    public static String printPL(double d, byte by, int n) {
        String string = SQUtils.d2String((double)d, (int)n) + "";
        switch (by) {
            case 30: {
                return string + " pips";
            }
            case 20: 
            case 50: {
                return string + " %";
            }
            case 10: 
            case 40: {
                return "$" + string;
            }
        }
        return string;
    }

    public static boolean isValid(byte by) {
        switch (by) {
            case 10: 
            case 20: 
            case 30: 
            case 40: 
            case 50: {
                return true;
            }
        }
        return false;
    }

    public static String typeToString(byte by) {
        switch (by) {
            case 10: {
                return "Money";
            }
            case 20: {
                return "%";
            }
            case 30: {
                return "Pips";
            }
            case 40: {
                return "Open $";
            }
            case 50: {
                return "Open %";
            }
        }
        return "?";
    }
}

