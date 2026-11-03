/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  org.apache.commons.lang3.text.StrSubstitutor
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.debug.Debugger;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime;
import java.io.File;
import java.text.DecimalFormat;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;
import org.apache.commons.lang3.text.StrSubstitutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class OverviewTemplate
extends Debugger {
    public static final Logger Log = LoggerFactory.getLogger(OverviewTemplate.class);
    private static DecimalFormat d2Format = new DecimalFormat("#.##");
    private String name = "?";
    private String screenshotName = null;
    protected String htmlTemplateName = null;
    private Map<String, String> valuesMap = new HashMap<String, String>();
    protected static final Comparator<Order> ComparatorByCloseTime = new OrderComparatorByCloseTime();
    protected static String NA = "N/A";
    protected String template;
    protected String templateOrig;

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getScreenshotName() {
        return this.screenshotName;
    }

    public void setScreenshotName(String string) {
        this.screenshotName = string;
    }

    public String getHtmlTemplateName() {
        return this.htmlTemplateName;
    }

    public void setHtmlTemplateName(String string) {
        this.htmlTemplateName = string;
    }

    public String toString() {
        return this.name;
    }

    public abstract String drawValues(ResultsGroup var1, String var2, StatsTypeCombination var3) throws Exception;

    public void loadTemplate() throws Exception {
        try {
            String string = MainApp.getDataPath() + "internal/plugins/ResultsOverview/templates/" + this.htmlTemplateName;
            this.templateOrig = SQUtils.fileToString((File)new File(string));
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            throw new Exception("Unable to read template file.");
        }
    }

    public void reset() {
        this.valuesMap.clear();
        this.template = this.templateOrig;
    }

    public String print() {
        this.template = this.template.replaceAll(Pattern.quote("${Label_Stats}"), L.t((String)"Stats", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_Strategy}"), L.t((String)"Strategy", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_Trades}"), L.t((String)"Trades", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_Performance_summary}"), L.t((String)"Performance summary", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_All_trades}"), L.t((String)"All trades", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_Long_trades}"), L.t((String)"Long trades", (Object[])new Object[0]));
        this.template = this.template.replaceAll(Pattern.quote("${Label_Short_trades}"), L.t((String)"Short trades", (Object[])new Object[0]));
        return StrSubstitutor.replace((Object)this.template, this.valuesMap);
    }

    public String d2WithPlType(Double d, byte by) {
        String string = this.d2(d);
        switch (by) {
            case 30: {
                return string + " ticks";
            }
            case 10: {
                return "$ " + string;
            }
            case 20: {
                return string + " %";
            }
        }
        return by == 0 ? string : string + " " + by;
    }

    public String d2(Double d) {
        return d2Format.format(d);
    }

    protected void replace(String string, String string2, String string3) {
        this.replace(string, string2, string3, null);
    }

    protected void replace(String string, String string2, String string3, String string4) {
        if (string4 != null) {
            this.valuesMap.put("Class_" + string, string4);
        }
        this.valuesMap.put("Label_" + string, string2);
        this.valuesMap.put("Value_" + string, string3);
    }

    protected void replaceLabel(String string, String string2) {
        this.valuesMap.put("Label_" + string, L.tsq((String)string2));
    }

    protected void replaceValue(String string, String string2) {
        this.replaceValue(string, string2, null);
    }

    protected void replaceValue(String string, String string2, String string3) {
        if (string3 != null) {
            this.valuesMap.put("Class_" + string, string3);
        }
        this.valuesMap.put("Value_" + string, string2);
    }
}

