/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.metatrader4.MT4Utils
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.settings.ParametrizationSettings
 *  com.strategyquant.lib.sourcecode.MissingBlockMessage
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.WalkForwardPeriod
 *  com.strategyquant.tradinglib.WalkForwardResult
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList
 *  com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StrategySaver
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.strategy.SizingMetadata
 *  com.strategyquant.tradinglib.strategy.xml.StrategyFixer
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.SourceCode;

import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.metatrader4.MT4Utils;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.settings.ParametrizationSettings;
import com.strategyquant.lib.sourcecode.MissingBlockMessage;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategySaver;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.strategy.SizingMetadata;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixer;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.awt.Desktop;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SourceCodeServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SourceCodeServlet.class);
    private static final String TYPE_TRADESTATION = "EasyLanguage for Tradestation / MultiCharts (*.el)";
    private static final String CODE_TRADESTATION = "EasyLanguage for Tradestation (*.el)";
    private static final String CODE_MULTICHARTS = "EasyLanguage for MultiCharts (*.pla)";
    private static final String TYPE_PSEUDO_CODE = "Pseudo Code(*.TXT)";
    private static final String LOCK_SOURCESERVLET = "SourceCodeServlet";
    private static IResultsGroupProvider rgProvider;

    public SourceCodeServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(parameterMap);
            }
            case "list": {
                return new JSONObject().put("engineTypes", (Object)this.onList()).toString();
            }
            case "getDataPath": {
                return this.onGetDataPath(parameterMap);
            }
            case "saveMTPaths": {
                return this.onSaveMTPaths(parameterMap);
            }
            case "saveEA": {
                return this.onSaveEA(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONArray onListMM() {
        JSONArray methods = new JSONArray();
        JSONObject methodObj = new JSONObject();
        methodObj.put("name", (Object)"From strategy");
        methodObj.put("value", (Object)"fromStrategy");
        methods.put((Object)methodObj);
        for (MoneyManagementMethod method : MoneyManagementMethodsList.get().getAvailableClasses()) {
            methodObj = new JSONObject();
            methodObj.put("name", (Object)method.getName());
            methodObj.put("value", (Object)method.getClass().getSimpleName());
            methods.put((Object)methodObj);
        }
        return methods;
    }

    static void canonicalizeStoredType() {
        try {
            String stored = MainApp.settings().get("sourceCodeType");
            Log.debug("Checking remembered source code type: '{}'", (Object)stored);
            if (stored == null || stored.isEmpty()) {
                return;
            }
            SourceCodeGenerator generator = SourceCodeGenerators.getInstance().getGeneratorFromName(stored);
            if (generator == null) {
                Log.debug("Remembered source code type '{}' matches no generator - left as is", (Object)stored);
                return;
            }
            if (!generator.getName().equals(stored)) {
                Log.info("Remembered source code type '{}' uses an older generator name, updating to '{}'", (Object)stored, (Object)generator.getName());
                MainApp.settings().set("sourceCodeType", generator.getName());
                MainApp.settings().save();
            }
        }
        catch (Exception e) {
            Log.error("Could not canonicalize the remembered source code type", (Throwable)e);
        }
    }

    public synchronized JSONArray onList() throws Exception {
        JSONArray generatorsArray = new JSONArray();
        List generators = SourceCodeGenerators.getInstance().getAvailableGenerators();
        JSONObject tradestation = new JSONObject();
        tradestation.put("name", (Object)TYPE_TRADESTATION);
        tradestation.put("key", (Object)"EasyLanguage");
        JSONObject tradestationExtension = new JSONObject();
        tradestationExtension.put("name", (Object)CODE_TRADESTATION);
        tradestationExtension.put("types", (Object)"el");
        JSONObject multichartsExtension = new JSONObject();
        multichartsExtension.put("name", (Object)CODE_MULTICHARTS);
        multichartsExtension.put("types", (Object)"pla");
        tradestation.put("extension", (Object)new JSONArray().put((Object)tradestationExtension).put((Object)multichartsExtension));
        tradestation.put("desc", (Object)L.tsq((String)"Saves Strategy EasyLanguage code."));
        generatorsArray.put((Object)tradestation);
        for (SourceCodeGenerator generator : generators) {
            JSONObject item = new JSONObject();
            String generatorName = generator.getName();
            if (generatorName.contains("EasyLanguage")) continue;
            item.put("name", (Object)generatorName);
            item.put("key", (Object)generator.getKey());
            String[] ext = generator.getFileExtension();
            JSONObject extension = new JSONObject();
            extension.put("name", (Object)ext[0]);
            extension.put("types", (Object)ext[1]);
            item.put("extension", (Object)extension);
            item.put("desc", (Object)generator.getDescription());
            generatorsArray.put((Object)item);
        }
        if (!"BACKTESTNODE".equals(MainApp.getProduct())) {
            JSONObject item = new JSONObject();
            item.put("name", (Object)"Strategy XML");
            JSONObject extension = new JSONObject();
            extension.put("name", (Object)"XML Document");
            extension.put("types", (Object)"xml");
            item.put("extension", (Object)extension);
            item.put("desc", (Object)L.tsq((String)"Saves Strategy XML code."));
            generatorsArray.put((Object)item);
        }
        return generatorsArray;
    }

    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        String code;
        JSONObject response = new JSONObject();
        String warning = null;
        String learnMoreURL = null;
        try {
            String[] data = this.getSourceCode(parameterMap, false);
            code = data[0];
            warning = data[1];
            learnMoreURL = data[2];
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            return SourceCodeServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            return SourceCodeServlet.apiErrorJSONNoLog((String)L.t((String)"Source code generation failed.", (Object[])new Object[0]), (Exception)e);
        }
        response.put("code", (Object)code);
        response.put("warning", (Object)warning);
        response.put("learnMoreURL", (Object)learnMoreURL);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private static String normalizeEngineName(String name) {
        if (name == null) {
            return "";
        }
        return name.replaceAll("\\s+", "").toLowerCase();
    }

    static String getLastSettingsParam(Map<String, String[]> parameterMap) {
        String[] values = parameterMap.get("lastSettingsXML");
        if (values == null || values.length == 0 || values[0] == null || values[0].trim().isEmpty()) {
            return null;
        }
        return values[0];
    }

    /*
     * Loose catch block
     */
    private String[] getSourceCode(Map<String, String[]> parameterMap, boolean forceGeneration) throws Exception {
        String code;
        ValuesMap parametrizationSettings;
        String mmType;
        boolean symmetricVariables;
        boolean useVariables;
        String _strategy;
        String lastSettings;
        ResultsGroup rg;
        Element rgEl;
        SizingMetadata sizing;
        String learnMoreURL;
        String warning;
        String _type;
        block38: {
            String[] stringArray;
            block41: {
                block39: {
                    String[] stringArray2;
                    block40: {
                        AbstractBroker broker;
                        this.checkParamExists(parameterMap, new String[]{"type", "symmetricVariables", "mmType"});
                        _type = SourceCodeGenerators.getInstance().canonicalize(parameterMap.get("type")[0].toString());
                        if (_type.equals(CODE_TRADESTATION) || _type.equals(CODE_MULTICHARTS)) {
                            _type = TYPE_TRADESTATION;
                        }
                        if (!forceGeneration && (broker = MainApp.getLicenseInfo().getBroker()) != null && broker.usesEAEncryption() && !_type.equals(TYPE_PSEUDO_CODE)) {
                            throw new Exception(L.t((String)"Option not supported for current broker", (Object[])new Object[0]));
                        }
                        warning = null;
                        learnMoreURL = null;
                        Map params = this.getParameters(null, parameterMap);
                        Map rgParams = this.getRgParams(params);
                        sizing = SizingMetadata.FALLBACK;
                        rgEl = this.getStrategyElement(parameterMap);
                        rg = null;
                        try {
                            rg = rgProvider.get(rgParams, LOCK_SOURCESERVLET);
                        }
                        catch (Exception e) {
                            Log.debug("Unable to load ResultsGroup from URL params (It is ok for AW template)", (Throwable)e);
                        }
                        String string = lastSettings = rg != null ? rg.getLastSettings() : SourceCodeServlet.getLastSettingsParam(parameterMap);
                        if (lastSettings != null && !_type.equals("Strategy XML") && !_type.equals(TYPE_PSEUDO_CODE)) {
                            try {
                                Element elSettings = XMLUtil.stringToElement((String)lastSettings);
                                Element elSetup = elSettings.getChild("Data").getChild("Setups").getChild("Setup");
                                String engine = elSetup.getAttributeValue("engine");
                                if (engine.contains("(")) {
                                    engine = engine.substring(0, engine.indexOf("(") + 1);
                                }
                                if (!SourceCodeServlet.normalizeEngineName(_type).contains(SourceCodeServlet.normalizeEngineName(engine))) {
                                    warning = L.t((String)"Note - this strategy was backtested with %s engine, but you are showing code for %s. Make sure you retest it with this engine before trading in your platform.", (Object[])new Object[]{engine, _type});
                                }
                                sizing = SizingMetadata.resolveFromSettings((String)lastSettings, (String)"source code");
                            }
                            catch (Exception e) {
                                Log.error("Exc.", (Throwable)e);
                            }
                        }
                        _strategy = null;
                        try {
                            _strategy = parameterMap.get("strategy")[0].toString();
                        }
                        catch (Exception e) {
                            _strategy = null;
                        }
                        useVariables = true;
                        symmetricVariables = Boolean.parseBoolean(parameterMap.get("symmetricVariables")[0].toString());
                        mmType = parameterMap.get("mmType")[0].toString();
                        parametrizationSettings = this.getParametrizationSettings(parameterMap);
                        MainApp.settings().set("sourceCodeType", _type);
                        MainApp.settings().set("sourceCodeVariables", useVariables + "");
                        MainApp.settings().set("sourceCodeSymmetry", symmetricVariables + "");
                        code = "NA";
                        if (rgEl == null) {
                            throw new Exception(L.t((String)"Strategy doesn't contain XML source code.", (Object[])new Object[0]));
                        }
                        if (_type.equals("Strategy XML") || _type.equals(TYPE_PSEUDO_CODE)) break block38;
                        String pickerEditor = rgEl.getChild("Strategy").getAttributeValue("pickerEditor");
                        if (pickerEditor == null || !pickerEditor.equals("true")) break block39;
                        code = "BACKTESTNODE".equals(MainApp.getProduct()) ? L.t((String)"Stockpicker strategies are not supported for this platform.", (Object[])new Object[0]) + "\n\n" + L.t((String)"You can trade it by saving to My strategies and deploying to Live/Paper account from there", (Object[])new Object[0]) : L.t((String)"Stockpicker strategies are not supported for this platform.", (Object[])new Object[0]) + "\n\n" + L.t((String)"You can see its Pseudo code, but live trading will be supported only in our new cloud trading platform https://algocloud.com", (Object[])new Object[0]);
                        stringArray2 = new String[]{code, null, null};
                        if (rg == null) break block40;
                        rg.releaseLock(LOCK_SOURCESERVLET);
                    }
                    return stringArray2;
                }
                if (!StrategyFixer.isTemplate((Element)rgEl)) break block38;
                code = L.t((String)"This is a template of a strategy, not a complete strategy. It is visible only in Pseudo code.", (Object[])new Object[0]);
                stringArray = new String[]{code, null, null};
                if (rg == null) break block41;
                rg.releaseLock(LOCK_SOURCESERVLET);
            }
            return stringArray;
        }
        try {
            block42: {
                break block42;
                {
                    catch (Exception e) {
                        Log.error("Exc.", (Throwable)e);
                    }
                }
            }
            boolean isMergedResult = this.recognizeMergedResult(rgEl);
            StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)rgEl);
            if (useVariables) {
                xmlS.transformToVariables(symmetricVariables, parametrizationSettings);
                xmlS.variables().sortByName();
            } else {
                xmlS.transformToNumbers();
            }
            if (_strategy == null || _strategy.trim().isEmpty()) {
                try {
                    _strategy = rgEl.getChild("options").getChild("StrategyName").getValue();
                    if (_strategy == null || _strategy.trim().isEmpty()) {
                        _strategy = "AlgoWizardStrategy";
                    }
                }
                catch (Exception e) {
                    _strategy = "AlgoWizardStrategy";
                }
            }
            rgEl = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)rg, (Element)rgEl, (String)mmType, (String)(rg != null ? rg.getName() : _strategy), (String)lastSettings, null);
            if (StrategySaver.isMetaTraderGenerator((String)_type)) {
                StrategySaver.normalizeExportSymbols((Element)rgEl);
            }
            XMLIndicatorsAnalyzer.init();
            XMLIndicatorsAnalyzer.fixItemAttributes((Element)rgEl);
            if (_type.equals("Strategy XML")) {
                CustomDataManager.addCDataIndySourceCodes((Element)rgEl);
                CustomBlocks.addCBlockSourceCodes((Element)rgEl);
                code = XMLUtil.elementToString((Element)rgEl);
            } else {
                SourceCodeGenerator sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(_type);
                if (sourceCodeGenerator != null) {
                    Log.debug("Generating {}", (Object)sourceCodeGenerator.getName());
                    CustomDataManager.addCDataIndySourceCodes((Element)rgEl);
                    CustomBlocks.addCBlockSourceCodes((Element)rgEl);
                    if (this.checkMMAllowed(rgEl, _type)) {
                        code = sourceCodeGenerator.getSource(_strategy, rgEl, sizing.orderSizeMultiplier, sizing.orderSizeStep, sizing.pointValue, sizing.barTimeType);
                        if (_type.equals(TYPE_TRADESTATION) && this.containsDuplicateEntries(rgEl)) {
                            warning = L.t((String)"Note - Tradestation/MultiCharts doesn't allow independent handling of multiple orders to the same direction, exits of these orders will be not applied correctly!", (Object[])new Object[0]);
                            learnMoreURL = "https://strategyquant.com/doc/strategyquant/multi-orders-to-same-direction";
                        }
                    } else {
                        code = L.t((String)"Unable to generate source code - the selected money management method has no template for this platform", (Object[])new Object[0]);
                    }
                }
            }
            if (isMergedResult) {
                warning = L.t((String)"Note - this is a merged portfolio. The strategy code here is the code of the very first startegy in portfolio. Merge functionality in SQ does not combine source codes of all strategies to one!", (Object[])new Object[0]);
            }
            String[] stringArray = new String[]{code, warning, learnMoreURL};
            return stringArray;
        }
        catch (Exception e) {
            String errorMessage = e.getMessage();
            if (MissingBlockMessage.matches((String)errorMessage)) {
                String code2 = MissingBlockMessage.format((String)errorMessage, (String)_type);
                warning = String.format(L.t((String)"Error! One or more blocks the strategy uses isn't implemented in %s.", (Object[])new Object[0]), this.getCodeType(_type));
                String[] stringArray = new String[]{code2, warning, learnMoreURL};
                return stringArray;
            }
            Log.error("Exc.", (Throwable)e);
            throw new Exception(L.t((String)"An error occured while generating the strategy XML source code.\nExc. ", (Object[])new Object[0]) + errorMessage);
        }
        catch (Throwable throwable) {
            throw throwable;
        }
        finally {
            if (rg != null) {
                rg.releaseLock(LOCK_SOURCESERVLET);
            }
        }
    }

    private ArrayList<String> getInputsToVarsFromLadder(ResultsGroup rg) {
        ArrayList<String> inputsToVars = new ArrayList<String>();
        WalkForwardMatrixResult mwfResult = null;
        try {
            mwfResult = (WalkForwardMatrixResult)rg.mainResult().get("WalkForwardResult");
            if (mwfResult != null) {
                WalkForwardResult wfResult = (WalkForwardResult)mwfResult.getResultList().get(0);
                ArrayList periods = wfResult.wfPeriods;
                if (periods.size() > 0) {
                    String[] params;
                    WalkForwardPeriod period = (WalkForwardPeriod)periods.get(0);
                    for (String param : params = period.testParameters.split(",")) {
                        inputsToVars.add(param);
                    }
                }
            }
        }
        catch (Exception e) {
            Log.info("Cannot create Data ladder", (Throwable)e);
        }
        return inputsToVars;
    }

    private void createLadderEntry(StringBuilder sb, WalkForwardPeriod period) {
        String[] params;
        int d1 = SQTime.getDay((long)period.runFrom);
        int m1 = SQTime.getMonth((long)period.runFrom) + 1;
        int y1 = SQTime.getYear((long)period.runFrom) + 1900;
        int d2 = SQTime.getDay((long)period.runTo);
        int m2 = SQTime.getMonth((long)period.runTo) + 1;
        int y2 = SQTime.getYear((long)period.runTo) + 1900;
        String date = String.format("if date >= ELDate(%d, %d, %d)  and date <= ELDate(%d, %d, %d) then begin\n", m1, d1, y1, m2, d2, y2);
        sb.append(date);
        for (String param : params = period.testParameters.split(",")) {
            sb.append("        ");
            sb.append(param);
            sb.append(";\n");
        }
        sb.append("end;\n");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private Element getStrategyElement(Map<String, String[]> parameterMap) throws Exception {
        String strategyXML = null;
        try {
            strategyXML = parameterMap.get("strategyXML")[0].toString();
        }
        catch (Exception exception) {
            // empty catch block
        }
        Map params = this.getParameters(null, parameterMap);
        Map rgParams = this.getRgParams(params);
        Element rgEl = null;
        ResultsGroup rg = null;
        try {
            try {
                rg = rgProvider.get(rgParams, LOCK_SOURCESERVLET);
            }
            catch (Exception e) {
                Log.debug("Unable to load ResultsGroup from URL params (It is ok for AW template)", (Throwable)e);
            }
            if (strategyXML == null || strategyXML.isEmpty()) {
                if (rg != null) {
                    rgEl = rg.portfolio().getStrategyXml();
                    if (rgEl != null) {
                        rgEl = rgEl.clone();
                    } else {
                        Log.error("Cannot get strategy XML from ResultsGroup - getStrategyXml() returned null");
                    }
                }
            } else {
                rgEl = XMLUtil.stringToElement((String)strategyXML);
            }
        }
        finally {
            if (rg != null) {
                rg.releaseLock(LOCK_SOURCESERVLET);
            }
        }
        return rgEl;
    }

    private boolean checkMMAllowed(Element rgEl, String sourceCodeType) throws Exception {
        Element elMoneyManagement = rgEl.getChild("Strategy").getChild("MoneyManagement");
        String mmType = elMoneyManagement.getAttributeValue("type");
        SourceCodeGenerator generator = SourceCodeGenerators.getInstance().getGeneratorFromName(sourceCodeType);
        if (generator == null) {
            return true;
        }
        return generator.supportsMoneyManagement(mmType);
    }

    private String getCodeType(String type) {
        return MissingBlockMessage.languageName((String)type);
    }

    private boolean recognizeMergedResult(Element rgEl) {
        String mergedResult = rgEl.getAttributeValue("mergedResult");
        return mergedResult != null && mergedResult.equals("true");
    }

    private ValuesMap getParametrizationSettings(Map<String, String[]> parameterMap) {
        String type = parameterMap.get("type")[0].toString();
        boolean periodParams = this.getBool(parameterMap, "periodParams");
        boolean constantsParams = this.getBool(parameterMap, "constantsParams");
        boolean shiftParams = this.getBool(parameterMap, "shiftParams");
        boolean otherParams = this.getBool(parameterMap, "otherParams");
        boolean entryParams = this.getBool(parameterMap, "entryParams");
        boolean entryLogic = this.getBool(parameterMap, "entryLogic");
        boolean exitParamsUsed = this.getBool(parameterMap, "exitParamsUsed");
        boolean exitParamsUnused = this.getBool(parameterMap, "exitParamsUnused");
        boolean booleanParams = this.getBool(parameterMap, "booleanParams");
        boolean symmetricVariables = this.getBool(parameterMap, "symmetricVariables");
        boolean recommendedParams = this.getBool(parameterMap, "recommendedParams");
        JSONObject config = new JSONObject();
        config.put("periodParams", periodParams);
        config.put("constantsParams", constantsParams);
        config.put("shiftParams", shiftParams);
        config.put("otherParams", otherParams);
        config.put("entryParams", entryParams);
        config.put("entryLogic", entryLogic);
        config.put("exitParamsUsed", exitParamsUsed);
        config.put("exitParamsUnused", exitParamsUnused);
        config.put("booleanParams", booleanParams);
        config.put("symmetricVariables", symmetricVariables);
        config.put("recommendedParams", recommendedParams);
        MainApp.settings().set(ParametrizationSettings.getSettingKey((String)type), config.toString());
        ValuesMap settings = new ValuesMap();
        settings.set("ParamTypePeriod", (Object)periodParams);
        settings.set("ParamTypeShift", (Object)shiftParams);
        settings.set("ParamTypeExitUsed", (Object)exitParamsUsed);
        settings.set("ParamTypeConstant", (Object)constantsParams);
        settings.set("ParamTypeOtherParam", (Object)otherParams);
        settings.set("ParamTypeEntryLevel", (Object)entryParams);
        settings.set("ParamTypeEntryLogic", (Object)entryLogic);
        settings.set("ParamTypeExitUnused", (Object)exitParamsUnused);
        settings.set("ParamTypeBoolean", (Object)booleanParams);
        settings.set("ParamTypeRecommended", (Object)recommendedParams);
        return settings;
    }

    private boolean getBool(Map<String, String[]> parameterMap, String paramName) {
        String[] vals = parameterMap.get(paramName);
        if (vals == null) {
            return false;
        }
        return Boolean.parseBoolean(vals[0]);
    }

    private String onGetDataPath(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String installPath = this.tryGetParamValue(parameterMap, "installPath");
        boolean isMT4 = Boolean.parseBoolean(this.tryGetParamValue(parameterMap, "isMT4"));
        File dataFolder = MT4Utils.getDataFolderFile();
        String dataPath = dataFolder.getAbsolutePath() + "\\" + MT4Utils.getTerminalHash((String)installPath) + (isMT4 ? "/MQL4/Experts" : "/MQL5/Experts");
        response.put("dataPath", (Object)dataPath);
        response.put("success", (Object)L.t((String)"Paths saved", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveMTPaths(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        if (parameterMap.get("mt4InstallPath") != null) {
            String mt4InstallPath = this.tryGetParamValue(parameterMap, "mt4InstallPath");
            MainApp.settings().set("mt4InstallPath", mt4InstallPath);
        }
        if (parameterMap.get("mt5InstallPath") != null) {
            String mt5InstallPath = this.tryGetParamValue(parameterMap, "mt5InstallPath");
            MainApp.settings().set("mt5InstallPath", mt5InstallPath);
        }
        if (parameterMap.get("mt4DataPath") != null) {
            String mt4DataPath = this.tryGetParamValue(parameterMap, "mt4DataPath");
            MainApp.settings().set("mt4DataPath", mt4DataPath);
        }
        if (parameterMap.get("mt5DataPath") != null) {
            String mt5DataPath = this.tryGetParamValue(parameterMap, "mt5DataPath");
            MainApp.settings().set("mt5DataPath", mt5DataPath);
        }
        MainApp.settings().save();
        response.put("success", (Object)L.t((String)"Paths saved", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveEA(Map<String, String[]> parameterMap) throws Exception {
        String dataFolderPath;
        JSONObject response = new JSONObject();
        Element rgEl = this.getStrategyElement(parameterMap);
        if (rgEl == null) {
            throw new Exception(L.t((String)"Strategy doesn't have any content", (Object[])new Object[0]));
        }
        String pickerEditor = rgEl.getChild("Strategy").getAttributeValue("pickerEditor");
        if (pickerEditor != null && pickerEditor.equals("true")) {
            throw new Exception(L.t((String)"Stockpicker strategies are not supported for MetraTrader platform.", (Object[])new Object[0]) + "\n" + L.t((String)"You can trade stockpicker strategies live at <a target='_blank' href='https://algowizard.io'>algowizard.io</a>", (Object[])new Object[0]));
        }
        boolean isMT4 = Boolean.parseBoolean(this.tryGetParamValue(parameterMap, "isMT4"));
        String metaeditorFolderPath = isMT4 ? MainApp.settings().get("mt4InstallPath") : MainApp.settings().get("mt5InstallPath");
        String metaeditorPath = metaeditorFolderPath + "/metaeditor.exe";
        if (!new File(metaeditorPath).exists() && !new File(metaeditorPath = metaeditorFolderPath + "/metaeditor64.exe").exists()) {
            return SourceCodeServlet.apiErrorJSON((String)L.t((String)"Cannot find metaeditor.exe. Please check your MetaTrader installation path", (Object[])new Object[0]), null);
        }
        String string = dataFolderPath = isMT4 ? MainApp.settings().get("mt4DataPath") : MainApp.settings().get("mt5DataPath");
        if (!new File(dataFolderPath).exists()) {
            return SourceCodeServlet.apiErrorJSON((String)L.t((String)"MetaTrader data folder doesn't exist. Please check your settings", (Object[])new Object[0]), null);
        }
        String strategyName = null;
        try {
            strategyName = parameterMap.get("strategy")[0].toString();
        }
        catch (Exception e) {
            strategyName = "AlgoWizardStrategy";
        }
        String mqlPath = dataFolderPath + "/" + strategyName + (isMT4 ? ".mq4" : ".mq5");
        File mqlFile = new File(mqlPath);
        String eaPath = dataFolderPath + "/" + strategyName + (isMT4 ? ".ex4" : ".ex5");
        parameterMap.put("type", new String[]{isMT4 ? SourceCodeGenerator.MetaTrader4 : SourceCodeGenerator.MetaTrader5});
        String code = this.getSourceCode(parameterMap, true)[0];
        String projectName = this.tryGetParam(parameterMap, "project")[0];
        if (projectName.equals("AlgoWizard")) {
            projectName = "Retester";
        }
        SQProject project = ProjectEngine.get((String)projectName);
        try {
            SQUtils.stringToFile((File)mqlFile, (String)code);
            project.getProgress().update("saveEA", 20.0, null);
            String cmd = metaeditorPath + " /compile:\"" + mqlPath.replace("/", "\\") + "\" /log";
            Log.debug("---- Running command: " + cmd);
            Process proc = Runtime.getRuntime().exec(cmd);
            if (!proc.waitFor(20L, TimeUnit.SECONDS)) {
                Log.error("Command '" + cmd + "' failed!");
                mqlFile.delete();
                String message = L.t((String)"MQL compilation timed out", (Object[])new Object[0]);
                project.getProgress().update("saveEA", 100.0, message);
                return SourceCodeServlet.apiErrorJSON((String)message, null);
            }
            mqlFile.delete();
            File eaFile = new File(eaPath);
            if (!eaFile.exists()) {
                String message = L.t((String)"EA was not created. Compilation failed", (Object[])new Object[0]);
                project.getProgress().update("saveEA", 100.0, message);
                return SourceCodeServlet.apiErrorJSON((String)message, null);
            }
            project.getProgress().update("saveEA", 100.0, null);
            Desktop.getDesktop().open(eaFile.getParentFile());
            response.put("success", (Object)L.t((String)"EA saved", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            project.getProgress().update("saveEA", 100.0, e.getMessage());
            throw e;
        }
    }

    private boolean containsDuplicateEntries(Element elStrategy) {
        try {
            ArrayList items = XMLUtil.getNestedElements((Element)elStrategy, (String)"Item");
            int longCount = 0;
            int shortCount = 0;
            for (int a = 0; a < items.size(); ++a) {
                Element elItem = (Element)items.get(a);
                String key = elItem.getAttributeValue("key");
                if (key == null || !key.startsWith("EnterAt")) continue;
                Element elParamDirection = XMLUtil.getItemParameterNoException((Element)elItem, (String)"#Direction#");
                if (elParamDirection != null) {
                    try {
                        int value = Integer.parseInt(elParamDirection.getText());
                        if (value == 1) {
                            ++longCount;
                        } else if (value == -1) {
                            ++shortCount;
                        }
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
                if (longCount <= 1 && shortCount <= true) continue;
                return true;
            }
        }
        catch (Exception e) {
            Log.error("Error while checking duplicate entries", (Throwable)e);
        }
        return false;
    }
}

