/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.timeframe;

import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.TradingException;
import java.util.Comparator;

public class TimeframesComparator
implements Comparator<String> {
    @Override
    public int compare(String string, String string2) {
        long l;
        long l2;
        try {
            l2 = TimeframeManager.getTFHash(string);
        }
        catch (TradingException tradingException) {
            l2 = Integer.MAX_VALUE;
        }
        try {
            l = TimeframeManager.getTFHash(string2);
        }
        catch (TradingException tradingException) {
            l = Integer.MAX_VALUE;
        }
        if (l2 > l) {
            return 1;
        }
        if (l2 < l) {
            return -1;
        }
        return 0;
    }

    public static int getSecondsCount(String string) {
        int n = 0;
        if (string == null || string.isEmpty()) {
            return Integer.MAX_VALUE;
        }
        if (string.equals("TICK")) {
            return 0;
        }
        try {
            n = Integer.parseInt(string.substring(1).trim());
        }
        catch (Exception exception) {
            return Integer.MAX_VALUE;
        }
        if (string.startsWith("S")) {
            return n;
        }
        if (string.startsWith("M")) {
            return 60 * n;
        }
        if (string.startsWith("H")) {
            return 3600 * n;
        }
        return 86400 * n;
    }
}

