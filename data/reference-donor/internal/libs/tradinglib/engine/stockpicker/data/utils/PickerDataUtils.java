/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.utils;

import com.strategyquant.datalib.data.io.VersatileData;

public class PickerDataUtils {
    public static float computeWeightedValue(VersatileData versatileData) {
        return (float)(versatileData.high + versatileData.low + versatileData.close + versatileData.close) / 4.0f;
    }

    public static float computeTypicalValue(VersatileData versatileData) {
        return (float)(versatileData.high + versatileData.low + versatileData.close) / 3.0f;
    }

    public static float computeMedianValue(VersatileData versatileData) {
        return (float)(versatileData.high + versatileData.low) / 2.0f;
    }

    public static float computeWeightedValue(float f, float f2, float f3, float f4) {
        return (f2 + f3 + f4 + f4) / 4.0f;
    }

    public static float computeTypicalValue(float f, float f2, float f3, float f4) {
        return (f2 + f3 + f4) / 3.0f;
    }

    public static float computeMedianValue(float f, float f2, float f3, float f4) {
        return (f2 + f3) / 2.0f;
    }
}

