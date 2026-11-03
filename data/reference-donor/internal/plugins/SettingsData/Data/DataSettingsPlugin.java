/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.strategy.OutOfSample
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import java.io.Serializable;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Data servlet plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class DataSettingsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(DataSettingsPlugin.class);

    public Handler getHandler() {
        return null;
    }

    public String getProduct() {
        return "SQUANTAlgoWizardAlgoWizardStandaloneBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings, ISQTask task) {
        Element elSetup;
        int i;
        Element elData = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        Element elSetups = XMLUtil.tryAddElement((Element)elData, (String)"Setups");
        String taskType = task.getType();
        int chartCount = 0;
        if (taskType.equals("Build")) {
            try {
                Element elBuildType = XMLUtil.getChildElem((Element)elSettings, (String)"WhatToBuild");
                Element elRulesComplexity = XMLUtil.getChildElem((Element)elBuildType, (String)"RulesComplexity");
                chartCount = elRulesComplexity.getChildren("Chart").size();
            }
            catch (Exception elBuildType) {
                // empty catch block
            }
        }
        List setups = elSetups.getChildren("Setup");
        for (i = 0; i < setups.size(); ++i) {
            elSetup = (Element)setups.get(i);
            int charts = elSetup.getChildren("Chart").size();
            if (chartCount == 0) {
                chartCount = charts;
                continue;
            }
            double spread = 3.0;
            try {
                spread = Double.parseDouble(elSetup.getChild("Chart").getAttributeValue("spread"));
            }
            catch (Exception e) {
                Log.error("Exception in spread", (Throwable)e);
            }
            for (int a = charts; a < chartCount; ++a) {
                Element newChart = new Element("Chart");
                newChart.setAttribute("symbol", "Same as main chart");
                newChart.setAttribute("timeframe", "H1");
                newChart.setAttribute("spread", String.valueOf(spread));
                elSetup.addContent((Content)newChart);
            }
        }
        XMLUtil.tryAddElement((Element)elData, (String)"OutOfSample");
        setups = elSetups.getChildren("Setup");
        for (i = 0; i < setups.size(); ++i) {
            elSetup = (Element)setups.get(i);
            List charts = elSetup.getChildren("Chart");
            for (int j = 0; j < charts.size(); ++j) {
                Element elChart = (Element)charts.get(j);
                this.fixChart(elChart, elSetup);
            }
        }
    }

    private void fixChart(Element elChart, Element elSetup) {
        String symbol = elChart.getAttributeValue("symbol");
        if (symbol.equals("Same as main chart")) {
            return;
        }
        try {
            List ranges;
            Element elOOS;
            Element elData;
            Element elSetups;
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (dataInfo == null) {
                ArrayList allSymbols = DataManager.list();
                if (allSymbols.size() == 0) {
                    Log.error("There are no data!");
                    return;
                }
                dataInfo = (DataInfo)allSymbols.get(0);
                elChart.setAttribute("symbol", dataInfo.symbol);
                String timeframe = elChart.getAttributeValue("timeframe");
                String finalTF = "";
                long tfMillis = TimeframeManager.getMillis((String)timeframe);
                long dataTfMillis = TimeframeManager.getMillis((String)dataInfo.timeframe);
                long h1TfMillis = TimeframeManager.getMillis((String)"H1");
                finalTF = tfMillis >= dataTfMillis ? timeframe : (h1TfMillis >= dataTfMillis ? "H1" : dataInfo.timeframe);
                elChart.setAttribute("timeframe", finalTF);
            }
            long dateFrom = XMLUtil.parseDate((String)elSetup.getAttributeValue("dateFrom"));
            long dateTo = XMLUtil.parseDate((String)elSetup.getAttributeValue("dateTo"));
            if (dateFrom == 0L || dateFrom < SQTime.correctDayStart((long)dataInfo.dateFrom)) {
                dateFrom = dataInfo.dateFrom;
                elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)dateFrom));
            }
            if (dateTo == 0L || dateTo > SQTime.correctDayEnd((long)dataInfo.dateTo) || dateFrom >= dateTo) {
                dateTo = dataInfo.dateTo;
                elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)dateTo));
            }
            if ((elSetups = elSetup.getParentElement()) != null && elSetups.getName().equals("Setups") && (elData = elSetups.getParentElement()) != null && elData.getName().equals("Data") && (elOOS = elData.getChild("OutOfSample")) != null && (ranges = elOOS.getChildren("Range")) != null && ranges.size() > 0) {
                for (int i = 0; i < ranges.size(); ++i) {
                    Element elRange = (Element)ranges.get(i);
                    long rangeDateFrom = XMLUtil.parseDate((String)elRange.getAttributeValue("dateFrom"));
                    long rangeDateTo = XMLUtil.parseDate((String)elRange.getAttributeValue("dateTo"));
                    boolean rangeModified = false;
                    if (rangeDateFrom == 0L || rangeDateFrom < dateFrom) {
                        rangeDateFrom = (long)((double)dateFrom + 0.7 * (double)(dateTo - dateFrom));
                        rangeModified = true;
                    }
                    if (rangeDateTo == 0L || rangeDateTo > dateTo) {
                        rangeDateTo = dateTo;
                        rangeModified = true;
                    }
                    if (rangeDateFrom > rangeDateTo) {
                        long temp = rangeDateFrom;
                        rangeDateFrom = rangeDateTo;
                        rangeDateTo = temp;
                        rangeModified = true;
                    }
                    if (!rangeModified) continue;
                    rangeDateFrom = SQTime.setTime((long)rangeDateFrom, (int)0, (int)0, (int)0, (int)0);
                    rangeDateTo = SQTime.setTime((long)rangeDateTo, (int)0, (int)0, (int)0, (int)0);
                    elRange.setAttribute("dateFrom", SQTime.toUIDateString((long)rangeDateFrom));
                    elRange.setAttribute("dateTo", SQTime.toUIDateString((long)rangeDateTo));
                }
            }
        }
        catch (Exception e) {
            Log.error("Error verifying date", (Throwable)e);
            e.printStackTrace();
        }
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings, task);
        Element elData = elSettings.getChild("Data");
        if (elData == null) {
            data.addError(this.getSettingName(), null, "Cannot find Data settings.");
            return;
        }
        Element elSetups = elData.getChild("Setups");
        if (elSetups == null) {
            data.addError(this.getSettingName(), null, "Cannot find Data.Setups settings.");
            return;
        }
        Element elSetup = elSetups.getChild("Setup");
        if (elSetup == null) {
            data.addError(this.getSettingName(), null, "You have to set up at least one backtest!");
            return;
        }
        ChartSetups chartSetups = new ChartSetups();
        this.checkSetup(data, elSetup, 1);
        try {
            data.addParam("Slippage", (Serializable)Double.valueOf(Double.parseDouble(elSetup.getAttributeValue("slippage"))));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot get main chart slippage value");
        }
        try {
            data.addParam("MinDistance", (Serializable)Double.valueOf(Double.parseDouble(elSetup.getAttributeValue("minDist"))));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot get main chart min distance value");
        }
        try {
            data.addParam("Commission", (Serializable)ProjectConfigHelper.getCommissionsMethod((Element)elSetup));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot get main chart commissions config");
        }
        try {
            data.addParam("Swap", (Serializable)ProjectConfigHelper.getSwapMethod((Element)elSetup));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot get main chart swap config");
        }
        try {
            chartSetups = ProjectConfigHelper.getChartSetups((Element)elData);
            data.addParam("ChartSetups", (Serializable)chartSetups);
        }
        catch (Exception e) {
            Log.error("Exception", (Throwable)e);
            data.addError(this.getSettingName(), null, "Cannot initialize Main chart setup - " + e.getMessage());
        }
        try {
            Element elOutOfSample = XMLUtil.getChildElem((Element)elData, (String)"OutOfSample");
            OutOfSample oos = ProjectConfigHelper.getOOS((Element)elOutOfSample);
            data.addParam("OutOfSample", (Serializable)oos);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot initialize OOS periods - " + e.getMessage());
        }
    }

    private void checkSetup(TaskSettingsData data, Element elSetup, int backtestIndex) {
        if (!this.checkCommissionSettings(elSetup)) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Commissions method in %s is not set!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        if (!XMLUtil.attributeValid((Element)elSetup, (String)"slippage")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Slippage in %s is undefined!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        if (!XMLUtil.attributeValid((Element)elSetup, (String)"minDist")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Min Distance in %s is undefined!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        if (Engines.getEngine((String)elSetup.getAttributeValue("engine")) == -1) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Trading engine in %s is undefined!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        long dateFrom = this.checkDate(data, elSetup.getAttributeValue("dateFrom"), "Date From", backtestIndex);
        long dateTo = this.checkDate(data, elSetup.getAttributeValue("dateTo"), "Date To", backtestIndex);
        if (dateFrom > 0L && dateTo > 0L && dateFrom > dateTo) {
            data.addError(this.getSettingName(backtestIndex), null, String.format(L.t((String)"Date from must be before Date to.", (Object[])new Object[0]), DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        Element elMainChart = (Element)elSetup.getChildren().get(0);
        String mainTF = elMainChart.getAttributeValue("timeframe");
        String mainSymbol = elMainChart.getAttributeValue("symbol");
        String testPrecision = elSetup.getAttributeValue("testPrecision");
        try {
            int precision = Precisions.getPrecision((int)Integer.parseInt(testPrecision));
            if (precision == 5 && TimeframeManager.getMillis((String)mainTF) < TimeframeManager.getMillis((String)"M1")) {
                data.addError(this.getSettingName(backtestIndex), null, String.format("Incorrect timeframe used in %s! Timeframe M1 or higher must be selected for On Bar Open precision.", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Precision in %s is undefined!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        int j = 0;
        IntOpenHashSet chartsSet = new IntOpenHashSet();
        for (Element elChart : elSetup.getChildren("Chart")) {
            int hash = this.checkChart(data, elChart, backtestIndex, ++j, mainSymbol, mainTF, elSetup);
            if (chartsSet.contains(hash)) {
                data.addError(this.getSettingName(backtestIndex), null, String.format("You cannot have duplicate subcharts!", DataSettingsPlugin.getBacktestLabel(backtestIndex)));
                continue;
            }
            chartsSet.add(hash);
        }
    }

    private boolean checkCommissionSettings(Element elSetup) {
        try {
            Element elCommissions = elSetup.getChild("Commissions");
            List commissionMethods = elCommissions.getChildren("Method");
            if (commissionMethods.size() == 1) {
                return true;
            }
            for (Element elMethod : elCommissions.getChildren("Method")) {
                if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) continue;
                return true;
            }
            return false;
        }
        catch (Exception e) {
            return XMLUtil.attributeValid((Element)elSetup, (String)"commissions");
        }
    }

    private int checkChart(TaskSettingsData data, Element elChart, int backtestIndex, int chartIndex, String mainSymbol, String mainTF, Element elSetup) {
        String chartName;
        String string = chartName = chartIndex > 1 ? "Subchart " + (chartIndex - 1) : "Main Chart";
        if (!XMLUtil.attributeValid((Element)elChart, (String)"symbol")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Symbol in %s in %s is undefined!", chartName, DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        if (!XMLUtil.attributeValid((Element)elChart, (String)"timeframe")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Timeframe in %s in %s is undefined!", chartName, DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        if (!XMLUtil.attributeValid((Element)elChart, (String)"spread")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("Spread in %s in %s is undefined!", chartName, DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        }
        String symbol = elChart.getAttributeValue("symbol");
        String tf = elChart.getAttributeValue("timeframe");
        if (chartIndex <= 1 || !symbol.equals(mainSymbol) && !symbol.equals("Same as main chart") || tf.equals(mainTF)) {
            // empty if block
        }
        return symbol.hashCode() + tf.hashCode();
    }

    private long checkDate(TaskSettingsData data, String value, String label, int backtestIndex) {
        if (value == null || value.equals("") || value.equals("undefined")) {
            data.addError(this.getSettingName(backtestIndex), null, String.format("%s in %s is undefined!", label, DataSettingsPlugin.getBacktestLabel(backtestIndex)));
        } else {
            try {
                return SQTime.parseDateToMilis((String)value);
            }
            catch (ParseException e) {
                data.addError(this.getSettingName(backtestIndex), null, String.format("%s in %s has incorrect value'%s'!", label, DataSettingsPlugin.getBacktestLabel(backtestIndex), value));
            }
        }
        return -1L;
    }

    private String getSettingName(int backtestIndex) {
        return this.getSettingName();
    }

    private static String getBacktestLabel(int index) {
        if (index == 1) {
            return "Main backtest";
        }
        return String.format("Additional Backtest %d", index - 1);
    }

    public String getSettingName() {
        return "Data";
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        List ranges;
        int i;
        if (elSettings == null) {
            return;
        }
        Element elData = elSettings.getChild("Data");
        if (elData == null) {
            return;
        }
        Element elSetups = elData.getChild("Setups");
        if (elSetups == null) {
            return;
        }
        Element elSetup = elSetups.getChild("Setup");
        if (elSetup == null) {
            return;
        }
        Element elChart = elSetup.getChild("Chart");
        if (elChart == null) {
            return;
        }
        String engine = elSetup.getAttributeValue("engine");
        String symbol = elChart.getAttributeValue("symbol");
        String timeframe = elChart.getAttributeValue("timeframe");
        String spread = elChart.getAttributeValue("spread");
        String dateFrom = elSetup.getAttributeValue("dateFrom");
        String dateTo = elSetup.getAttributeValue("dateTo");
        String precision = elSetup.getAttributeValue("testPrecision");
        String slippage = elSetup.getAttributeValue("slippage");
        String minDistance = elSetup.getAttributeValue("minDist");
        try {
            dateFrom = SQTime.toUIDateString((long)SQTime.parseDateToMilis((String)dateFrom));
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            dateTo = SQTime.toUIDateString((long)SQTime.parseDateToMilis((String)dateTo));
        }
        catch (Exception exception) {
            // empty catch block
        }
        String commission = null;
        String swap = null;
        try {
            commission = ProjectConfigHelper.getCommissionsMethod((Element)elSetup).printFormatedName();
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            swap = ProjectConfigHelper.getSwapMethod((Element)elSetup).printFormatedName();
        }
        catch (Exception exception) {
            // empty catch block
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Engine").put("value", (Object)(engine != null ? engine : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Symbol").put("value", (Object)(symbol != null ? symbol : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Timeframe").put("value", (Object)(timeframe != null ? timeframe : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Start date").put("value", (Object)(dateFrom != null ? dateFrom : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"End date").put("value", (Object)(dateTo != null ? dateTo : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Test precision").put("value", (Object)(precision != null ? Precisions.toString((int)Integer.parseInt(precision)) : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Spread").put("value", (Object)(spread != null ? spread : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Slippage ").put("value", (Object)(slippage != null ? slippage : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Min distance ").put("value", (Object)(minDistance != null ? minDistance : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Commission").put("value", (Object)(commission != null ? commission : "N/A")));
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Swap").put("value", (Object)(swap != null ? swap : "N/A")));
        JSONArray instruments = new JSONArray();
        ArrayList<String> allSymbols = new ArrayList<String>();
        allSymbols.add(symbol);
        String subcharts = "None";
        List subchartEls = elSetup.getChildren("Chart");
        if (subchartEls.size() > 1) {
            subcharts = "";
            for (i = 1; i < subchartEls.size(); ++i) {
                String subchartSymbol = ((Element)subchartEls.get(i)).getAttributeValue("symbol");
                subcharts = subcharts + String.format("Subcharts (%d): ", i);
                subcharts = subcharts + String.format("%s, %s", subchartSymbol, ((Element)subchartEls.get(i)).getAttributeValue("timeframe"));
                subcharts = subcharts + "\n";
                if (subchartSymbol == null || subchartSymbol.equals("Same as main chart")) continue;
                allSymbols.add(subchartSymbol);
            }
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Subcharts").put("value", (Object)subcharts));
        for (int a = 0; a < allSymbols.size(); ++a) {
            instruments.put((Object)new JSONObject().put("key", (Object)("Instrument " + (String)allSymbols.get(a))).put("value", (Object)"N/A"));
        }
        try {
            for (i = 0; i < instruments.length(); ++i) {
                JSONObject instrumentInfo = instruments.getJSONObject(i);
                String symbolName = instrumentInfo.getString("key").replace("Instrument ", "");
                DataInfo info = DataManager.getDataInfo((String)"History", (String)symbolName);
                if (info == null) continue;
                instrumentInfo.put("value", (Object)this.getInstrumentInfo(info.barTimeType, info.timezone));
            }
        }
        catch (Exception i2) {
            // empty catch block
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Instruments").put("value", (Object)instruments));
        String dataRanges = "None";
        Element elOOS = elData.getChild("OutOfSample");
        if (elOOS != null && (ranges = elOOS.getChildren("Range")).size() > 0) {
            dataRanges = "";
            int[] indexes = new int[]{0, 0, 0};
            for (int i3 = 0; i3 < ranges.size(); ++i3) {
                Element elRange = (Element)ranges.get(i3);
                long rangeDateFrom = XMLUtil.parseDate((String)elRange.getAttributeValue("dateFrom"));
                long rangeDateTo = XMLUtil.parseDate((String)elRange.getAttributeValue("dateTo"));
                String type = XMLUtil.getStringAttr((Element)elRange, (String)"type", (String)"oos");
                if (type.equals("isv")) {
                    indexes[0] = indexes[0] + 1;
                    dataRanges = dataRanges + String.format("ISV%d: ", indexes[0]);
                } else if (type.equals("oos")) {
                    indexes[1] = indexes[1] + 1;
                    dataRanges = dataRanges + String.format("OOS%d: ", indexes[1]);
                } else {
                    if (!type.equals("notrade")) continue;
                    indexes[2] = indexes[2] + 1;
                    dataRanges = dataRanges + String.format("NoTrade%d: ", indexes[2]);
                }
                dataRanges = dataRanges + String.format("%s - %s", SQTime.toString((long)rangeDateFrom, (String)"yyyy.MM.dd"), SQTime.toString((long)rangeDateTo, (String)"yyyy.MM.dd"));
                dataRanges = dataRanges + "\n";
            }
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Data ranges").put("value", (Object)dataRanges));
    }

    private String getInstrumentInfo(int barType, String timezone) {
        String info = barType == 2 ? "End of bar" : "Start of bar";
        info = info + " | " + timezone;
        return info;
    }

    public String getName() {
        return L.tsq((String)"Data");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

