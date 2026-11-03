/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.RenameTool;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RenameToolGenerator {
    private static final Logger Log = LoggerFactory.getLogger(RenameToolGenerator.class);
    private static String NO_VALUE = "NN";
    private static int strategyNumber = 0;

    public static void processStrategy(ResultsGroup rg) throws Exception {
        Element elParams;
        Element elBuildTradingOptions;
        String originalName = rg.getName();
        String newName = "";
        Element elStrategyFile = rg.getStrategyXml();
        Element lastSettings = XMLUtil.stringToElement((String)rg.getLastSettings());
        String mainMarket = NO_VALUE;
        String mainTF = NO_VALUE;
        String secondaryTF = NO_VALUE;
        try {
            Element elData = lastSettings.getChild("Data");
            Element elSetups = elData.getChild("Setups");
            Element elSetup = elSetups.getChild("Setup");
            List chartElems = elSetup.getChildren("Chart");
            for (int a = 0; a < chartElems.size(); ++a) {
                Element elChart = (Element)chartElems.get(a);
                String symbol = elChart.getAttributeValue("symbol");
                String timeframe = elChart.getAttributeValue("timeframe");
                if (a == 0) {
                    mainMarket = symbol;
                    mainTF = timeframe != null ? timeframe : NO_VALUE;
                    continue;
                }
                if (a != 1) continue;
                secondaryTF = timeframe != null ? timeframe : NO_VALUE;
                break;
            }
        }
        catch (Exception e) {
            Log.error("Cannot read market info", (Throwable)e);
        }
        String mnMarket = RenameToolGenerator.getValue(RenameToolSettings.MN_Markets, mainMarket);
        String tf = mainTF + (secondaryTF != null && !secondaryTF.equals(NO_VALUE) ? "," + secondaryTF : "");
        String mnTF = RenameToolGenerator.getValue(RenameToolSettings.MN_TimeFrames, tf);
        String magicNumber = RenameToolGenerator.getNumber(mnMarket) + RenameToolGenerator.getNumber(mnTF) + RenameToolGenerator.getStrategyId(originalName);
        Element elStrategy = XMLUtil.getChildElem((Element)elStrategyFile, (String)"Strategy");
        ArrayList ruleElems = XMLUtil.getNestedElements((Element)elStrategy, (String)"Rule");
        String strategyArchitecture = "SQ3";
        String orderType = "N";
        String indicator = NO_VALUE;
        block19: for (int i = 0; i < ruleElems.size(); ++i) {
            String mI;
            Element elItem;
            Element elRule = (Element)ruleElems.get(i);
            String ruleType = elRule.getAttributeValue("type");
            if (ruleType == null) continue;
            if (ruleType.equals("Signal")) {
                strategyArchitecture = "SQX";
            } else if (ruleType.equals("SignalFuzzy")) {
                strategyArchitecture = "FUZ";
            }
            Element elThen = elRule.getChild("Then");
            if (elThen == null || (elItem = elThen.getChild("Item")) == null || (mI = elItem.getAttributeValue("mI")) == null || !mI.equals("Open")) continue;
            String actionKey = elItem.getAttributeValue("key");
            orderType = RenameToolGenerator.getValue(RenameToolSettings.SN_OrderTypes, actionKey);
            orderType = !orderType.equals(NO_VALUE) ? orderType : "N";
            List paramElems = elItem.getChildren("Param");
            for (int a = 0; a < paramElems.size(); ++a) {
                Element elParam = (Element)paramElems.get(a);
                String key = elParam.getAttributeValue("key");
                if (key == null || !key.equals("#Price#")) continue;
                ArrayList itemElems = XMLUtil.getNestedElements((Element)elParam, (String)"Item");
                for (int ii = 0; ii < itemElems.size(); ++ii) {
                    Element itemElem = (Element)itemElems.get(ii);
                    String imI = itemElem.getAttributeValue("mI");
                    if (imI == null || imI.equals("Functions") || imI.equals("Comparisons")) continue;
                    String indicatorName = itemElem.getAttributeValue("key");
                    indicator = RenameToolGenerator.getValue(RenameToolSettings.SN_Indicators, indicatorName);
                    break block19;
                }
                break block19;
            }
            break;
        }
        String closeType = "";
        String timeRange = "";
        Element elOptions = lastSettings.getChild("Options");
        if (elOptions != null && (elBuildTradingOptions = elOptions.getChild("BuildTradingOptions")) != null && (elParams = elBuildTradingOptions.getChild("Params")) != null) {
            List paramElems = elParams.getChildren("Param");
            boolean timeRangeUsed = false;
            boolean closeAtEndOfRange = false;
            String timeFrom = "";
            String timeTo = "";
            block22: for (int a = 0; a < paramElems.size(); ++a) {
                Element elParam = (Element)paramElems.get(a);
                String key = elParam.getAttributeValue("key");
                if (key == null) continue;
                switch (key) {
                    case "ExitAtEndOfDay": {
                        closeType = RenameToolGenerator.isUsed(elParam) ? "CD" : closeType;
                        continue block22;
                    }
                    case "ExitOnFriday": {
                        closeType = closeType.isEmpty() && RenameToolGenerator.isUsed(elParam) ? "CF" : closeType;
                        continue block22;
                    }
                    case "LimitTimeRange": {
                        timeRangeUsed = RenameToolGenerator.isUsed(elParam);
                        continue block22;
                    }
                    case "SignalTimeRangeFrom": {
                        timeFrom = RenameToolGenerator.getTimeRangeHour(elParam);
                        continue block22;
                    }
                    case "SignalTimeRangeTo": {
                        timeTo = RenameToolGenerator.getTimeRangeHour(elParam);
                        continue block22;
                    }
                    case "ExitAtEndOfRange": {
                        closeAtEndOfRange = RenameToolGenerator.isUsed(elParam);
                    }
                }
            }
            if (timeRangeUsed) {
                timeRange = timeFrom + timeTo + (closeAtEndOfRange ? "C" : "");
            }
        }
        newName = newName + RenameToolGenerator.getValue(RenameToolSettings.SN_Markets, mainMarket);
        newName = newName + "_" + RenameToolGenerator.getValue(RenameToolSettings.SN_TimeFrames, mainTF);
        newName = newName + (secondaryTF != null && !secondaryTF.equals(NO_VALUE) ? RenameToolGenerator.getValue(RenameToolSettings.SN_TimeFrames, secondaryTF) : "");
        newName = newName + "_" + magicNumber;
        newName = newName + "_" + orderType;
        newName = newName + "_" + indicator;
        newName = newName + (!closeType.isEmpty() ? "_" + closeType : "");
        newName = newName + (!timeRange.isEmpty() ? "_" + timeRange : "");
        newName = newName + "_" + strategyArchitecture;
        Log.info("Original name: " + originalName + " -> generater name: " + newName);
        Element elVariables = elStrategy.getChild("Variables");
        if (elVariables != null) {
            List variableElems = elVariables.getChildren("variable");
            for (int i = 0; i < variableElems.size(); ++i) {
                String variableName;
                Element elVariable = (Element)variableElems.get(i);
                Element elName = elVariable.getChild("name");
                if (elName == null || (variableName = elName.getTextTrim()) == null || !variableName.equals("MagicNumber")) continue;
                Element elValue = XMLUtil.tryAddElement((Element)elVariable, (String)"value");
                elValue.setText(magicNumber);
                break;
            }
        } else {
            Log.error("Cannot set magic number - element Variables is missing in strategy config");
        }
        rg.setName(newName);
    }

    private static String getValue(HashMap<String, String> valuesMap, String value) {
        if (value == null || value.equals(NO_VALUE)) {
            return NO_VALUE;
        }
        String containingValue = null;
        int matchingLetters = 0;
        for (String key : valuesMap.keySet()) {
            int keyLength;
            if (value.equals(key)) {
                return valuesMap.get(key);
            }
            if (!value.contains(key) || (keyLength = key.length()) <= matchingLetters) continue;
            containingValue = valuesMap.get(key);
            matchingLetters = keyLength;
        }
        if (containingValue != null) {
            return containingValue;
        }
        return NO_VALUE;
    }

    private static String getNumber(String value) {
        if (value == null || value.equals(NO_VALUE)) {
            return "99";
        }
        String temp = value;
        while (!temp.isEmpty() && temp.startsWith("0")) {
            temp = temp.substring(1);
        }
        try {
            Integer.valueOf(temp);
        }
        catch (Exception e) {
            return "99";
        }
        return value;
    }

    private static String getStrategyId(String originalName) {
        String namePrefix = "Strategy ";
        if (originalName != null && originalName.contains("Strategy ")) {
            int startIndex = originalName.indexOf("Strategy ");
            String tempName = originalName.substring(startIndex + "Strategy ".length());
            int idN = 0;
            for (int i = 0; i < tempName.length(); ++i) {
                try {
                    String number = tempName.substring(i, i + 1);
                    int n = Integer.parseInt(number);
                    idN = idN * 10 + n;
                    continue;
                }
                catch (Exception exception) {
                    // empty catch block
                }
            }
            return String.format("%05d", idN %= 100000);
        }
        return String.format("%05d", ++strategyNumber % 100000);
    }

    private static boolean isUsed(Element element) {
        String value = element.getTextTrim();
        boolean isUsed = false;
        try {
            isUsed = Boolean.parseBoolean(value);
        }
        catch (Exception exception) {
            // empty catch block
        }
        return isUsed;
    }

    private static String getTimeRangeHour(Element element) {
        try {
            int seconds = Integer.parseInt(element.getValue());
            return String.format("%02d", seconds / 3600);
        }
        catch (Exception e) {
            return NO_VALUE;
        }
    }
}

