/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.swap;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import java.util.ArrayList;
import java.util.HashMap;

public class SwapCalculator {
    private static final HashMap<String, InstrumentInfo> instrumentsMap = new HashMap();
    private static final long DayMillis = 86400000L;

    public static double calculate(LiveOrderObj liveOrderObj, SwapMethod swapMethod) throws Exception {
        if (swapMethod == null || !swapMethod.isUsed()) {
            return 0.0;
        }
        double d = liveOrderObj.getOpenPrice();
        return SwapCalculator.calculateSwap(liveOrderObj.getSymbol(), d, liveOrderObj.getOpenTime(), liveOrderObj.getCloseTime(), liveOrderObj.getSize(), swapMethod, liveOrderObj.isLong());
    }

    public static double calculate(Order order, SwapMethod swapMethod) throws Exception {
        if (order.isBalanceOrder() || !order.isRealOrder()) {
            return 0.0;
        }
        if (swapMethod == null || !swapMethod.isUsed()) {
            return 0.0;
        }
        double d = order.OpenPrice;
        return SwapCalculator.calculateSwap(order.Symbol, d, order.OpenTime, order.CloseTime, order.Size, swapMethod, order.isLong());
    }

    private static double calculateSwap(String string, double d, long l, long l2, double d2, SwapMethod swapMethod, boolean bl) throws Exception {
        InstrumentInfo instrumentInfo = SwapCalculator.getInstrumentInfo(string);
        double d3 = SwapCalculator.calculateSwapCost(instrumentInfo.tickStep, d, d2, instrumentInfo.pointValue, swapMethod.getLongSwap(), swapMethod.getType());
        double d4 = SwapCalculator.calculateSwapCost(instrumentInfo.tickStep, d, d2, instrumentInfo.pointValue, swapMethod.getShortSwap(), swapMethod.getType());
        int n = SwapCalculator.getSwapCount(swapMethod.getRolloutHour(), swapMethod.getRolloutMinute(), l, l2, swapMethod.getTripleSwapOn());
        double d5 = d3 * (double)n;
        double d6 = d4 * (double)n;
        if (bl) {
            return d5;
        }
        return d6;
    }

    private static double calculateSwapCost(double d, double d2, double d3, double d4, double d5, String string) throws Exception {
        switch (string) {
            case "points": {
                return d3 * d4 * d * d5;
            }
            case "percent": {
                return d3 * d4 * d2 * (d5 / 100.0 / 360.0);
            }
            case "money": {
                return d3 * d5;
            }
        }
        throw new Exception(String.format("Swap type not recognized: %s", string));
    }

    private static int getSwapCount(int n, int n2, long l, long l2, String string) throws Exception {
        long l3 = SQTime.setTime((long)l, (int)n, (int)n2, (int)0, (int)0);
        long l4 = SQTime.setTime((long)l2, (int)n, (int)n2, (int)0, (int)0);
        int n3 = SwapCalculator.getTripleDayIndex(string);
        ArrayList<Integer> arrayList = SwapCalculator.getTradeDaysOfWeek(l, l2);
        int n4 = 0;
        for (int i = 0; i < arrayList.size(); ++i) {
            int n5 = arrayList.get(i);
            if (i == 0 && l > l3 || i == arrayList.size() - 1 && l2 <= l4 || n5 == 6 || n5 == 7) continue;
            if (n5 == n3) {
                n4 += 3;
                continue;
            }
            ++n4;
        }
        return n4;
    }

    private static ArrayList<Integer> getTradeDaysOfWeek(long l, long l2) {
        ArrayList<Integer> arrayList = new ArrayList<Integer>();
        int n = 1;
        for (long i = l - l % 86400000L; i <= l2; i += 86400000L) {
            int n2 = SQTime.getDayOfWeek((long)i);
            arrayList.add(n2);
            if (n++ <= 10000) continue;
            break;
        }
        return arrayList;
    }

    private static synchronized InstrumentInfo getInstrumentInfo(String string) throws Exception {
        InstrumentInfo instrumentInfo;
        DataInfo dataInfo;
        if (!instrumentsMap.containsKey(string) && (dataInfo = DataManager.getDataInfo((String)"History", (String)string)) != null && (instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument)) != null) {
            instrumentsMap.put(string, instrumentInfo);
            return instrumentInfo;
        }
        return instrumentsMap.get(string);
    }

    private static int getTripleDayIndex(String string) {
        if (string == null) {
            return -1;
        }
        switch (string) {
            case "MONDAY": {
                return 1;
            }
            case "TUESDAY": {
                return 2;
            }
            case "WEDNESDAY": {
                return 3;
            }
            case "THURSDAY": {
                return 4;
            }
            case "FRIDAY": {
                return 5;
            }
        }
        return -1;
    }
}

