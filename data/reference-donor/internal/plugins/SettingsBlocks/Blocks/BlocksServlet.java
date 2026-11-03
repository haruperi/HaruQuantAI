/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.utils.WizardConfigWorker
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.file.SQFileManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Blocks;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.utils.WizardConfigWorker;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlocksServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(BlocksServlet.class);
    private static final ArrayList<String> signalKeys = new ArrayList();

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList();
            }
            case "loadFromFile": {
                return this.onLoadFromFile(parameterMap);
            }
            case "saveToFile": {
                return this.onSaveToFile(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onList() throws Exception {
        JSONObject response = new JSONObject();
        try {
            Element wizardConfig = WizardConfigWorker.getWizardConfig();
            signalKeys.clear();
            response.put("orderTypes", (Object)this.getOrderTypes(wizardConfig));
            response.put("indicators", (Object)this.getIndicators(wizardConfig));
            response.put("priceRanges", (Object)this.getPriceRanges(wizardConfig));
            response.put("priceValues", (Object)this.getPriceValues(wizardConfig));
            response.put("operators", (Object)this.getOperators(wizardConfig));
            response.put("simpleRules", (Object)this.getSimpleRules(wizardConfig));
            response.put("others", (Object)this.getOthers(wizardConfig));
            response.put("exitTypes", (Object)this.getExitTypes(wizardConfig));
            response.put("formulas", (Object)this.getFormulas(wizardConfig));
            response.put("parameterSets", (Object)this.getParameterSets(wizardConfig));
            response.put("customBlocks", (Object)CustomBlocks.getAsBuildingBlocks());
        }
        catch (Exception e) {
            return BlocksServlet.apiErrorJSON((String)L.t((String)"Cannot list building blocks.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Blocks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadFromFile(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String filePath = this.tryGetParamValue(args, "filePath");
            response.put("blockSettings", (Object)SQFileManager.loadFile((String)filePath));
        }
        catch (Exception e) {
            return BlocksServlet.apiErrorJSON((String)L.t((String)"Cannot load block settings.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Settings loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveToFile(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String filePath = this.tryGetParamValue(args, "filePath");
            String fileContent = this.tryGetParamValue(args, "fileContent");
            SQFileManager.saveFile((String)filePath, (String)fileContent);
        }
        catch (Exception e) {
            return BlocksServlet.apiErrorJSON((String)L.t((String)"Cannot save block settings.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Settings saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray getOrderTypes(Element wizardConfig) throws Exception {
        JSONArray orderTypes = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromElement((Element)wizardConfig, (String)"Actions", null)) {
            orderTypes.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        return orderTypes;
    }

    private JSONArray getIndicators(Element wizardConfig) throws Exception {
        JSONArray indicators = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromCategory((Element)wizardConfig, (String)"Indicators", (String)"indicator")) {
            indicators.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        return indicators;
    }

    private JSONArray getPriceRanges(Element wizardConfig) throws Exception {
        JSONArray priceRanges = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromCategory((Element)wizardConfig, (String)"Indicators", (String)"priceRange")) {
            priceRanges.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        return priceRanges;
    }

    private JSONArray getPriceValues(Element wizardConfig) throws Exception {
        JSONArray priceValues = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromCategory((Element)wizardConfig, (String)"Price", (String)"priceValue")) {
            priceValues.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        return priceValues;
    }

    private JSONArray getOperators(Element wizardConfig) throws Exception {
        JSONArray operators = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromCategory((Element)wizardConfig, (String)"Comparisons", (String)"operators")) {
            operators.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        JSONObject andBlock = new JSONObject();
        andBlock.put("key", (Object)"AND");
        andBlock.put("name", (Object)"And");
        andBlock.put("group", (Object)"Other");
        andBlock.put("weight", 1);
        andBlock.put("use", false);
        JSONObject orBlock = new JSONObject();
        orBlock.put("key", (Object)"OR");
        orBlock.put("name", (Object)"Or");
        orBlock.put("group", (Object)"Other");
        orBlock.put("weight", 1);
        orBlock.put("use", false);
        operators.put((Object)andBlock);
        operators.put((Object)orBlock);
        return operators;
    }

    private JSONArray getSimpleRules(Element wizardConfig) throws Exception {
        JSONArray simpleRules = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromElement((Element)wizardConfig, (String)"Conditions", (String)"simpleRules")) {
            JSONObject signal = WizardConfigWorker.getBlockInfo((Element)elem, (int)1);
            simpleRules.put((Object)signal);
            signalKeys.add(signal.getString("key"));
        }
        return simpleRules;
    }

    private JSONArray getOthers(Element wizardConfig) throws Exception {
        JSONArray others = new JSONArray();
        for (Element elem : WizardConfigWorker.getElementsFromElement((Element)wizardConfig, (String)"Comparisons", (String)"other")) {
            others.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        for (Element elem : WizardConfigWorker.getElementsFromElement((Element)wizardConfig, (String)"Conditions", (String)"other")) {
            others.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        for (Element elem : WizardConfigWorker.getElementsFromElement((Element)wizardConfig, (String)"Values", (String)"other")) {
            others.put((Object)WizardConfigWorker.getBlockInfo((Element)elem, (int)1));
        }
        return others;
    }

    private JSONArray getExitTypes(Element wizardConfig) throws Exception {
        JSONArray exitTypes = new JSONArray();
        Element exitRulesElem = XMLUtil.findFirst((Element)wizardConfig, (String)"ExitRules");
        for (Element exitRuleElem : exitRulesElem.getChildren("ExitRule")) {
            try {
                exitTypes.put((Object)WizardConfigWorker.getSpecialItemInfo((Element)exitRuleElem));
            }
            catch (Exception e) {
                Log.error("Cannot get exit rule details. ", (Throwable)e);
            }
        }
        return exitTypes;
    }

    private JSONArray getFormulas(Element wizardConfig) throws Exception {
        JSONArray formulas = new JSONArray();
        Element formulasElem = XMLUtil.findFirst((Element)wizardConfig, (String)"Formulas");
        for (Element formulaElem : formulasElem.getChildren("Formula")) {
            try {
                formulas.put((Object)WizardConfigWorker.getSpecialItemInfo((Element)formulaElem));
            }
            catch (Exception e) {
                Log.error("Cannot get formula details. ", (Throwable)e);
            }
        }
        return formulas;
    }

    private JSONArray getParameterSets(Element wizardConfig) throws Exception {
        JSONArray parameterSets = new JSONArray();
        Element elParamSets = wizardConfig.getChild("ParameterSets");
        if (elParamSets != null) {
            for (Element elItem : elParamSets.getChildren("Item")) {
                JSONObject blockObj = new JSONObject();
                JSONArray paramSetsArray = new JSONArray();
                String blockKey = elItem.getAttributeValue("key");
                for (Element elSet : elItem.getChildren("Set")) {
                    JSONObject setObj = new JSONObject();
                    try {
                        int weight = Integer.parseInt(elSet.getAttributeValue("weight"));
                        weight = weight >= 0 ? weight : (signalKeys.contains(blockKey) ? 10 : 1);
                        setObj.put("weight", weight);
                        setObj.put("values", (Object)elSet.getAttributeValue("values"));
                        paramSetsArray.put((Object)setObj);
                    }
                    catch (Exception e) {
                        Log.error("Invalid parameter set settings. Block: '" + blockKey + "', settings: '" + elSet.getAttributeValue("values") + "'", (Throwable)e);
                    }
                }
                blockObj.put("block", (Object)blockKey);
                blockObj.put("paramSets", (Object)paramSetsArray);
                parameterSets.put((Object)blockObj);
            }
        }
        return parameterSets;
    }

    public String loadStockpickerDefaultBlocks() {
        try {
            File templateFile = new File(SQPaths.simpleTemplatesDirPath + "/DefaultStockpicker.xml");
            if (!templateFile.exists()) {
                throw new Exception(L.t((String)"Template file '%s' not found.", (Object[])new Object[]{templateFile.getName()}));
            }
            Element elTask = XMLUtil.fileToXmlElement((File)templateFile);
            Element elSettings = elTask.getChild("Settings");
            Element elBlocks = elSettings.getChild("Blocks");
            return XMLUtil.elementToString((Element)elBlocks);
        }
        catch (Exception e) {
            Log.error("Cannot load stockpicker default blocks.", (Throwable)e);
            return new JSONObject().toString();
        }
    }
}

