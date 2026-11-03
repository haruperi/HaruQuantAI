/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.bestresults;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import java.io.File;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BestResultOverview {
    public static final Logger Log = LoggerFactory.getLogger(BestResultOverview.class);
    private static String template = null;

    public String print(ResultsGroup resultsGroup, byte by) {
        String string = null;
        try {
            string = this.loadTemplate();
            boolean bl = resultsGroup.isStockpickerStrategy();
            if (bl) {
                template = template.replaceAll("StatsMoney.ReturnDDRatio", "StatsMoney.ReturnOpenDDRatio");
                template = template.replaceAll("StatsMoney.Drawdown", "StatsMoney.OpenDrawdown");
                template = template.replaceAll("StatsPct.DrawdownPct", "StatsPct.OpenDrawdownPct");
            }
            SQStats sQStats = resultsGroup.portfolio().stats((byte)0, (byte)10, by);
            String string2 = null;
            for (DatabankColumn databankColumn : DatabankColumns.get().getAvailableClasses()) {
                try {
                    double d = databankColumn.getNumericValue(sQStats);
                    String string3 = string2 = d >= 0.0 ? "positiveNum" : "negativeNum";
                    if (databankColumn.getClass().getSimpleName().equals("Drawdown") || databankColumn.getClass().getSimpleName().equals("DrawdownPct") || databankColumn.getClass().getSimpleName().equals("OpenDrawdown") || databankColumn.getClass().getSimpleName().equals("OpenDrawdownPct")) {
                        string2 = "negativeNum";
                    }
                    string = string.replace("{{StatsMoney." + databankColumn.getClass().getSimpleName() + "}}", "<span class=\"" + string2 + "\">" + databankColumn.printPlValue(sQStats, (byte)10) + "</span>");
                    string = string.replace("{StatsMoney." + databankColumn.getClass().getSimpleName() + "}", databankColumn.printPlValue(sQStats, (byte)10));
                }
                catch (NullPointerException nullPointerException) {
                }
                catch (Exception exception) {
                    Log.error("Exc. Column " + databankColumn.getClass().getSimpleName(), (Throwable)exception);
                }
            }
            string = string.replaceAll(Pattern.quote("${Label_1}"), L.t((String)"TOTAL PROFIT", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_2}"), L.t((String)"YEARLY AVG PROFIT", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_3}"), L.t((String)"YEARLY AVG % RETURN", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_4}"), L.t((String)"CAGR", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_5}"), L.t((String)"# OF TRADES", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_6}"), L.t((String)"SHARPE RATIO", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_7}"), L.t((String)"PROFIT FACTOR", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_8}"), bl ? L.t((String)"RETURN / OPEN DD RATIO", (Object[])new Object[0]) : L.t((String)"RETURN / DD RATIO", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_9}"), L.t((String)"WINNING PERCENTAGE", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_10}"), bl ? L.t((String)"OPEN DRAWDOWN", (Object[])new Object[0]) : L.t((String)"DRAWDOWN", (Object[])new Object[0]));
            string = string.replaceAll(Pattern.quote("${Label_11}"), bl ? L.t((String)"OPEN % DRAWDOWN", (Object[])new Object[0]) : L.t((String)"% DRAWDOWN", (Object[])new Object[0]));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return string != null ? string : "";
    }

    private String loadTemplate() throws Exception {
        if (template == null) {
            try {
                String string = MainApp.getDataPath() + "/user/settings/ResultsDashboard/template.html";
                template = SQUtils.fileToString((File)new File(string));
                template = template.replaceAll("StatsPct.AnnualPctReturn", "StatsMoney.AvgPctProfitPerYear");
                template = template.replaceAll("StatsPct", "StatsMoney");
                template = template.replaceAll("StatsPips", "StatsMoney");
                return template;
            }
            catch (Exception exception) {
                Log.error("Exc. Cannot load template file.", (Throwable)exception);
                throw new Exception("Cannot load template file.");
            }
        }
        return template;
    }
}

