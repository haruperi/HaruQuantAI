/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine.stockpicker.constants;

public class PickerEodTypes {
    public static final byte DayClose = 5;
    public static final byte NotDefined = 10;
    public static final byte[] AvailableOptions = new byte[]{5, 10};

    public static String toString(byte by) {
        switch (by) {
            case 5: {
                return "End of day";
            }
            case 10: {
                return "";
            }
        }
        return "Unknown";
    }
}

