/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.customData;

import java.util.Arrays;
import java.util.List;

public class CustomDataTypes {
    public static final byte IndicatorValuePrice = 1;
    public static final byte IndicatorValueNumber = 2;
    public static final byte IndicatorValuePriceRange = 3;
    public static final byte SignalValueBoolean = 10;
    public static final byte SignalValueAction = 11;
    public static final String IndicatorValuePriceKey = "IndicatorValuePrice";
    public static final String IndicatorValueNumberKey = "IndicatorValueNumber";
    public static final String IndicatorValuePriceRangeKey = "IndicatorValuePriceRange";
    public static final String SignalValueBooleanKey = "SignalValueBoolean";
    public static final String SignalValueActionKey = "SignalValueAction";
    public static final String IndicatorValuePriceName = "Indicator value - price";
    public static final String IndicatorValueNumberName = "Indicator value - number";
    public static final String IndicatorValuePriceRangeName = "Indicator value - price range";
    public static final String SignalValueBooleanName = "Signal - 0 means false, anything else means true";

    public static String toString(byte by) {
        switch (by) {
            case 1: {
                return IndicatorValuePriceName;
            }
            case 2: {
                return IndicatorValueNumberName;
            }
            case 3: {
                return IndicatorValuePriceRangeName;
            }
            case 10: {
                return SignalValueBooleanName;
            }
        }
        return "CustomDataType" + by;
    }

    public static String translateDataType(byte by) throws Exception {
        switch (by) {
            case 1: {
                return "price";
            }
            case 2: {
                return "number";
            }
            case 3: {
                return "pricerange";
            }
            case 10: {
                return "boolean";
            }
        }
        throw new Exception("Cannot recognize custom data indoicartor type: " + by);
    }

    public static List<Byte> availableDataTypes() {
        return Arrays.asList((byte)1, (byte)2, (byte)3, (byte)10, (byte)11);
    }
}

