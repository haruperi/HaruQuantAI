/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.settings.ParametrizationSettings
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.pluginlib.ISQPlugin
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.program.IProgram
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.settings.ParametrizationSettings;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.results.file.FileHandler;
import com.strategyquant.tradinglib.results.file.ISaverPlugin;
import java.io.File;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategySaver {
    public static final Logger Log = LoggerFactory.getLogger(StrategySaver.class);
    private int index = 0;
    private IProgram saver = new FileHandler();

    public void resetCounting() {
        this.index = 0;
    }

    public void save(ResultsGroup resultsGroup, String string, String string2, boolean bl, int n) throws Exception {
        this.save(resultsGroup, string, string2, bl, n, null);
    }

    public void save(ResultsGroup resultsGroup, String string, String string2, boolean bl, int n, Map<String, String[]> map) throws Exception {
        this.save(resultsGroup, string, string2, bl, n, null, map, false);
    }

    public void save(ResultsGroup resultsGroup, String string, String string2, boolean bl, int n, SourceCodeGenerator sourceCodeGenerator, Map<String, String[]> map, boolean bl2) throws Exception {
        boolean bl3 = false;
        if (map != null && map.containsKey("extension[description]")) {
            boolean bl4 = bl3 = map.get("extension[description]")[0].toLowerCase().contains("brazil") || map.get("extension[description]")[0].toLowerCase().contains("brasil");
        }
        if (sourceCodeGenerator != null) {
            bl3 = sourceCodeGenerator.isBrazilianVersion();
        }
        if (string == null) {
            throw new Exception("File format (extension) cannot be null.");
        }
        switch (string) {
            case "sq4": 
            case "sqx": {
                this.saveStrategy(resultsGroup, string2, bl, n, map);
                break;
            }
            case "xml": {
                this.saveConfig(resultsGroup, string2);
                break;
            }
            case "txt": {
                this.saveCode(resultsGroup, string2, SourceCodeGenerator.PseudoCode, bl, n);
                break;
            }
            case "mq4": {
                this.saveCode(resultsGroup, string2, SourceCodeGenerator.MetaTrader4, bl, n);
                break;
            }
            case "mq5": {
                if (bl3) {
                    this.saveCode(resultsGroup, string2, SourceCodeGenerator.MetaTrader5BR, bl, n);
                    break;
                }
                this.saveCode(resultsGroup, string2, SourceCodeGenerator.MetaTrader5, bl, n);
                break;
            }
            case "java": {
                this.saveCode(resultsGroup, string2, SourceCodeGenerator.JForex, bl, n);
                break;
            }
            case "el": {
                this.saveELCode(resultsGroup, string2, bl, n, false);
                break;
            }
            case "pla": {
                this.saveELCode(resultsGroup, string2, bl, n, true);
                break;
            }
            default: {
                this.saveUsingPlugins(resultsGroup, string, string2, map, bl2);
            }
        }
    }

    private void saveUsingPlugins(ResultsGroup resultsGroup, String string, String string2, Map<String, String[]> map, boolean bl) throws Exception {
        Throwable throwable = null;
        ArrayList arrayList = SQPluginManager.getPlugins(ISaverPlugin.class);
        for (ISaverPlugin iSaverPlugin : arrayList) {
            String string3 = SQPluginManager.getPluginName((ISQPlugin)iSaverPlugin);
            try {
                String[] stringArray = iSaverPlugin.getFileExtensions();
                if (stringArray == null || stringArray.length <= 0) continue;
                for (int i = 0; i < stringArray.length; ++i) {
                    if (!stringArray[i].equalsIgnoreCase(string)) continue;
                    if (bl) {
                        iSaverPlugin = iSaverPlugin.clone();
                    }
                    iSaverPlugin.save(resultsGroup, string2, map);
                    return;
                }
            }
            catch (Exception exception) {
                throwable = exception;
                if (!Log.isDebugEnabled()) continue;
                Log.debug(" - Save using {} failed with exception: {}", (Object)string3, (Object)exception.getMessage());
            }
        }
        if (throwable == null) {
            throw new Exception("No plugin found for saving strategy to '" + string + "'.");
        }
        throw new Exception(throwable.getMessage());
    }

    private void saveStrategy(ResultsGroup resultsGroup, String string, boolean bl, int n, Map<String, String[]> map) throws Exception {
        if (bl) {
            ResultsGroup resultsGroup2 = resultsGroup.clone();
            Element element = resultsGroup2.getStrategyXml();
            Element element2 = XMLUtil.getChildElem((Element)element, (String)"Strategy");
            Element element3 = XMLUtil.getChildElem((Element)element2, (String)"Variables");
            List list = element3.getChildren("variable");
            for (int i = 0; i < list.size(); ++i) {
                Element element4 = (Element)list.get(i);
                String string2 = XMLUtil.getChildElem((Element)element4, (String)"name").getText();
                if (string2 == null || !string2.equals("MagicNumber")) continue;
                XMLUtil.getChildElem((Element)element4, (String)"value").setText("" + (n + this.index++));
            }
            resultsGroup2.portfolio().addStrategyXml(element);
            this.saver.call("saveFile", new Object[]{resultsGroup2, string, true, map});
        } else {
            this.saver.call("saveFile", new Object[]{resultsGroup, string, true, map});
        }
    }

    private void saveStrategy(Element element, String string) throws Exception {
        this.saver.call("saveStrategyFile", new Object[]{element, string, true});
    }

    private void saveConfig(ResultsGroup resultsGroup, String string) throws Exception {
        AbstractBroker abstractBroker = MainApp.v571hfnsHw().inygRmSMx7();
        if (abstractBroker != null && abstractBroker.usesEAEncryption()) {
            throw new Exception(L.t((String)"Action not supported for current broker", (Object[])new Object[0]));
        }
        Element element = StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup);
        SQUtils.stringToFile((String)string, (String)XMLUtil.elementToString((Element)element));
    }

    private void saveCode(ResultsGroup resultsGroup, String string, String string2, boolean bl, int n) throws Exception {
        String string3 = this.getSourceCode(resultsGroup, string2, string);
        if (bl) {
            int n2 = 0;
            int n3 = 0;
            String string4 = "int MagicNumber";
            while ((n3 = string3.indexOf(string4, n2)) >= 0) {
                int n4;
                n2 = n3 + 1;
                int n5 = string3.indexOf(" = ", n3);
                if (n5 < 0 || (n4 = string3.indexOf(";", n5)) < 0) continue;
                string3 = string3.substring(0, n5 + 3) + (n + this.index++) + string3.substring(n4);
            }
        }
        SQUtils.stringToFile((String)string, (String)string3);
    }

    private void saveELCode(ResultsGroup resultsGroup, String string, boolean bl, int n, boolean bl2) throws Exception {
        String string2 = this.getSourceCode(resultsGroup, SourceCodeGenerator.EasyLanguage, string);
        if (bl) {
            int n2 = 0;
            int n3 = 0;
            String string3 = "MagicNumber(";
            while ((n3 = string2.indexOf(string3, n2)) >= 0) {
                n2 = n3 + string3.length();
                int n4 = string2.indexOf(")", n2);
                if (n4 < 0) {
                    throw new Exception("MagicNumber param end bracket not found");
                }
                string2 = string2.substring(0, n2) + (n + this.index++) + string2.substring(n4);
            }
        }
        File file = new File(string);
        if (bl2) {
            String string4 = SQUtils.stripExtension((String)file.getName());
            string2 = StrategySaver.getPLAContent(string4, string2);
        }
        SQUtils.stringToFile((File)file, (String)string2);
    }

    public static String getPLAContent(String string, String string2) {
        string = string == null ? "SQStrategy" : string.replaceAll("[^A-Za-z0-9_]", "");
        String string3 = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\r\n<Graph>\r\n\t<GraphNode>\r\n\t\t<data first=\"s_" + string + "\" second=\"7\"/>\r\n\t\t<signature ObligatoryParamCount=\"0\" RetType=\"0\" StorageType=\"32\"/>\r\n\t\t<StudyProperties BarRefMode=\"1\" BarRefValue=\"50\" SaveAsSymbol=\"0\" SemilogAxis=\"1\" SkipIdentTicks=\"1\" UpdateOnEveryTick=\"1\"/>\r\n\t\t<PasswordState IsProtectedByPassword=\"0\" Password=\"1B2M2Y8AsgTpgAmY7PhCfg==\"/>\r\n\t\t<NodeText Encoded=\"1\">";
        String string4 = Base64.getEncoder().encodeToString(string2.getBytes());
        for (int i = 76; i < string4.length(); i += 77) {
            string4 = string4.substring(0, i) + "\n" + string4.substring(i);
        }
        string3 = string3 + string4 + "</NodeText>\r\n\t</GraphNode>\r\n</Graph>";
        return string3;
    }

    private String getSourceCode(ResultsGroup resultsGroup, String string, String string2) throws Exception {
        Object object;
        Element element;
        block15: {
            AbstractBroker abstractBroker = MainApp.v571hfnsHw().inygRmSMx7();
            if (abstractBroker != null && abstractBroker.usesEAEncryption()) {
                throw new Exception(L.t((String)"Action not supported for current broker", (Object[])new Object[0]));
            }
            element = StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup, "fromStrategy", string2);
            if (StrategySaver.isMetaTraderGenerator(string)) {
                StrategySaver.normalizeExportSymbols(element);
            }
            try {
                String string3 = ParametrizationSettings.getSettingKey((String)string);
                if (!MainApp.settings().containsKey(string3)) break block15;
                JSONObject jSONObject = new JSONObject(MainApp.settings().get(string3));
                ValuesMap valuesMap = new ValuesMap();
                valuesMap.set("ParamTypePeriod", (Object)jSONObject.getBoolean("periodParams"));
                valuesMap.set("ParamTypeShift", (Object)jSONObject.getBoolean("shiftParams"));
                valuesMap.set("ParamTypeExitUsed", (Object)jSONObject.getBoolean("exitParamsUsed"));
                valuesMap.set("ParamTypeConstant", (Object)jSONObject.getBoolean("constantsParams"));
                valuesMap.set("ParamTypeOtherParam", (Object)jSONObject.getBoolean("otherParams"));
                valuesMap.set("ParamTypeEntryLevel", (Object)jSONObject.getBoolean("entryParams"));
                valuesMap.set("ParamTypeEntryLogic", (Object)jSONObject.getBoolean("entryLogic"));
                valuesMap.set("ParamTypeExitUnused", (Object)jSONObject.getBoolean("exitParamsUnused"));
                valuesMap.set("ParamTypeBoolean", (Object)jSONObject.getBoolean("booleanParams"));
                valuesMap.set("ParamTypeRecommended", (Object)jSONObject.getBoolean("recommendedParams"));
                boolean bl = false;
                try {
                    bl = Boolean.parseBoolean(MainApp.settings().get("sourceCodeVariables"));
                }
                catch (Exception exception) {
                    // empty catch block
                }
                boolean bl2 = true;
                try {
                    bl2 = Boolean.parseBoolean(MainApp.settings().get("sourceCodeSymmetry"));
                }
                catch (Exception exception) {
                    // empty catch block
                }
                object = StrategyBase.createXmlStrategy(element);
                if (bl) {
                    ((StrategyBase)object).transformToVariables(bl2, valuesMap);
                    ((StrategyBase)object).variables().sortByName();
                } else {
                    ((StrategyBase)object).transformToNumbers();
                }
            }
            catch (Exception exception) {
                Log.error("Failed to apply parametrization settings", (Throwable)exception);
            }
        }
        double d = 1.0;
        double d2 = 0.0;
        if (!string.equals(SourceCodeGenerator.StrategyXML) && !string.equals(SourceCodeGenerator.PseudoCode)) {
            if (resultsGroup.isStockpickerStrategy()) {
                throw new Exception(String.format("Stockpicker strategies are not supported for platform '%s'.", string));
            }
            try {
                String string4 = resultsGroup.getLastSettings();
                if (string4 != null) {
                    object = XMLUtil.stringToElement((String)string4);
                    Element element2 = object.getChild("Data").getChild("Setups").getChild("Setup");
                    Element element3 = XMLUtil.getChildElem((Element)element2, (String)"Chart");
                    String string5 = element3.getAttributeValue("symbol");
                    InstrumentInfo instrumentInfo = DataManager.getDataInfo((String)"History", (String)string5).symbolInfo;
                    d = instrumentInfo.orderSizeMultiplier;
                    d2 = instrumentInfo.orderSizeStep;
                }
            }
            catch (Exception exception) {
                Log.error("Exc.", (Throwable)exception);
            }
        }
        XMLIndicatorsAnalyzer.init();
        XMLIndicatorsAnalyzer.fixItemAttributes((Element)element);
        CustomDataManager.init((String)SQPaths.customDataDirPath);
        CustomDataManager.addCDataIndySourceCodes((Element)element);
        CustomBlocks.addCBlockSourceCodes(element);
        SourceCodeGenerator sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(string);
        return sourceCodeGenerator.getSource(resultsGroup.getName(), element, d, d2);
    }

    public static boolean isMetaTraderGenerator(String string) {
        return string.equals(SourceCodeGenerator.MetaTrader4) || string.equals(SourceCodeGenerator.MetaTrader5) || string.equals(SourceCodeGenerator.MetaTrader5BR);
    }

    public static void normalizeExportSymbols(Element element) {
        try {
            Element element2 = element.getChild("Strategy").getChild("Datas");
            if (element2 == null) {
                return;
            }
            List list = element2.getChildren("data");
            if (list == null || list.isEmpty()) {
                return;
            }
            for (int i = 0; i < list.size(); ++i) {
                String string;
                Element element3 = (Element)list.get(i);
                Element element4 = element3.getChild("symbol");
                if (element4 == null || (string = element4.getText()) == null || string.equals("NULL") || string.equals("Current")) continue;
                if (i == 0) {
                    element4.setText("NULL");
                    continue;
                }
                try {
                    DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
                    if (dataInfo == null || dataInfo.instrument == null || dataInfo.instrument.isEmpty() || dataInfo.instrument.equals(string)) continue;
                    element4.setText(dataInfo.instrument);
                    continue;
                }
                catch (Exception exception) {
                    Log.info("Cannot resolve instrument name for subchart symbol '{}', keeping as is", (Object)string);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Failed to normalize chart symbols for MT export", (Throwable)exception);
        }
    }
}

