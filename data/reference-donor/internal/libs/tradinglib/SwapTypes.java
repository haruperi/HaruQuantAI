/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.task.settings.buildmode.JSONAble;

public class SwapTypes
extends JSONAble {
    public static final String POINTS = "points";
    public static final String PERCENT = "percent";
    public static final String MONEY = "money";

    public static String toString(String string) {
        switch (string) {
            case "points": {
                return L.t((String)POINTS, (Object[])new Object[0]);
            }
            case "percent": {
                return "%";
            }
            case "money": {
                return "$";
            }
        }
        return L.t((String)"Unknown", (Object[])new Object[0]);
    }
}

