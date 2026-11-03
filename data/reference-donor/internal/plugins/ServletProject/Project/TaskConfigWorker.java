/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Project;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TaskConfigWorker {
    private static final Logger Log = LoggerFactory.getLogger(TaskConfigWorker.class);

    public static boolean isCustomSettings(String templateName, Element existingSettings) throws Exception {
        if (templateName == null || templateName.equals("Custom")) {
            return true;
        }
        if (existingSettings == null) {
            throw new Exception(L.t((String)"Config has no settings", (Object[])new Object[0]));
        }
        Element elSettingsTemplate = null;
        try {
            elSettingsTemplate = TaskConfigWorker.getTemplateSettings(templateName);
        }
        catch (Exception e) {
            return true;
        }
        try {
            if (!XMLUtil.elementsEqual((Element)XMLUtil.getChildElem((Element)existingSettings, (String)"Blocks"), (Element)XMLUtil.getChildElem((Element)elSettingsTemplate, (String)"Blocks"))) {
                return true;
            }
            Element elWhatToBuildExisting = XMLUtil.getChildElem((Element)existingSettings, (String)"WhatToBuild");
            Element elWhatToBuildTemplate = XMLUtil.getChildElem((Element)elSettingsTemplate, (String)"WhatToBuild");
            Element elStrategyTypeExisting = XMLUtil.getChildElem((Element)elWhatToBuildExisting, (String)"StrategyType");
            Element elStrategyTypeTemplate = XMLUtil.getChildElem((Element)elWhatToBuildTemplate, (String)"StrategyType");
            if (!(elStrategyTypeExisting.getAttributeValue("architecture").equals(elStrategyTypeTemplate.getAttributeValue("architecture")) && XMLUtil.elementsEqual((Element)XMLUtil.getChildElem((Element)elWhatToBuildExisting, (String)"MarketSides"), (Element)XMLUtil.getChildElem((Element)elWhatToBuildTemplate, (String)"MarketSides")) && XMLUtil.elementsEqual((Element)XMLUtil.getChildElem((Element)elWhatToBuildExisting, (String)"SLPTOptions"), (Element)XMLUtil.getChildElem((Element)elWhatToBuildTemplate, (String)"SLPTOptions")) && XMLUtil.elementsEqual((Element)XMLUtil.getChildElem((Element)elWhatToBuildExisting, (String)"BuildMode"), (Element)XMLUtil.getChildElem((Element)elWhatToBuildTemplate, (String)"BuildMode")))) {
                return true;
            }
            Element elRulesComplexityExisting = XMLUtil.getChildElem((Element)elWhatToBuildExisting, (String)"RulesComplexity");
            Element elRulesComplexityTemplate = XMLUtil.getChildElem((Element)elWhatToBuildTemplate, (String)"RulesComplexity");
            List complexitiesExisting = elRulesComplexityExisting.getChildren("Chart");
            List complexitiesTemplate = elRulesComplexityTemplate.getChildren("Chart");
            boolean differentSettingsExisting = false;
            try {
                differentSettingsExisting = Boolean.parseBoolean(elRulesComplexityExisting.getAttributeValue("useDifferentSettings"));
            }
            catch (Exception exception) {
                // empty catch block
            }
            boolean differentSettingsTemplate = false;
            try {
                differentSettingsTemplate = Boolean.parseBoolean(elRulesComplexityTemplate.getAttributeValue("useDifferentSettings"));
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (differentSettingsExisting != differentSettingsTemplate) {
                return true;
            }
            for (int a = 0; a < complexitiesExisting.size() && a < complexitiesTemplate.size() && (differentSettingsExisting || a <= 0); ++a) {
                if (XMLUtil.elementsEqual((Element)((Element)complexitiesExisting.get(a)), (Element)((Element)complexitiesTemplate.get(a)))) continue;
                return true;
            }
            Element elCrossChecksExisting = XMLUtil.getChildElem((Element)existingSettings, (String)"CrossChecks");
            Element elCrossChecksTemplate = XMLUtil.getChildElem((Element)elSettingsTemplate, (String)"CrossChecks");
            List crossChecksExisting = elCrossChecksExisting.getChildren();
            List crossChecksTemplate = elCrossChecksTemplate.getChildren();
            for (int a = 0; a < crossChecksTemplate.size(); ++a) {
                Element crossCheckTemplate = (Element)crossChecksTemplate.get(a);
                boolean found = false;
                for (int i = 0; i < crossChecksExisting.size(); ++i) {
                    String useTemplate;
                    Element crossCheckExisting = (Element)crossChecksExisting.get(i);
                    if (!crossCheckExisting.getName().equals(crossCheckTemplate.getName())) continue;
                    String useExisting = crossCheckExisting.getAttributeValue("use", "false");
                    if (!useExisting.equals(useTemplate = crossCheckTemplate.getAttributeValue("use", "false"))) {
                        return true;
                    }
                    found = true;
                }
                if (found) continue;
                return true;
            }
            return false;
        }
        catch (Exception e) {
            Log.error("Comapring config with template failed", (Throwable)e);
            return true;
        }
    }

    public static void correctDataSettings(Element elSettingsExisting, String mainChartTF) throws Exception {
        Element elChart;
        Element elData = XMLUtil.getChildElem((Element)elSettingsExisting, (String)"Data");
        Element elSetups = XMLUtil.tryAddElement((Element)elData, (String)"Setups");
        ArrayList symbols = DataManager.list();
        DataInfo firstSymbol = symbols.isEmpty() ? null : (DataInfo)symbols.get(0);
        Element elSetup = elSetups.getChild("Setup");
        if (elSetup == null) {
            elSetup = new Element("Setup");
            elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)(firstSymbol != null ? firstSymbol.dateFrom : 0L)));
            elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)(firstSymbol != null ? firstSymbol.dateTo : 0L)));
            elSetup.setAttribute("testPrecision", "Selected timeframe only (fastest)");
            elSetup.setAttribute("session", "No Session");
            elSetup.setAttribute("slippage", "0");
            elSetup.setAttribute("minDist", "0");
            elSetup.setAttribute("engine", "MetaTrader4");
            elSetups.addContent((Content)elSetup);
        }
        if ((elChart = elSetup.getChild("Chart")) == null) {
            TaskConfigWorker.addDefaultChart(elSetup, firstSymbol, mainChartTF);
        } else {
            String usedSymbol = elChart.getAttributeValue("symbol");
            DataInfo usedSymbolInfo = DataManager.getDataInfo((String)"History", (String)usedSymbol);
            if (usedSymbolInfo != null) {
                try {
                    long dateFrom = SQTime.parseDateToMilis((String)elSetup.getAttributeValue("dateFrom"));
                    if (dateFrom < usedSymbolInfo.dateFrom) {
                        elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)usedSymbolInfo.dateFrom));
                    }
                }
                catch (Exception e) {
                    elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)usedSymbolInfo.dateFrom));
                }
                try {
                    long dateTo = SQTime.parseDateToMilis((String)elSetup.getAttributeValue("dateTo"));
                    if (dateTo > usedSymbolInfo.dateTo) {
                        elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)usedSymbolInfo.dateTo));
                    }
                }
                catch (Exception e) {
                    elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)usedSymbolInfo.dateTo));
                }
                if (mainChartTF != null) {
                    elChart.setAttribute("timeframe", mainChartTF);
                }
            } else {
                TaskConfigWorker.addDefaultChart(elSetup, firstSymbol, mainChartTF);
            }
        }
    }

    private static void addDefaultChart(Element elSetup, DataInfo firstSymbol, String mainChartTF) throws Exception {
        elSetup.removeChildren("Chart");
        elSetup.removeChildren("Commissions");
        Element elChart = new Element("Chart");
        elChart.setAttribute("symbol", firstSymbol != null ? firstSymbol.symbol : "undefined");
        elChart.setAttribute("timeframe", mainChartTF != null ? mainChartTF : (firstSymbol != null ? firstSymbol.timeframe : "undefined"));
        elChart.setAttribute("spread", "0");
        Element elCommissions = new Element("Commissions");
        Element elMethod = null;
        if (firstSymbol != null && firstSymbol.symbolInfo != null) {
            elMethod = XMLUtil.stringToElement((String)firstSymbol.symbolInfo.commissions);
        } else {
            elMethod = new Element("Method");
            elMethod.setAttribute("type", "None");
            elMethod.setAttribute("use", "true");
        }
        elCommissions.addContent((Content)elMethod);
        elSetup.addContent((Content)elCommissions);
        elSetup.addContent((Content)elChart);
        elSetup.setAttribute("dateFrom", SQTime.toUIDateString((long)(firstSymbol != null ? firstSymbol.dateFrom : 0L)));
        elSetup.setAttribute("dateTo", SQTime.toUIDateString((long)(firstSymbol != null ? firstSymbol.dateTo : 0L)));
        elSetup.setAttribute("testPrecision", "Selected timeframe only (fastest)");
    }

    public static Element getTemplateSettings(String templateName) throws Exception {
        File templateFile = new File(SQPaths.simpleTemplatesDirPath + "/" + templateName + ".xml");
        if (!templateFile.exists()) {
            throw new Exception("Template file '" + templateFile.getName() + "' not found");
        }
        Element templateSettings = XMLUtil.fileToXmlElement((File)templateFile);
        return XMLUtil.getChildElem((Element)templateSettings, (String)"Settings");
    }
}

