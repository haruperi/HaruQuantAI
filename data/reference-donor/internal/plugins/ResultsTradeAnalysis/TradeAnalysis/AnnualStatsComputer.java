/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  org.json.JSONArray
 */
package com.strategyquant.plugin.Results.impl.TradeAnalysis;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import java.text.DecimalFormat;
import org.json.JSONArray;

public class AnnualStatsComputer {
    public static final int YEAR_ALL = 0;
    public DecimalFormat twoDFormat = new DecimalFormat("0.00");

    public JSONArray compute(int year, OrdersList orders, byte plType, byte tradePeriod) {
        JSONArray data = new JSONArray();
        int numTrades = 0;
        double netProfit = 0.0;
        double sumProfits = 0.0;
        double sumLosses = 0.0;
        double profitFactor = 0.0;
        int countProfits = 0;
        int countLosses = 0;
        double pctWins = 0.0;
        double pl = 0.0;
        for (int i = 0; i < orders.size(); ++i) {
            Order order = orders.get(i);
            long time = order.getTimeByPeriodType(tradePeriod);
            if (year != 0 && SQTime.getFullYear((long)time) != year) continue;
            ++numTrades;
            pl = order.getPLByType(plType);
            netProfit += pl;
            if (pl > 0.0) {
                ++countProfits;
                sumProfits += Math.abs(pl);
                continue;
            }
            if (!(pl < 0.0)) continue;
            ++countLosses;
            sumLosses += Math.abs(pl);
        }
        pctWins = numTrades == 0 ? 0.0 : SQUtils.safeDivide((double)countProfits, (double)(countProfits + countLosses)) * 100.0;
        if (numTrades == 0) {
            profitFactor = 0.0;
        }
        if (sumProfits == 0.0) {
            profitFactor = 0.0;
        }
        profitFactor = sumLosses == 0.0 ? (numTrades > 10 ? 5.0 : 0.0) : sumProfits / sumLosses;
        data.put(year == 0 ? "All" : Integer.valueOf(year));
        data.put((Object)PlTypes.printPL((double)netProfit, (byte)plType));
        data.put((Object)SQUtils.d2((double)profitFactor));
        data.put(numTrades);
        data.put((Object)PlTypes.printPL((double)pctWins, (byte)20));
        return data;
    }
}

