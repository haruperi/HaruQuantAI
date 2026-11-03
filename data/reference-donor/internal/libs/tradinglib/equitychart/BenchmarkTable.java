/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import org.json.JSONObject;

public class BenchmarkTable {
    public String MoneyManagement;
    public double InitialCapital;
    public String Symbol;
    public String Normalization;
    public String InitBuyAmount;
    public SQStats StatsStrategy;
    public SQStats StatsBenchmark;
    public SQStats StatsBenchmarkDDPct;
    public double Correlation;

    public String toJSON() {
        if (this.StatsStrategy == null) {
            return new JSONObject().toString();
        }
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("normalization", (Object)this.Normalization);
        jSONObject.put("moneyManagement", (Object)this.MoneyManagement);
        jSONObject.put("initialCapital", (Object)PlTypes.printPL(this.InitialCapital, (byte)10));
        jSONObject.put("symbol", (Object)this.Symbol);
        jSONObject.put("initBuyAmount", (Object)this.InitBuyAmount);
        double d = this.StatsStrategy.getDouble("NetProfit");
        double d2 = this.StatsBenchmarkDDPct.getDouble("NetProfit");
        jSONObject.put("result", (Object)(d > d2 ? L.tsq((String)"better") : L.tsq((String)"worse")));
        JSONObject jSONObject2 = new JSONObject();
        jSONObject2.put("NetProfit", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("NetProfit")));
        jSONObject2.put("NumberOfTrades", this.StatsStrategy.getInt("NumberOfTrades"));
        jSONObject2.put("Drawdown", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("Drawdown")));
        jSONObject2.put("DrawdownPct", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("DrawdownPct")));
        jSONObject2.put("ProfitFactor", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("ProfitFactor")));
        jSONObject2.put("SharpeRatio", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("SharpeRatio")));
        jSONObject2.put("ReturnDDRatio", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("ReturnDDRatio")));
        jSONObject2.put("AvgTrade", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("AvgTrade")));
        jSONObject2.put("CAGR", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("CAGR")));
        jSONObject2.put("AnnualPctReturnDDRatio", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("AnnualPctReturnDDRatio")));
        jSONObject2.put("Exposure", (Object)SQUtils.d2((double)this.StatsStrategy.getDouble("Exposure")));
        jSONObject2.put("Correlation", (Object)SQUtils.d2((double)this.Correlation));
        JSONObject jSONObject3 = new JSONObject();
        jSONObject3.put("NetProfit", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("NetProfit")));
        jSONObject3.put("NumberOfTrades", 1);
        jSONObject3.put("Drawdown", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("Drawdown")));
        jSONObject3.put("DrawdownPct", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("DrawdownPct")));
        jSONObject3.put("ProfitFactor", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("ProfitFactor")));
        jSONObject3.put("SharpeRatio", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("SharpeRatio")));
        jSONObject3.put("ReturnDDRatio", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("ReturnDDRatio")));
        jSONObject3.put("AvgTrade", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("AvgTrade")));
        jSONObject3.put("CAGR", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("CAGR")));
        jSONObject3.put("AnnualPctReturnDDRatio", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("AnnualPctReturnDDRatio")));
        if (this.Normalization.equals("exposure")) {
            jSONObject3.put("Exposure", (Object)SQUtils.d2((double)this.StatsBenchmark.getDouble("Exposure", 1.0)));
        } else {
            jSONObject3.put("Exposure", 100);
        }
        JSONObject jSONObject4 = new JSONObject();
        jSONObject4.put("NetProfit", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("NetProfit")));
        jSONObject4.put("Drawdown", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("Drawdown")));
        jSONObject4.put("DrawdownPct", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("DrawdownPct")));
        jSONObject4.put("SharpeRatio", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("SharpeRatio")));
        jSONObject4.put("CAGR", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("CAGR")));
        jSONObject4.put("AnnualPctReturnDDRatio", (Object)SQUtils.d2((double)this.StatsBenchmarkDDPct.getDouble("AnnualPctReturnDDRatio")));
        JSONObject jSONObject5 = new JSONObject();
        jSONObject5.put("strategy", (Object)jSONObject2);
        jSONObject5.put("benchmark", (Object)jSONObject3);
        jSONObject5.put("benchmarkDD", (Object)jSONObject4);
        jSONObject.put("stats", (Object)jSONObject5);
        return jSONObject.toString();
    }

    public void clear() {
        this.MoneyManagement = null;
        this.InitialCapital = 0.0;
        this.Symbol = null;
        this.InitBuyAmount = null;
        this.StatsStrategy = null;
        this.StatsBenchmark = null;
        this.StatsBenchmarkDDPct = null;
    }

    public void fill(ResultsGroup resultsGroup, MoneyManagementMethod moneyManagementMethod, String string, SQStats sQStats, double d, String string2, double d2, SQStats sQStats2, SQStats sQStats3) throws Exception {
        this.MoneyManagement = moneyManagementMethod.printFormatedName();
        this.InitialCapital = moneyManagementMethod.getInitialCapital();
        this.Symbol = string = string.replace("_benchmark.D", "");
        this.Normalization = string2;
        this.InitBuyAmount = PlTypes.printPL(d2, (byte)10);
        this.Correlation = d;
        this.StatsStrategy = sQStats;
        this.StatsBenchmark = sQStats2;
        this.StatsBenchmarkDDPct = sQStats3;
    }
}

