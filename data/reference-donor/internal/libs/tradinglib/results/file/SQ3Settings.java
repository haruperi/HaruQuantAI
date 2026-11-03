/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results.file;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQ3Settings {
    public static final Logger Log = LoggerFactory.getLogger(SQ3Settings.class);

    public Element convertToSQ3Xml(ResultsGroup resultsGroup) throws Exception {
        Object object;
        Element element;
        String string;
        Element element2 = new Element("Settings");
        SettingsMap settingsMap = resultsGroup.specialValues();
        String string2 = "3";
        String string3 = "false";
        String string4 = "false";
        String string5 = "0";
        String string6 = "5";
        String string7 = "1";
        String string8 = "3";
        String string9 = "false";
        String string10 = "100";
        try {
            string = resultsGroup.getLastSettings();
            if (string == null) {
                Log.info("Strategy '{}' doesn't contain last settings", (Object)resultsGroup.getName());
                return element2;
            }
            element = XMLUtil.stringToElement((String)string);
            object = XMLUtil.getChildElem((Element)element, (String)"WhatToBuild");
            Element element3 = XMLUtil.getChildElem((Element)object, (String)"MarketSides");
            string2 = this.directionToSQ3(element3.getAttributeValue("type"));
            if (element3.getAttributeValue("type").equals("both")) {
                string3 = element3.getChild("EntrySymmetry").getText();
                string4 = element3.getChild("ExitSymmetry").getText();
            }
            Element element4 = element.getChild("Data");
            Element element5 = element4.getChild("Setups");
            Element element6 = element5.getChild("Setup");
            string5 = element6.getAttributeValue("slippage");
            string6 = element6.getAttributeValue("minDist");
            string7 = element6.getAttributeValue("testPrecision");
            if (Integer.parseInt(string7) == 4) {
                string9 = "true";
            }
            Element element7 = element6.getChild("Chart");
            string8 = element7.getAttributeValue("spread");
            Element element8 = element2.getChild("Rankings");
            if (element8 != null) {
                Element element9 = element8.getChild("MaxStrategies");
                string10 = element9.getText();
            }
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
        string = resultsGroup.portfolio().getSettings();
        element2.addContent((Content)new Element("generationType").addContent("1"));
        element2.addContent((Content)new Element("tradingSides").addContent(string2));
        element2.addContent((Content)new Element("symmetricLongShortEntry").addContent(string3));
        element2.addContent((Content)new Element("symmetricLongShortExit").addContent(string4));
        element2.addContent((Content)new Element("slRequired").addContent("true"));
        element2.addContent((Content)new Element("ptRequired").addContent("true"));
        element2.addContent((Content)new Element("slptBasedOnATR").addContent("true"));
        element2.addContent((Content)new Element("slptBasedOnFixedPips").addContent("true"));
        element2.addContent((Content)new Element("minimumPTSL").addContent("0"));
        element2.addContent((Content)new Element("maximumPTSL").addContent("1000"));
        element2.addContent((Content)new Element("minAtrMultiply").addContent("0"));
        element2.addContent((Content)new Element("maxAtrMultiply").addContent("100"));
        element2.addContent((Content)new Element("spread").addContent(string8));
        element2.addContent((Content)new Element("useRealSpread").addContent(string9));
        element2.addContent((Content)new Element("slippage").addContent(string5));
        element2.addContent((Content)new Element("minDistance").addContent(string6));
        element2.addContent((Content)new Element("testPrecision").addContent(string7));
        element2.addContent((Content)new Element("dateFrom").addContent(settingsMap.getLong(SpecialValues.HistoryFrom) / 1000L + ""));
        element2.addContent((Content)new Element("dateTo").addContent(settingsMap.getLong(SpecialValues.HistoryTo) / 1000L + ""));
        OutOfSample outOfSample = element = string == null ? null : (OutOfSample)string.get("OutOfSample");
        if (element == null || !element.isEmpty()) {
            element2.addContent((Content)new Element("oosDateFrom").addContent("0"));
            element2.addContent((Content)new Element("oosDateTo").addContent("0"));
        } else {
            element2.addContent((Content)new Element("oosDateFrom").addContent(element.getDateFrom(0) / 1000L + ""));
            element2.addContent((Content)new Element("oosDateTo").addContent(element.getDateTo(0) / 1000L + ""));
        }
        element2.addContent((Content)new Element("symbol").addContent(resultsGroup.mainResult().getString(SpecialValues.Symbol, "N/A")));
        object = resultsGroup.mainResult().getString(SpecialValues.Timeframe, "N/A");
        element2.addContent((Content)new Element("timeframe").addContent(SQ3Settings.translateSQ4TFToInt((String)object) + ""));
        element2.addContent((Content)new Element("rankingType").addContent("2"));
        element2.addContent((Content)new Element("maxRecordsInDatabank").addContent(string10));
        element2.addContent((Content)new Element("tradeTimeFrom").addContent(settingsMap.getLong(SpecialValues.HistoryFrom) / 1000L + ""));
        element2.addContent((Content)new Element("tradeTimeTo").addContent(settingsMap.getLong(SpecialValues.HistoryTo) / 1000L + ""));
        element2.addContent((Content)new Element("sliderOOS").addContent("0"));
        element2.addContent((Content)new Element("testPrecision").addContent("1"));
        element2.addContent((Content)new Element("capitalSize").addContent(Integer.toString((int)string.getDouble("MoneyManagement.InitialCapital", 10000.0))));
        element2.addContent((Content)new Element("mmType").addContent("0"));
        element2.addContent((Content)new Element("mmLots").addContent("0.1"));
        element2.addContent((Content)new Element("crossoverProbability").addContent("0.95"));
        element2.addContent((Content)new Element("mutationProbability").addContent("0.1"));
        element2.addContent((Content)new Element("exitEndOfDay").addContent(string.containsKey("ExitAtEndOfDay.EODExitTime") + ""));
        element2.addContent((Content)new Element("exitFriday").addContent(string.containsKey("ExitOnFriday.FridayExitTime") + ""));
        element2.addContent((Content)new Element("limitTradesPerDay").addContent(string.get("MaxTradesPerDay", (Object)0) + ""));
        return element2;
    }

    private String directionToSQ3(String string) {
        if (string.equals("both")) {
            return "1";
        }
        if (string.equals("long")) {
            return "2";
        }
        if (string.equals("short")) {
            return "3";
        }
        return "1";
    }

    public Element convertToSQ4Xml(Element element) {
        return null;
    }

    public static int translateSQ4TFToInt(String string) {
        if (string == null) {
            return -2;
        }
        switch (string) {
            case "TICK": {
                return 0;
            }
            case "M1": {
                return 1;
            }
            case "M5": {
                return 5;
            }
            case "M14": {
                return 14;
            }
            case "M15": {
                return 15;
            }
            case "M30": {
                return 30;
            }
            case "M53": {
                return 53;
            }
            case "H1": {
                return 60;
            }
            case "H2": {
                return 120;
            }
            case "H4": {
                return 240;
            }
            case "D1": {
                return 1440;
            }
            case "unknown": {
                return -2;
            }
            case "Intraday": {
                return -10;
            }
        }
        return -2;
    }
}

