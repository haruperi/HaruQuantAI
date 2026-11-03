/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

public class Directions {
    public static final byte Both = 0;
    public static final byte Long = 1;
    public static final byte Short = -1;

    public static String typeToString(byte by) {
        switch (by) {
            case 0: {
                return "Both";
            }
            case 1: {
                return "Long";
            }
            case -1: {
                return "Short";
            }
        }
        return "?";
    }
}

