/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.engine.stockpicker.constants;

import com.strategyquant.lib.L;

public class PickerTriggerTypes {
    public static final byte OnBarOpen = 5;
    public static final byte OnBarClose = 10;
    public static final byte BeforeBarOpen = 15;
    public static final byte[] AvailableOptions = new byte[]{5, 10, 15};

    public static String toString(byte by) {
        switch (by) {
            case 15: {
                return L.tsq((String)"Before Bar Open");
            }
            case 5: {
                return L.tsq((String)"On Bar Open");
            }
            case 10: {
                return L.tsq((String)"On Bar Close");
            }
        }
        return "Unknown";
    }

    public static byte parse(String string) {
        switch (string) {
            case "BeforeBarOpen": 
            case "AfterBarClose": {
                return 15;
            }
            case "OnBarOpen": {
                return 5;
            }
            case "OnBarClose": {
                return 10;
            }
        }
        return -1;
    }

    public static String getKey(byte by) throws Exception {
        switch (by) {
            case 15: {
                return "BeforeBarOpen";
            }
            case 5: {
                return "OnBarOpen";
            }
            case 10: {
                return "OnBarClose";
            }
        }
        throw new Exception(L.t((String)"Invalid trigger type %s", (Object[])new Object[]{by}));
    }
}

