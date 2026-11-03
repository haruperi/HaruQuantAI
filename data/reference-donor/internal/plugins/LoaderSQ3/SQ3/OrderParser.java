/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.time.SQTimeOld
 *  com.strategyquant.tradinglib.Order
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.Loader.impl.SQ3;

import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.Order;
import org.jdom2.Element;

public class OrderParser {
    public static Order parse(Element elOrder, String ordersVersion) {
        long timeInTrade;
        Order order = new Order();
        if (ordersVersion == null || !ordersVersion.equalsIgnoreCase("2.0")) {
            order.Ticket = OrderParser.getInt(elOrder, "ticket", 0);
            order.Type = OrderParser.getByteFromInt(elOrder, "type", 0);
            order.OriginalType = OrderParser.getByteFromInt(elOrder, "originalType", 0);
            order.Size = OrderParser.getFloat(elOrder, "volume", 0.0f);
            order.OpenPrice = OrderParser.getFloat(elOrder, "openPrice", 0.0f);
            order.ClosePrice = OrderParser.getFloat(elOrder, "closePrice", 0.0f);
            order.StopLoss = OrderParser.getFloat(elOrder, "stoploss", 0.0f);
            order.TakeProfit = OrderParser.getFloat(elOrder, "takeprofit", 0.0f);
            order.OpenTime = OrderParser.getLong(elOrder, "openTime", 0);
            order.CloseTime = OrderParser.getLong(elOrder, "closeTime", 0);
            order.CloseType = OrderParser.getByteFromInt(elOrder, "closeType", 0);
            order.BarsInTrade = OrderParser.getShortFromInt(elOrder, "barsInTrade", 0);
            order.PL = OrderParser.getFloat(elOrder, "pl", 0.0f);
            order.SampleType = OrderParser.setSampleType(OrderParser.getBool(elOrder, "outOfSample", false), OrderParser.getBool(elOrder, "inSampleValidation", false));
            order.MAE = OrderParser.getFloat(elOrder, "mae", 0.0f);
            order.MFE = OrderParser.getFloat(elOrder, "mfe", 0.0f);
        } else {
            order.Ticket = OrderParser.getInt(elOrder, "ticket", 0);
            order.Type = OrderParser.getByte(elOrder, "type", 0);
            order.OriginalType = OrderParser.getByte(elOrder, "originalType", 0);
            order.Size = OrderParser.getFloat(elOrder, "volume", 0.0f);
            order.OpenPrice = OrderParser.getFloat(elOrder, "openPrice", 0.0f);
            order.ClosePrice = OrderParser.getFloat(elOrder, "closePrice", 0.0f);
            order.StopLoss = OrderParser.getFloat(elOrder, "stoploss", 0.0f);
            order.TakeProfit = OrderParser.getFloat(elOrder, "takeprofit", 0.0f);
            order.OpenTime = OrderParser.getLong(elOrder, "openTime", 0);
            order.CloseTime = OrderParser.getLong(elOrder, "closeTime", 0);
            order.CloseType = OrderParser.getByte(elOrder, "closeType", 0);
            order.BarsInTrade = OrderParser.getShort(elOrder, "barsInTrade", 0);
            order.PL = OrderParser.getFloat(elOrder, "pl", 0.0f);
            order.SampleType = OrderParser.setSampleType(OrderParser.getBool(elOrder, "outOfSample", false), OrderParser.getBool(elOrder, "inSampleValidation", false));
            order.MAE = OrderParser.getFloat(elOrder, "mae", 0.0f);
            order.MFE = OrderParser.getFloat(elOrder, "mfe", 0.0f);
            order.DD = OrderParser.getFloat(elOrder, "dd", 0.0f);
            order.PctDD = OrderParser.getFloat(elOrder, "pctDD", 0.0f);
            order.PipsDD = OrderParser.getFloat(elOrder, "pipsDD", 0.0f);
            order.CommSwap = -OrderParser.getFloat(elOrder, "commSwap", 0.0f);
        }
        int timeSec = new SQTimeOld().getDateTime();
        if (order.OpenTime < (long)timeSec) {
            order.OpenTime *= 1000L;
        }
        if (order.CloseTime < (long)timeSec) {
            order.CloseTime *= 1000L;
        }
        order.Duration = order.CloseType == 0 || order.CloseType == 6 || order.CloseType == 9 || order.CloseType == 8 ? 0 : (int)((timeInTrade = (order.CloseTime - order.OpenTime) / 1000L) < Integer.MAX_VALUE ? timeInTrade : Integer.MAX_VALUE);
        return order;
    }

    private static byte setSampleType(boolean oos, boolean isv) {
        if (oos) {
            return 20;
        }
        return 10;
    }

    public static short getShortFromInt(Element elValues, String name, int defaultValue) {
        return (short)OrderParser.getInt(elValues, name, defaultValue);
    }

    public static byte getByteFromInt(Element elValues, String name, int defaultValue) {
        return (byte)OrderParser.getInt(elValues, name, defaultValue);
    }

    public static short getShort(Element elValues, String name, int defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return (short)defaultValue;
        }
        return Short.parseShort(el.getValue());
    }

    public static byte getByte(Element elValues, String name, int defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return (byte)defaultValue;
        }
        return Byte.parseByte(el.getValue());
    }

    public static int getInt(Element elValues, String name, int defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return defaultValue;
        }
        return Integer.parseInt(el.getValue());
    }

    public static long getLong(Element elValues, String name, int defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return defaultValue;
        }
        return Long.parseLong(el.getValue());
    }

    public static float getFloat(Element elValues, String name, float defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return defaultValue;
        }
        return Float.parseFloat(el.getValue());
    }

    public static double getDouble(Element elValues, String name, float defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return defaultValue;
        }
        return Double.parseDouble(el.getValue());
    }

    public static boolean getBool(Element elValues, String name, boolean defaultValue) {
        Element el = elValues.getChild(name);
        if (el == null) {
            return defaultValue;
        }
        return Boolean.parseBoolean(el.getValue());
    }
}

