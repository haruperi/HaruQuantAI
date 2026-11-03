/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.TimePeriod
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.miniequitychart;

import com.strategyquant.lib.TimePeriod;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.ChartOptimalizer;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.Periods;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MiniEquityChartComputer {
    private static final Logger Log = LoggerFactory.getLogger((String)"MiniEquityChartComputer");
    private static final String KEY_ST_FULL = "MEC_FULL_";
    private static final String KEY_ST_IS = "MEC_IS_";
    private static final String KEY_ST_OOS = "MEC_OOS_";

    public static String getValue(ResultsGroup resultsGroup, String string, byte by) throws Exception {
        return MiniEquityChartComputer.getValue(resultsGroup, string, by, 50);
    }

    public static String getValue(ResultsGroup resultsGroup, String string, byte by, int n) throws Exception {
        String string2 = MiniEquityChartComputer.getSpecialValuesKey(resultsGroup, string, by);
        if (resultsGroup.specialValues().containsKey(string2)) {
            return resultsGroup.specialValues().getString(string2);
        }
        String string3 = MiniEquityChartComputer.computeMiniEquity(resultsGroup, string, by, n);
        resultsGroup.specialValues().setString(string2, string3);
        resultsGroup.updated = true;
        return string3;
    }

    public static void computeForResult(ResultsGroup resultsGroup, String string) throws Exception {
        String string2;
        String string3 = MiniEquityChartComputer.getSpecialValuesKey(resultsGroup, string, (byte)127);
        if (!resultsGroup.specialValues().containsKey(string3)) {
            string2 = MiniEquityChartComputer.computeMiniEquity(resultsGroup, string, (byte)127);
            resultsGroup.specialValues().setString(string3, string2);
        }
        string3 = MiniEquityChartComputer.getSpecialValuesKey(resultsGroup, string, (byte)10);
        if (!resultsGroup.specialValues().containsKey(string3)) {
            string2 = MiniEquityChartComputer.computeMiniEquity(resultsGroup, string, (byte)10);
            resultsGroup.specialValues().setString(string3, string2);
        }
        string3 = MiniEquityChartComputer.getSpecialValuesKey(resultsGroup, string, (byte)20);
        if (!resultsGroup.specialValues().containsKey(string3)) {
            string2 = MiniEquityChartComputer.computeMiniEquity(resultsGroup, string, (byte)20);
            resultsGroup.specialValues().setString(string3, string2);
        }
    }

    public static String getSpecialValuesKey(ResultsGroup resultsGroup, String string, byte by) {
        StringBuilder stringBuilder = new StringBuilder();
        string = MiniEquityChartComputer.getResultKey(resultsGroup, string);
        string = MiniEquityChartComputer.correctResultKey(string);
        if (by == 10) {
            stringBuilder.append(KEY_ST_IS);
        } else if (by == 20) {
            stringBuilder.append(KEY_ST_OOS);
        } else {
            stringBuilder.append(KEY_ST_FULL);
        }
        stringBuilder.append(string);
        return stringBuilder.toString();
    }

    public static String computeMiniEquity(ResultsGroup resultsGroup, String string, byte by) {
        return MiniEquityChartComputer.computeMiniEquity(resultsGroup, string, by, 50);
    }

    public static String computeMiniEquity(ResultsGroup resultsGroup, String string, byte by, int n) {
        try {
            int n2;
            OrdersList ordersList = resultsGroup.orders().filter(string, (byte)0, by, true);
            MainChartDataset mainChartDataset = EquityChartUtils.generateTradeDataset(ordersList);
            ChartOptimalizer.OptimizerResult optimizerResult = new ChartOptimalizer().optimalize(false, mainChartDataset.xVals, mainChartDataset.yVals, 0L, (long)mainChartDataset.xVals.length - 1L, n < 0 ? ordersList.size() : n);
            int[] nArray = new int[optimizerResult.yVals.length];
            double d = Double.MAX_VALUE;
            double d2 = -1.7976931348623157E308;
            int n3 = 17;
            for (n2 = 0; n2 < optimizerResult.size(); ++n2) {
                if (optimizerResult.yVals[n2] < d) {
                    d = optimizerResult.yVals[n2];
                }
                if (!(optimizerResult.yVals[n2] > d2)) continue;
                d2 = optimizerResult.yVals[n2];
            }
            for (n2 = 0; n2 < optimizerResult.size(); ++n2) {
                nArray[n2] = MiniEquityChartComputer.map(optimizerResult.yVals[n2], d, d2, 0.0, n3);
            }
            n2 = 0;
            if (d < 0.0) {
                n2 = nArray.length > 0 ? MiniEquityChartComputer.map(0.0, d, d2, 0.0, n3) : 0;
            }
            JSONObject jSONObject = new JSONObject();
            JSONArray jSONArray = new JSONArray();
            for (int i = 0; i < nArray.length; ++i) {
                jSONArray.put(nArray[i]);
            }
            jSONObject.put("values", (Object)jSONArray);
            if (by == 127 || by == 10) {
                int n4;
                JSONArray jSONArray2;
                Periods periods = new Periods();
                List<TimePeriod> list = periods.getAvailablePeriods(ordersList, "trade");
                int[][] nArray2 = by == 127 ? MiniEquityChartComputer.getSampleMarkersByType(periods.filter(list, (byte)20), ordersList, optimizerResult) : null;
                int[][] nArray3 = MiniEquityChartComputer.getSampleMarkersByType(periods.filter(list, (byte)40), ordersList, optimizerResult);
                if (nArray2 != null && nArray2.length > 0) {
                    jSONArray2 = new JSONArray();
                    for (n4 = 0; n4 < nArray2.length; ++n4) {
                        jSONArray2.put((Object)new JSONArray().put(nArray2[n4][0]).put(nArray2[n4][1]));
                    }
                    jSONObject.put("oos", (Object)jSONArray2);
                }
                if (nArray3 != null && nArray3.length > 0) {
                    jSONArray2 = new JSONArray();
                    for (n4 = 0; n4 < nArray3.length; ++n4) {
                        jSONArray2.put((Object)new JSONArray().put(nArray3[n4][0]).put(nArray3[n4][1]));
                    }
                    jSONObject.put("isv", (Object)jSONArray2);
                }
            }
            jSONObject.put("zeroPoint", n2);
            return "{{sparklinesWidget data='" + jSONObject.toString() + "'}}";
        }
        catch (Exception exception) {
            Log.error("Cannot compute mini equity chart", (Throwable)exception);
            return "";
        }
    }

    public static String correctResultKey(String string) {
        return string.replaceAll("[^\\dA-Za-z ]", "__").replaceAll("\\s+", "_");
    }

    private static String getResultKey(ResultsGroup resultsGroup, String string) {
        try {
            if (string.equals(resultsGroup.getMainResultKey()) || string.equals("Portfolio") && resultsGroup.mainResult().get("WalkForwardResult") != null) {
                return "Main";
            }
        }
        catch (Exception exception) {
            Log.error("Cannot correct resultkey", (Throwable)exception);
        }
        return string;
    }

    private static int[][] getSampleMarkersByType(List<TimePeriod> list, OrdersList ordersList, ChartOptimalizer.OptimizerResult optimizerResult) throws Exception {
        int[][] nArray = null;
        if (list.size() > 0) {
            nArray = new int[list.size()][2];
            for (int i = 0; i < list.size(); ++i) {
                TimePeriod timePeriod = list.get(i);
                nArray[i][0] = -1;
                nArray[i][1] = -1;
                for (int j = 0; j < optimizerResult.size(); ++j) {
                    if (nArray[i][0] == -1 && timePeriod.from <= optimizerResult.xVals[j]) {
                        nArray[i][0] = j;
                    }
                    if (nArray[i][1] != -1 || timePeriod.to > optimizerResult.xVals[j]) continue;
                    nArray[i][1] = j;
                }
            }
            if (nArray[list.size() - 1][1] == -1) {
                nArray[list.size() - 1][1] = optimizerResult.size() - 1;
            }
        }
        return nArray;
    }

    public static int map(double d, double d2, double d3, double d4, double d5) {
        return new Double((d - d2) * (d5 - d4) / (d3 - d2) + d4).intValue();
    }
}

