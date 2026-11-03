/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.generator.StrategyTemplateGenerator
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.task.settings.buildmode.BuildMode
 *  com.strategyquant.tradinglib.task.settings.buildtype.BuildType
 *  com.strategyquant.tradinglib.task.settings.buildtype.ChartSettings
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.WhatToBuild;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.task.settings.buildmode.BuildMode;
import com.strategyquant.tradinglib.task.settings.buildtype.BuildType;
import com.strategyquant.tradinglib.task.settings.buildtype.ChartSettings;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.File;
import java.io.Serializable;
import java.util.Iterator;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Build type servlet plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class WhatToBuildSettingsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(WhatToBuildSettingsPlugin.class);
    private static final String tabTitle = "What to build";
    private ServletContextHandler dataContext;
    private WhatToBuildServlet servlet;

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new WhatToBuildServlet();
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/buildType/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 5;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elBuildMode;
        Element elRulesComplexity;
        List chartElems;
        Element elWhatToBuild = XMLUtil.tryAddElement((Element)elSettings, (String)"WhatToBuild");
        Element elMarketSides = XMLUtil.tryAddElement((Element)elWhatToBuild, (String)"MarketSides");
        String marketSidesType = XMLUtil.tryGetAttr((Element)elMarketSides, (String)"type", (String)"both");
        if (marketSidesType.equals("both")) {
            Element elExitSymmetry;
            String exitSymmetry;
            Element elEntrySymmetry = XMLUtil.tryAddElement((Element)elMarketSides, (String)"EntrySymmetry");
            String entrySymmetry = elEntrySymmetry.getText();
            if (entrySymmetry == null || entrySymmetry.isEmpty()) {
                elEntrySymmetry.setText("true");
            }
            if ((exitSymmetry = (elExitSymmetry = XMLUtil.tryAddElement((Element)elMarketSides, (String)"ExitSymmetry")).getText()) == null || exitSymmetry.isEmpty()) {
                elExitSymmetry.setText("true");
            }
        }
        if ((chartElems = (elRulesComplexity = XMLUtil.tryAddElement((Element)elWhatToBuild, (String)"RulesComplexity")).getChildren("Chart")).isEmpty()) {
            Element elChart = XMLUtil.tryAddElement((Element)elRulesComplexity, (String)"Chart");
            elChart.setAttribute("name", "Main chart");
            elChart.setAttribute("minConditions", "1");
            elChart.setAttribute("maxConditions", "4");
            elChart.setAttribute("minExitConditions", "1");
            elChart.setAttribute("maxExitConditions", "4");
            elChart.setAttribute("maxExitTypes", "5");
            elChart.setAttribute("minPeriod", "2");
            elChart.setAttribute("maxPeriod", "100");
            elChart.setAttribute("minShift", "0");
            elChart.setAttribute("maxShift", "10");
        }
        if ((elBuildMode = XMLUtil.tryAddElement((Element)elWhatToBuild, (String)"BuildMode")).getAttributeValue("generationType") == null) {
            elBuildMode.setAttribute("generationType", "random-generation");
        }
        try {
            String architecture;
            Element elStrategyType = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"StrategyType");
            if (elStrategyType != null && (architecture = elStrategyType.getAttributeValue("architecture")) != null && architecture.equals("sq4fuzzy")) {
                if (elStrategyType.getAttributeValue("minTrue") == null) {
                    elStrategyType.setAttribute("minTrue", "60");
                }
                if (elStrategyType.getAttributeValue("maxTrue") == null) {
                    elStrategyType.setAttribute("maxTrue", "80");
                }
            }
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            return;
        }
        this.fixSLPTOptions(elWhatToBuild);
    }

    private void fixSLPTOptions(Element elWhatToBuild) {
        Element elSLPTOptions = XMLUtil.tryAddElement((Element)elWhatToBuild, (String)"SLPTOptions");
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"SLRequired", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"PTRequired", (boolean)true);
        XMLUtil.tryAddNode((Element)elSLPTOptions, (String)"SLValueType", (String)"pips");
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"SLATR", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"SLFixedPips", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"SLPercent", (boolean)true);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MinSLInPips", (int)40);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MinSLInMoney", (double)50.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MinSLInPercent", (double)1.0);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MaxSLInPips", (int)200);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MaxSLInMoney", (double)300.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MaxSLInPercent", (double)10.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MinSLATRMultiple", (double)1.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MaxSLATRMultiple", (double)15.0);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MinSLATRPeriod", (int)20);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MaxSLATRPeriod", (int)20);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"SeparatedSettings", (boolean)false);
        XMLUtil.tryAddNode((Element)elSLPTOptions, (String)"PTValueType", (String)"pips");
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"PTFixedPips", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"PTATR", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"PTPercent", (boolean)true);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MinPTInPips", (int)40);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MinPTInMoney", (int)50);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MinPTInPercent", (double)1.0);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MaxPTInPips", (int)200);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MaxPTInMoney", (int)300);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MaxPTInPercent", (double)10.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MinPTATRMultiple", (double)1.0);
        XMLUtil.tryAddDoubleNode((Element)elSLPTOptions, (String)"MaxPTATRMultiple", (double)15.0);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MinPTATRPeriod", (int)20);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"MaxPTATRPeriod", (int)20);
        XMLUtil.tryAddBooleanNode((Element)elSLPTOptions, (String)"LimitSLPTRRR", (boolean)false);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"LimitSLPTRRRFrom", (int)1);
        XMLUtil.tryAddIntNode((Element)elSLPTOptions, (String)"LimitSLPTRRRTo", (int)1);
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        Element elWhatToBuild = null;
        Element elStrategyType = null;
        Element elMarketSides = null;
        Element elRulesComplexity = null;
        Element elBuildMode = null;
        Element elSLPTOptions = null;
        try {
            elWhatToBuild = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
            elStrategyType = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"StrategyType");
            elMarketSides = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"MarketSides");
            elRulesComplexity = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"RulesComplexity");
            elBuildMode = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"BuildMode");
            elSLPTOptions = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"SLPTOptions");
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            data.addError(tabTitle, null, e.getMessage());
            return;
        }
        BuildType buildType = new BuildType();
        buildType.strategyType = elStrategyType.getAttributeValue("type");
        if (buildType.strategyType == null) {
            data.addError(tabTitle, "StrategyType", "Strategy type not filled");
            return;
        }
        try {
            data.addParam("BuildType", (Serializable)((Object)buildType.strategyType));
        }
        catch (Exception e) {
            Log.error("Cannot add build type", (Throwable)e);
        }
        try {
            switch (buildType.strategyType) {
                case "simple": {
                    break;
                }
                case "multi-tf": {
                    this.checkMultiTFType(elStrategyType, elRulesComplexity, buildType, data);
                    break;
                }
                case "template": {
                    buildType.templateFile = elStrategyType.getAttributeValue("templateFile");
                    if (buildType.templateFile == null) {
                        data.addError(tabTitle, "TemplateFile", "Template file not set");
                        return;
                    }
                    this.checkTemplateType(elSettings, task, data);
                    break;
                }
                case "improve": {
                    this.checkImproveType(elStrategyType, buildType, data, projectName);
                    break;
                }
                default: {
                    data.addError(tabTitle, "StrategyType", "Unknown strategy type: '" + buildType.strategyType + "'");
                    return;
                }
            }
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            return;
        }
        try {
            switch (buildType.direction = elMarketSides.getAttributeValue("type")) {
                case "both": 
                case "long": 
                case "short": {
                    break;
                }
                default: {
                    throw new Exception();
                }
            }
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            data.addError(tabTitle, "StrategyDirections", "Strategy directions type not set or invalid");
            return;
        }
        if (buildType.direction.equals("both")) {
            try {
                buildType.entrySymmetry = Boolean.parseBoolean(elMarketSides.getChild("EntrySymmetry").getText());
            }
            catch (Exception e) {
                data.addError(tabTitle, "EntrySymmetry", "Entry symmetry not set or invalid");
                return;
            }
            try {
                buildType.exitSymmetry = Boolean.parseBoolean(elMarketSides.getChild("ExitSymmetry").getText());
            }
            catch (Exception e) {
                data.addError(tabTitle, "ExitSymmetry", "Exit symmetry not set or invalid");
                return;
            }
        }
        try {
            data.addParam("WhatToBuild", (Serializable)buildType);
        }
        catch (Exception e) {
            Log.error("StrategyType param is already defined", (Throwable)e);
        }
        try {
            if (ProjectEngine.isDefaulProject((String)projectName)) {
                Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)"Results");
                if (databank == null) {
                    data.addParam("DatabankTarget", (Serializable)ProjectConfigHelper.getOutputDatabank((String)projectName, (Element)elSettings));
                } else {
                    data.addParam("DatabankTarget", (Serializable)databank);
                }
            } else {
                data.addParam("DatabankTarget", (Serializable)ProjectConfigHelper.getOutputDatabank((String)projectName, (Element)elSettings));
            }
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            data.addError(this.getSettingName(), null, e.getMessage());
        }
        try {
            BuildMode buildMode = new BuildMode();
            switch (buildMode.generationType = elBuildMode.getAttributeValue("generationType")) {
                case "genetic-evolution": {
                    this.checkGeneticEvolution(elBuildMode, buildMode, data);
                    if (buildMode.initGenerationType == 2) {
                        try {
                            data.addParam("DatabankSource", (Serializable)ProjectEngine.get((String)projectName).getDatabanks().get((Object)"Initial population"));
                        }
                        catch (Exception e) {
                            data.addError(this.getSettingName(), null, e.getMessage());
                        }
                    }
                    data.addParam("DatabankLastGeneration", (Serializable)ProjectEngine.get((String)projectName).getDatabanks().get((Object)"Last generation"));
                    break;
                }
                case "random-generation": {
                    break;
                }
                default: {
                    data.addError(tabTitle, "GenerationType", "Unknown generation type: '" + buildMode.generationType + "'");
                    return;
                }
            }
            data.addParam("BuildMode", (Serializable)buildMode);
        }
        catch (Exception e) {
            Log.error("Exception ", (Throwable)e);
            data.addError(tabTitle, null, e.getMessage());
        }
        try {
            this.readBuildSettings(elSLPTOptions, elStrategyType, data);
            this.checkNumberOfExitTypes(elSettings, data, buildType);
        }
        catch (Exception e) {
            Log.error("Exception", (Throwable)e);
            data.addError(this.getSettingName(), "SL/PT settings", e.getMessage());
        }
    }

    private void readBuildSettings(Element elSLPTOptions, Element elStrategyType, TaskSettingsData data) throws Exception {
        boolean SLRequired = Boolean.parseBoolean(elSLPTOptions.getChild("SLRequired").getText());
        boolean PTRequired = Boolean.parseBoolean(elSLPTOptions.getChild("PTRequired").getText());
        int MinSLInPips = Integer.parseInt(elSLPTOptions.getChild("MinSLInPips").getText());
        int MaxSLInPips = Integer.parseInt(elSLPTOptions.getChild("MaxSLInPips").getText());
        double MinSLInPercent = Double.parseDouble(elSLPTOptions.getChild("MinSLInPercent").getText());
        double MaxSLInPercent = Double.parseDouble(elSLPTOptions.getChild("MaxSLInPercent").getText());
        double MinSLATRMultiple = Double.parseDouble(elSLPTOptions.getChild("MinSLATRMultiple").getText());
        double MaxSLATRMultiple = Double.parseDouble(elSLPTOptions.getChild("MaxSLATRMultiple").getText());
        int MinSLATRPeriod = Integer.parseInt(elSLPTOptions.getChild("MinSLATRPeriod").getText());
        int MaxSLATRPeriod = Integer.parseInt(elSLPTOptions.getChild("MaxSLATRPeriod").getText());
        int MinPTInPips = Integer.parseInt(elSLPTOptions.getChild("MinPTInPips").getText());
        int MaxPTInPips = Integer.parseInt(elSLPTOptions.getChild("MaxPTInPips").getText());
        double MinPTInPercent = Double.parseDouble(elSLPTOptions.getChild("MinPTInPercent").getText());
        double MaxPTInPercent = Double.parseDouble(elSLPTOptions.getChild("MaxPTInPercent").getText());
        double MinPTATRMultiple = Double.parseDouble(elSLPTOptions.getChild("MinPTATRMultiple").getText());
        double MaxPTATRMultiple = Double.parseDouble(elSLPTOptions.getChild("MaxPTATRMultiple").getText());
        int MinPTATRPeriod = Integer.parseInt(elSLPTOptions.getChild("MinPTATRPeriod").getText());
        int MaxPTATRPeriod = Integer.parseInt(elSLPTOptions.getChild("MaxPTATRPeriod").getText());
        boolean LimitSLPTRRR = Boolean.parseBoolean(elSLPTOptions.getChild("LimitSLPTRRR").getText());
        int LimitSLPTRRRFrom = Integer.parseInt(elSLPTOptions.getChild("LimitSLPTRRRFrom").getText());
        int LimitSLPTRRRTo = Integer.parseInt(elSLPTOptions.getChild("LimitSLPTRRRTo").getText());
        boolean SLATR = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("SLATR"), (boolean)false);
        boolean SLFixedPips = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("SLFixedPips"), (boolean)false);
        boolean SLPercent = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("SLPercent"), (boolean)false);
        boolean PTATR = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("PTATR"), (boolean)false);
        boolean PTFixedPips = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("PTFixedPips"), (boolean)false);
        boolean PTPercent = XMLUtil.getBooleanFromElText((Element)elSLPTOptions.getChild("PTPercent"), (boolean)false);
        String architecture = elStrategyType.getAttributeValue("architecture");
        int fuzzyMinTrue = 60;
        int fuzzyMaxTrue = 80;
        if (architecture != null && architecture.equals("sq4fuzzy")) {
            fuzzyMinTrue = Integer.parseInt(elStrategyType.getAttributeValue("minTrue"));
            fuzzyMaxTrue = Integer.parseInt(elStrategyType.getAttributeValue("maxTrue"));
        }
        boolean hasError = false;
        if (SLFixedPips && MaxSLInPips < MinSLInPips) {
            data.addError(tabTitle, "Min/Max SL", "Max SL in pips cannot be smaller than Min SL in pips");
            hasError = true;
        }
        if (SLPercent && MaxSLInPercent < MinSLInPercent) {
            data.addError(tabTitle, "Min/Max SL", "Max SL in percent cannot be smaller than Min SL in percent");
            hasError = true;
        }
        if (SLATR && MaxSLATRMultiple < MinSLATRMultiple) {
            data.addError(tabTitle, "Min/Max SL", "Max SL ATR coeficient cannot be smaller than Min SL ATR coeficient");
            hasError = true;
        }
        if (SLATR && MaxSLATRPeriod < MinSLATRPeriod) {
            data.addError(tabTitle, "Min/Max SL", "Max SL ATR period cannot be smaller than Min SL ATR period");
            hasError = true;
        }
        if (PTFixedPips && MaxPTInPips < MinPTInPips) {
            data.addError(tabTitle, "Min/Max PT", "Max PT in pips cannot be smaller than Min PT in pips");
            hasError = true;
        }
        if (PTPercent && MaxPTInPercent < MinPTInPercent) {
            data.addError(tabTitle, "Min/Max SL", "Max PT in percent cannot be smaller than Min PT in percent");
            hasError = true;
        }
        if (PTATR && MaxPTATRMultiple < MinPTATRMultiple) {
            data.addError(tabTitle, "Min/Max PT", "Max PT ATR coeficient cannot be smaller than Min PT ATR coeficient");
            hasError = true;
        }
        if (PTATR && MaxPTATRPeriod < MinPTATRPeriod) {
            data.addError(tabTitle, "Min/Max PT", "Max PT ATR period cannot be smaller than Min PT ATR period");
            hasError = true;
        }
        if (LimitSLPTRRR && LimitSLPTRRRFrom > LimitSLPTRRRTo) {
            data.addError(tabTitle, "Limit Risk-reward ratio", "Minumum must be smaller or equal to maximum!");
            hasError = true;
        }
        if (hasError) {
            return;
        }
        boolean separateSettingsForPT = Boolean.parseBoolean(elSLPTOptions.getChild("SeparatedSettings").getText());
        if (!separateSettingsForPT) {
            MinPTInPips = MinSLInPips;
            MaxPTInPips = MaxSLInPips;
            MinPTATRMultiple = MinSLATRMultiple;
            MaxPTATRMultiple = MaxSLATRMultiple;
            MinPTATRPeriod = MinSLATRPeriod;
            MaxPTATRPeriod = MaxSLATRPeriod;
            PTATR = SLATR;
        }
        if (LimitSLPTRRR) {
            double coefFrom = (double)LimitSLPTRRRFrom / 100.0;
            double coefTo = (double)LimitSLPTRRRTo / 100.0;
            if (SLFixedPips && PTFixedPips) {
                MaxPTInPips = (int)this.setCorrectMax(MinPTInPips, MaxPTInPips, coefTo * (double)MaxSLInPips);
                MinPTInPips = (int)this.setCorrectMin(MinPTInPips, MaxPTInPips, coefFrom * (double)MinSLInPips);
                MinSLInPips = (int)this.setCorrectMin(MinSLInPips, MaxSLInPips, (double)MinPTInPips / coefFrom);
                MaxSLInPips = (int)this.setCorrectMax(MinSLInPips, MaxSLInPips, (double)MinPTInPips / coefTo);
            }
            if (SLATR && PTATR) {
                MaxPTATRMultiple = this.setCorrectMax(MinPTATRMultiple, MaxPTATRMultiple, coefTo * MaxSLATRMultiple);
                MinPTATRMultiple = this.setCorrectMin(MinPTATRMultiple, MaxPTATRMultiple, coefFrom * MinSLATRMultiple);
                MinSLATRMultiple = this.setCorrectMin(MinSLATRMultiple, MaxSLATRMultiple, MinPTATRMultiple / coefFrom);
                MaxSLATRMultiple = this.setCorrectMax(MinSLATRMultiple, MaxSLATRMultiple, MaxPTATRMultiple / coefTo);
            }
        }
        SettingsMap buildSettings = new SettingsMap();
        buildSettings.set("SLRequired", (Object)SLRequired);
        buildSettings.set("PTRequired", (Object)PTRequired);
        buildSettings.set("MinSLInPips", (Object)MinSLInPips);
        buildSettings.set("MaxSLInPips", (Object)MaxSLInPips);
        buildSettings.set("MinSLInPercent", (Object)MinSLInPercent);
        buildSettings.set("MaxSLInPercent", (Object)MaxSLInPercent);
        buildSettings.set("MinSLATRMultiple", (Object)MinSLATRMultiple);
        buildSettings.set("MaxSLATRMultiple", (Object)MaxSLATRMultiple);
        buildSettings.set("MinSLATRPeriod", (Object)MinSLATRPeriod);
        buildSettings.set("MaxSLATRPeriod", (Object)MaxSLATRPeriod);
        buildSettings.set("MinPTInPips", (Object)MinPTInPips);
        buildSettings.set("MaxPTInPips", (Object)MaxPTInPips);
        buildSettings.set("MinPTInPercent", (Object)MinPTInPercent);
        buildSettings.set("MaxPTInPercent", (Object)MaxPTInPercent);
        buildSettings.set("MinPTATRMultiple", (Object)MinPTATRMultiple);
        buildSettings.set("MaxPTATRMultiple", (Object)MaxPTATRMultiple);
        buildSettings.set("MinPTATRPeriod", (Object)MinPTATRPeriod);
        buildSettings.set("MaxPTATRPeriod", (Object)MaxPTATRPeriod);
        buildSettings.set("LimitSLPTRRR", (Object)LimitSLPTRRR);
        buildSettings.set("LimitSLPTRRRFrom", (Object)LimitSLPTRRRFrom);
        buildSettings.set("LimitSLPTRRRTo", (Object)LimitSLPTRRRTo);
        buildSettings.set("SLATR", (Object)SLATR);
        buildSettings.set("PTATR", (Object)PTATR);
        buildSettings.set("SLFixedPips", (Object)SLFixedPips);
        buildSettings.set("PTFixedPips", (Object)PTFixedPips);
        buildSettings.set("SLPercent", (Object)SLPercent);
        buildSettings.set("PTPercent", (Object)PTPercent);
        buildSettings.set("SeparateSLPT", (Object)separateSettingsForPT);
        buildSettings.set("FuzzyMinTrue", (Object)fuzzyMinTrue);
        buildSettings.set("FuzzyMaxTrue", (Object)fuzzyMaxTrue);
        buildSettings.set("Architecture", (Object)architecture);
        data.addParam("BuildSettings", (Serializable)buildSettings);
    }

    private double setCorrectMin(double min, double max, double newValue) {
        if (newValue < min) {
            return min;
        }
        if (newValue < max) {
            return newValue;
        }
        return max;
    }

    private double setCorrectMax(double min, double max, double newValue) {
        if (newValue > max) {
            return max;
        }
        if (newValue > min) {
            return newValue;
        }
        return max;
    }

    private void checkGeneticEvolution(Element elBuildMode, BuildMode buildMode, TaskSettingsData data) {
        try {
            Element elEvoInSamplePeriod;
            Element elRestartOnStagnation;
            String status;
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"PopulationSize", (int)5);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"MaxGenerations", (int)10);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"CrossoverProbability", (int)50);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"MutationProbability", (int)20);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"ShowAdvancedGeneticSettings", (boolean)false);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"Islands", (int)10);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"MigrationModulo", (int)50);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"MigrationRate", (int)20);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"ShowLastGenerationDatabank", (boolean)false);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"InitGenerationType", (int)1);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"DecimationCoef", (int)1);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"FilterInitialPopulation", (boolean)true);
            XMLUtil.tryAddElement((Element)elBuildMode, (String)"Conditions");
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"EvoRestartOnStagnation", (boolean)true);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"EvoFitnessRestartType", (int)0);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"EvoStagnationRestartGenerations", (int)3);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"ShowLastGenerationDatabank", (boolean)false);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"FreshBloodReplaceSimilar", (boolean)true);
            XMLUtil.tryAddBooleanNode((Element)elBuildMode, (String)"FreshBloodReplaceWeakest", (boolean)true);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"FreshBloodWeakestPct", (int)10);
            XMLUtil.tryAddIntNode((Element)elBuildMode, (String)"FreshBloodWeakestGenerations", (int)2);
            buildMode.populationSize = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"PopulationSize"));
            buildMode.maxGenerations = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"MaxGenerations"));
            buildMode.crossoverProbability = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"CrossoverProbability"));
            buildMode.mutationProbability = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"MutationProbability"));
            buildMode.islands = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"Islands"));
            if (buildMode.islands < 1 || buildMode.islands > 100) {
                data.addError(tabTitle, "Islands", L.t((String)"Islands number must be between 1 and 100", (Object[])new Object[0]));
            }
            buildMode.migrationModulo = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"MigrationModulo"));
            buildMode.migrationRate = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"MigrationRate"));
            buildMode.initGenerationType = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"InitGenerationType"));
            buildMode.decimationCoef = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"DecimationCoef"));
            try {
                buildMode.conditions = ProjectConfigHelper.getConditions((Element)elBuildMode.getChild("Conditions"));
            }
            catch (Exception e) {
                throw new Exception(L.t((String)"Invalid initial population conditions: %s", (Object[])new Object[]{e.getMessage()}));
            }
            data.addParam("InitialGenerationConditions", (Serializable)buildMode.conditions);
            buildMode.evoRestartOnStagnation = XMLUtil.getNodeBooleanValue((Element)elBuildMode, (String)"EvoRestartOnStagnation", (boolean)false);
            buildMode.evoFitnessRestartType = XMLUtil.getNodeIntValue((Element)elBuildMode, (String)"EvoFitnessRestartType", (int)40);
            buildMode.evoStagnationRestartGenerations = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"EvoStagnationRestartGenerations", (String)"0"));
            buildMode.showLastGeneration = Boolean.parseBoolean(XMLUtil.getNodeValue((Element)elBuildMode, (String)"ShowLastGenerationDatabank", (String)"false"));
            Element elRestartOnFinish = elBuildMode.getChild("EvoRestartOnFinish");
            if (elRestartOnFinish != null && (status = elRestartOnFinish.getAttributeValue("status")) != null && status.equals("true")) {
                buildMode.evoRestartOnFinish = true;
            }
            if ((elRestartOnStagnation = elBuildMode.getChild("EvoRestartOnStagnation")) != null) {
                String generations;
                String status2 = elRestartOnStagnation.getAttributeValue("status");
                if (status2 != null && status2.equals("true")) {
                    buildMode.evoRestartOnStagnation = true;
                }
                if ((generations = elRestartOnStagnation.getAttributeValue("generations")) != null && !generations.equals("")) {
                    buildMode.evoStagnationRestartGenerations = Integer.parseInt(generations);
                }
                buildMode.evoFitnessRestartType = XMLUtil.getIntAttr((Element)elRestartOnStagnation, (String)"fitnessType", (byte)10);
            }
            if ((elEvoInSamplePeriod = elBuildMode.getChild("EvoInSamplePeriod")) != null) {
                buildMode.evoDivideInSamplePeriod = XMLUtil.getBooleanAttr((Element)elEvoInSamplePeriod, (String)"divide", (boolean)true);
                buildMode.evoTrainingValidationRatio = XMLUtil.getIntAttr((Element)elEvoInSamplePeriod, (String)"ratio", (int)50) / 100;
            } else {
                buildMode.evoDivideInSamplePeriod = true;
                buildMode.evoTrainingValidationRatio = 0.5;
            }
            buildMode.freshBloodReplaceSimilar = Boolean.parseBoolean(XMLUtil.getNodeValue((Element)elBuildMode, (String)"FreshBloodReplaceSimilar", (String)"true"));
            buildMode.freshBloodReplaceWeakest = Boolean.parseBoolean(XMLUtil.getNodeValue((Element)elBuildMode, (String)"FreshBloodReplaceWeakest", (String)"true"));
            buildMode.freshBloodWeakestPct = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"FreshBloodWeakestPct", (String)"10"));
            buildMode.freshBloodWeakestGenerations = Integer.parseInt(XMLUtil.getNodeValue((Element)elBuildMode, (String)"FreshBloodWeakestGenerations", (String)"2"));
        }
        catch (Exception e) {
            data.addError(tabTitle, null, "Cannot load GeneticEvolution settings. " + e.getMessage());
        }
    }

    private void checkImproveType(Element elStrategyType, BuildType buildType, TaskSettingsData data, String projectName) throws Exception {
        buildType.improveType = elStrategyType.getAttributeValue("improveType");
        if (buildType.improveType == null) {
            data.addError(tabTitle, "ImproveType", L.t((String)"Improve type not set", (Object[])new Object[0]));
            throw new Exception();
        }
        switch (buildType.improveType) {
            case "strategy": {
                buildType.strategyFile = elStrategyType.getAttributeValue("strategyFile");
                if (buildType.strategyFile == null) {
                    data.addError(tabTitle, "Strategy file", L.t((String)"Improve strategy file not set", (Object[])new Object[0]));
                    throw new Exception();
                }
                if (!buildType.strategyFile.contains("/") && !buildType.strategyFile.contains("\\")) {
                    buildType.strategyFile = MainApp.getDataPath() + "user/strategies/" + buildType.strategyFile;
                }
                if (new File(buildType.strategyFile).exists()) break;
                data.addError(tabTitle, "Strategy file", "Strategy file '" + buildType.strategyFile + "' doesn't exist");
                throw new Exception();
            }
            case "databank": {
                buildType.improveDatabank = elStrategyType.getAttributeValue("improveDatabank");
                if (buildType.improveDatabank != null && !buildType.improveDatabank.isEmpty()) break;
                buildType.improveDatabank = ProjectEngine.isDefaulProject((String)projectName) ? "Strategies to improve" : "Results";
                break;
            }
            default: {
                data.addError(tabTitle, "ImproveType", "Unknown improve type: '" + buildType.improveType + "'");
                throw new Exception();
            }
        }
    }

    private void checkTemplateType(Element elSettings, ISQTask task, TaskSettingsData data) throws Exception {
        if (!MainApp.runInConsoleWithoutActiveWebserver()) {
            return;
        }
        Element elStrategyTemplate = StrategyTemplateGenerator.getConfiguredTemplate((Element)elSettings, (String)task.getCustomName());
        if (elStrategyTemplate == null) {
            return;
        }
        List elCharts = ((Element)elSettings.getChild("Data").getChild("Setups").getChildren("Setup").get(0)).getChildren("Chart");
        int chartCount = elCharts.size();
        Element elMainChart = (Element)elCharts.get(0);
        String mainSymbol = elMainChart.getAttributeValue("symbol");
        String mainTimeframe = elMainChart.getAttributeValue("timeframe");
        String mainSpread = elMainChart.getAttributeValue("spread");
        Element elDatas = elStrategyTemplate.getChild("Strategy").getChild("Datas");
        List children = elDatas.getChildren("data");
        int templateDataCount = children.size();
        if (templateDataCount > chartCount) {
            for (int i = chartCount; i < children.size(); ++i) {
                Element elData = (Element)children.get(i);
                String symbol = XMLUtil.getNodeValue((Element)elData, (String)"symbol");
                String timeframe = XMLUtil.getNodeValue((Element)elData, (String)"timeFrame");
                try {
                    TimeframeManager.getMillis((String)timeframe);
                }
                catch (Exception e) {
                    timeframe = TimeframeManager.translateSQ3TFToString((int)Integer.parseInt(timeframe));
                }
                DataInfo symbolInfo = DataManager.getDataInfo((String)"History", (String)symbol);
                if (symbolInfo == null) {
                    return;
                }
                if (TimeframeManager.getMillis((String)timeframe) < TimeframeManager.getMillis((String)symbolInfo.timeframe)) {
                    return;
                }
                Element elChart = new Element("Chart");
                elChart.setAttribute("symbol", symbol);
                elChart.setAttribute("timeframe", timeframe);
                elChart.setAttribute("spread", mainSpread);
                elCharts.add(elChart);
            }
        }
    }

    private void checkMultiTFType(Element elStrategyType, Element elRulesComplexity, BuildType buildType, TaskSettingsData data) throws Exception {
        try {
            buildType.additionalCharts = Integer.parseInt(elStrategyType.getAttributeValue("additionalCharts"));
        }
        catch (Exception e) {
            data.addError(tabTitle, "AdditionalCharts", L.t((String)"Additional charts number not set or invalid", (Object[])new Object[0]));
            throw new Exception();
        }
        boolean differentSettings = false;
        try {
            differentSettings = Boolean.parseBoolean(XMLUtil.getAttr((Element)elRulesComplexity, (String)"useDifferentSettings"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        int chartIndex = 0;
        for (Element elChart : elRulesComplexity.getChildren("Chart")) {
            ChartSettings chartSettings = new ChartSettings();
            String chartName = this.getChartName(chartIndex);
            try {
                chartSettings.minConditions = Integer.parseInt(elChart.getAttributeValue("minConditions"));
                if (chartSettings.minConditions < 0) {
                    throw new Exception();
                }
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min conditions not set or invalid. Min allowed value: 1");
            }
            try {
                chartSettings.maxConditions = Integer.parseInt(elChart.getAttributeValue("maxConditions"));
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Max conditions not set or invalid");
            }
            if (chartSettings.minConditions > chartSettings.maxConditions) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min conditions must be lower than Max conditions");
            }
            boolean exitConditionsSet = false;
            try {
                chartSettings.minExitConditions = Integer.parseInt(elChart.getAttributeValue("minExitConditions"));
                if (chartSettings.minExitConditions < 0) {
                    throw new Exception();
                }
                exitConditionsSet = true;
            }
            catch (Exception e) {
                chartSettings.minExitConditions = chartSettings.minConditions;
            }
            try {
                chartSettings.maxExitConditions = Integer.parseInt(elChart.getAttributeValue("maxExitConditions"));
                if (chartSettings.maxExitConditions < 0) {
                    throw new Exception();
                }
                exitConditionsSet = true;
            }
            catch (Exception e) {
                chartSettings.maxExitConditions = chartSettings.maxExitConditions;
            }
            if (exitConditionsSet && chartSettings.minExitConditions > chartSettings.maxExitConditions) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min exit conditions must be lower than Max exit conditions");
            }
            if (chartIndex == 0) {
                try {
                    chartSettings.maxExitTypes = XMLUtil.getIntAttr((Element)elChart, (String)"maxExitTypes", (int)5);
                    if (chartSettings.maxExitTypes < 1) {
                        throw new Exception();
                    }
                }
                catch (Exception e) {
                    data.addError(tabTitle, "AdditionalCharts", chartName + " - Max Exit Types not set or invalid. Min allowed value: 1");
                }
            }
            try {
                chartSettings.minPeriod = Integer.parseInt(elChart.getAttributeValue("minPeriod"));
                if (chartSettings.minPeriod < 2) {
                    throw new Exception();
                }
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min period not set or invalid. Min allowed value: 2");
            }
            try {
                chartSettings.maxPeriod = Integer.parseInt(elChart.getAttributeValue("maxPeriod"));
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Max period not set or invalid");
            }
            if (chartSettings.minPeriod > chartSettings.maxPeriod) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min period must be lower than Max period");
            }
            try {
                chartSettings.minShift = Integer.parseInt(elChart.getAttributeValue("minShift"));
                if (chartSettings.minShift < 0) {
                    throw new Exception();
                }
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Min shift not set or invalid. Min allowed value: 0");
            }
            try {
                chartSettings.maxShift = Integer.parseInt(elChart.getAttributeValue("maxShift"));
            }
            catch (Exception e) {
                data.addError(tabTitle, "AdditionalCharts", chartName + " - Max shift not set or invalid");
            }
            ++chartIndex;
        }
    }

    private void checkNumberOfExitTypes(Element elSettings, TaskSettingsData data, BuildType buildType) throws Exception {
        block6: {
            Element elRulesComplexity;
            try {
                Element elWhatToBuild = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
                elRulesComplexity = XMLUtil.getChildElem((Element)elWhatToBuild, (String)"RulesComplexity");
            }
            catch (Exception e) {
                Log.error("Exception ", (Throwable)e);
                data.addError(tabTitle, null, e.getMessage());
                return;
            }
            boolean chartIndex = false;
            Iterator iterator = elRulesComplexity.getChildren("Chart").iterator();
            if (!iterator.hasNext()) break block6;
            Element elChart = (Element)iterator.next();
            if (!chartIndex) {
                int maxExitTypes = 0;
                try {
                    maxExitTypes = XMLUtil.getIntAttr((Element)elChart, (String)"maxExitTypes", (int)5);
                    if (maxExitTypes < 0) {
                        throw new Exception();
                    }
                }
                catch (Exception e) {
                    data.addError(tabTitle, "WhatToBuild", " - Max Exit Types number not set or invalid");
                }
                SettingsMap buildSettings = (SettingsMap)data.getParams().get("BuildSettings");
                buildSettings.set("MaxExitTypes", (Object)maxExitTypes);
                buildSettings.set("ExitSymmetry", (Object)buildType.exitSymmetry);
            }
        }
    }

    private String getChartName(int index) {
        return index == 0 ? "Main chart" : "Additional chart " + index;
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        String type;
        Element elWhatToBuild = XMLUtil.tryAddElement((Element)elSettings, (String)"WhatToBuild");
        Element elStrategyType = XMLUtil.tryAddElement((Element)elWhatToBuild, (String)"StrategyType");
        switch (type = XMLUtil.getStringAttr((Element)elStrategyType, (String)"type", (String)"N/A")) {
            case "simple": {
                type = L.t((String)"Simple strategies", (Object[])new Object[0]);
                break;
            }
            case "multi-tf": {
                type = L.t((String)"Multi-symbol/Multi-TF strategies", (Object[])new Object[0]);
                break;
            }
            case "template": {
                type = L.t((String)"Strategies using template", (Object[])new Object[0]);
                break;
            }
            case "improve": {
                type = L.t((String)"Improve existing strategy", (Object[])new Object[0]);
            }
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Strategy type", (Object[])new Object[0])).put("value", (Object)type));
    }

    public String getSettingName() {
        return "WhatToBuild";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

