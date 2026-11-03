/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;

public class OrderTypes {
    public static final byte Any = 0;
    public static final byte Buy = 1;
    public static final byte Sell = 2;
    public static final byte BuyLimit = 3;
    public static final byte SellLimit = 4;
    public static final byte BuyStop = 5;
    public static final byte SellStop = 6;
    public static final byte BuyStopLimit = 7;
    public static final byte SellStopLimit = 8;
    public static final byte Deposit = 9;
    public static final byte Withdrawal = 10;
    public static final byte Balance = 11;
    public static final byte BuyToCoverStop = 100;
    public static final byte BuyToCoverLimit = 101;
    public static final byte SellToCoverStop = 102;
    public static final byte SellToCoverLimit = 103;

    public static boolean isMarketOrder(byte by) {
        return by == 1 || by == 2;
    }

    public static boolean isLongOrder(byte by) {
        return by == 1 || by == 3 || by == 5 || by == 7;
    }

    public static boolean isShortOrder(byte by) {
        return by == 2 || by == 4 || by == 6 || by == 8;
    }

    public static boolean areOppositeOrders(byte by, byte by2) {
        if (OrderTypes.isShortOrder(by) && OrderTypes.isLongOrder(by2)) {
            return true;
        }
        return OrderTypes.isLongOrder(by) && OrderTypes.isShortOrder(by2);
    }

    public static byte getOppositeType(byte by) {
        if (by == 1) {
            return 2;
        }
        if (by == 2) {
            return 1;
        }
        return 0;
    }

    public static String toString(byte by) {
        switch (by) {
            case 0: {
                return L.t((String)"Any", (Object[])new Object[0]);
            }
            case 1: {
                return L.t((String)"Buy", (Object[])new Object[0]);
            }
            case 2: {
                return L.t((String)"Sell", (Object[])new Object[0]);
            }
            case 3: {
                return L.t((String)"BuyLimit", (Object[])new Object[0]);
            }
            case 4: {
                return L.t((String)"SellLimit", (Object[])new Object[0]);
            }
            case 5: {
                return L.t((String)"BuyStop", (Object[])new Object[0]);
            }
            case 6: {
                return L.t((String)"SellStop", (Object[])new Object[0]);
            }
            case 7: {
                return L.t((String)"BuyStopLimit", (Object[])new Object[0]);
            }
            case 8: {
                return L.t((String)"SellStopLimit", (Object[])new Object[0]);
            }
            case 9: {
                return L.t((String)"Deposit", (Object[])new Object[0]);
            }
            case 10: {
                return L.t((String)"Withdrawal", (Object[])new Object[0]);
            }
            case 11: {
                return L.t((String)"Balance", (Object[])new Object[0]);
            }
            case 100: {
                return L.t((String)"BuyToCoverStop", (Object[])new Object[0]);
            }
            case 101: {
                return L.t((String)"BuyToCoverLimit", (Object[])new Object[0]);
            }
            case 102: {
                return L.t((String)"SellToCoverStop", (Object[])new Object[0]);
            }
            case 103: {
                return L.t((String)"SellToCoverLimit", (Object[])new Object[0]);
            }
        }
        return L.t((String)"Unknown", (Object[])new Object[0]);
    }

    public static byte parseMT4(String string) {
        switch (string) {
            case "buy": {
                return 1;
            }
            case "buy stop": {
                return 5;
            }
            case "buy limit": {
                return 3;
            }
            case "sell": {
                return 2;
            }
            case "sell stop": {
                return 6;
            }
            case "sell limit": {
                return 4;
            }
        }
        return -1;
    }

    public static byte parseMT5(String string) {
        switch (string) {
            case "buy": {
                return 1;
            }
            case "buy stop": {
                return 1;
            }
            case "buy limit": {
                return 1;
            }
            case "sell": {
                return 2;
            }
            case "sell stop": {
                return 2;
            }
            case "sell limit": {
                return 2;
            }
        }
        return -1;
    }

    public static boolean isStopOrder(byte by) {
        return by == 5 || by == 6;
    }

    public static boolean isLimitOrder(byte by) {
        return by == 3 || by == 4;
    }
}

