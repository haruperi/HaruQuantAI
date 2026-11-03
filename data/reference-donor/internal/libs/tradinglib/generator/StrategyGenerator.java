/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.customData.CustomDataTypes
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.customData.CustomDataTypes;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.annotations.Value;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.ItemRandomValueRanges;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.GeneratorBase;
import com.strategyquant.tradinglib.generator.RandomAndOrList;
import com.strategyquant.tradinglib.generator.RulePart;
import com.strategyquant.tradinglib.generator.RuleType;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4Fuzzy;
import com.strategyquant.tradinglib.generator.StrategyWithVariables;
import com.strategyquant.tradinglib.gp.strategies.FixNumberOfExitTypes;
import com.strategyquant.tradinglib.gp.strategies.FixStockpickerBlocks;
import com.strategyquant.tradinglib.gp.strategies.FixUnusedDependentFormulas;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixer;
import com.strategyquant.tradinglib.strategy.xml.XmlStrategyException;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyGenerator
extends GeneratorBase {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyGenerator");
    private BlocksConfig blocksConfig;
    private boolean free;
    private String architecture;
    private int fuzzyMinTrue;
    private int fuzzyMaxTrue;
    private ATMGenerateConfig atmGenerateConfig;
    private FixNumberOfExitTypes fixNumberOfExitTypes;

    StrategyGenerator(Element element, Element element2, IRandomGenerator iRandomGenerator, SettingsMap settingsMap, ATMGenerateConfig aTMGenerateConfig) throws JDOMException, IOException, Exception {
        this.elTemplate = element;
        this.rng = iRandomGenerator;
        this.free = true;
        this.addTemplateVariablesToBuildSettings(settingsMap);
        this.blocksConfig = BlocksConfig.getConfig();
        this.replacements = new ReplacementsConfig(element2, this.blocksConfig, this.rng, settingsMap);
        this.atmGenerateConfig = aTMGenerateConfig;
        this.architecture = settingsMap.getString("Architecture");
        this.fuzzyMinTrue = settingsMap.getInt("FuzzyMinTrue", 60);
        this.fuzzyMaxTrue = settingsMap.getInt("FuzzyMaxTrue", 80);
        this.fuzzyMaxTrue = settingsMap.getInt("FuzzyMaxTrue", 80);
        this.fuzzyMaxTrue = settingsMap.getInt("FuzzyMaxTrue", 80);
        this.fuzzyMaxTrue = settingsMap.getInt("FuzzyMaxTrue", 80);
        this.fuzzyMaxTrue = settingsMap.getInt("FuzzyMaxTrue", 80);
        this.fixNumberOfExitTypes = new FixNumberOfExitTypes(settingsMap, element2);
        this.checkConfig();
    }

    private void checkConfig() throws GenerateException {
        Element element = this.elTemplate;
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        StrategyGenerator.checkUniqueRandomIdentifiers(element, hashMap);
        ArrayList<String> arrayList = new ArrayList<String>();
        this.getIdentifiers(element, arrayList, hashMap, true);
        this.replacements.checkAllExist(arrayList);
        ArrayList<String> arrayList2 = new ArrayList<String>();
        this.getIdentifiers(element, arrayList2, hashMap, false);
        for (String string : arrayList2) {
            if (SQUtils.isInStringArray((String)string, arrayList)) continue;
            throw new GenerateException(String.format("Bad configuration - identifier %s referenced in Same/Opposite block or parameter, but it doesn't exist!", string));
        }
    }

    public Element generate(String string) throws GenerateException {
        this.generatedElements = new HashMap();
        Element element = this.elTemplate.clone();
        this.modifyFuzzyPercentage(element);
        StrategyWithVariables strategyWithVariables = new StrategyWithVariables(element);
        this.findAndReplaceAndOrRndBlocks(element);
        this.findAndReplaceRandomBlocks(element, 1);
        this.findAndReplaceRandomParameters(element, 1, 0);
        this.findAndReplaceSameBlocks(element);
        this.findAndReplaceNegatedBlocks(element, strategyWithVariables);
        this.fillGeneratedElements(element);
        this.findAndReplaceSameOrOppositeParameters(element, strategyWithVariables);
        this.deleteMarkedRules(element);
        this.deleteMarkedExits(element);
        this.fixBlocksAndParams(element);
        this.fixFuzzySignalRuleConditions(element);
        FixUnusedDependentFormulas.fix(element);
        StrategyGenerator.fixValuesInCDataIndy(element);
        this.fixIsFormula(element);
        this.addCustomBlocksData(element, strategyWithVariables);
        StrategyFixer.setCurrentVersion(element);
        StrategyFixer.removeAllowRandom(element);
        StrategyFixer.removeRandomGenerateAttributes(element);
        this.generateATM(element);
        FixStockpickerBlocks.fixSPStrategy(element, this.blocksConfig);
        boolean bl = this.fixNumberOfExitTypes.fixStrategy(element);
        if (bl) {
            // empty if block
        }
        return element;
    }

    private void fixIsFormula(Element element) {
        List list;
        if (element.getName().equals("Param") && (list = element.getChild("Formula")) != null) {
            element.setAttribute("isFormula", "true");
        }
        if ((list = element.getChildren()) != null && list.size() > 0) {
            for (int i = 0; i < list.size(); ++i) {
                Element element2 = (Element)list.get(i);
                this.fixIsFormula(element2);
            }
        }
    }

    private void generateATM(Element element) throws GenerateException {
        if (this.atmGenerateConfig == null) {
            return;
        }
        if (!MainApp.v571hfnsHw().aDm88fRJB2()) {
            Log.info("ATM generation functionality is available only in Ultimate license!");
            return;
        }
        Element element2 = this.atmGenerateConfig.generate(this.rng);
        element.addContent((Content)element2);
    }

    public Element mutateATM(Element element, IRandomGenerator iRandomGenerator) throws GenerateException {
        if (this.atmGenerateConfig == null) {
            return null;
        }
        if (!MainApp.v571hfnsHw().aDm88fRJB2()) {
            Log.info("ATM generation functionality is available only in Ultimate license!");
            return null;
        }
        Element element2 = this.atmGenerateConfig.generate(iRandomGenerator);
        this.randomlyReplacePartOfATM(element, element2);
        return element;
    }

    private void randomlyReplacePartOfATM(Element element, Element element2) {
        element.removeChild("ATMs");
        element.addContent((Content)element2);
    }

    private void addCustomBlocksData(Element element, StrategyWithVariables strategyWithVariables) throws GenerateException {
        Element element2 = element.getChild("Strategy");
        Element element3 = element2.getChild("CustomBlocks");
        if (element3 == null) {
            element3 = new Element("CustomBlocks");
            element3.setAttribute("genby", "SG");
            element2.addContent((Content)element3);
        } else {
            element3.setAttribute("genby", "Exist");
        }
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        this.fillCBMap(element2, hashMap);
        StrategyGenerator.addBlocksToXML(element3, hashMap);
    }

    private void fillCBMap(Element element, HashMap<String, Element> hashMap) throws GenerateException {
        Element element2;
        Object object;
        Object object2;
        if (element.getName().equals("Item") && (object2 = element.getAttributeValue("key")) != null && ((String)object2).startsWith("CBlock") && (object = object2) != null) {
            element2 = CustomBlocks.getElement((String)object);
            if (element2 != null) {
                hashMap.put((String)object, element2);
            } else {
                throw new GenerateException("Cannot find definition for Custom Block '" + (String)object + "'");
            }
        }
        if ((object2 = element.getChildren()) != null && object2.size() > 0) {
            for (int i = 0; i < object2.size(); ++i) {
                element2 = (Element)object2.get(i);
                this.fillCBMap(element2, hashMap);
            }
        }
    }

    public static void addBlocksToXML(Element element, HashMap<String, Element> hashMap) {
        if (hashMap == null) {
            return;
        }
        for (Element element2 : hashMap.values()) {
            element.addContent((Content)element2.clone());
        }
    }

    public static void fixValuesInCDataIndy(Element element) throws GenerateException {
        String string;
        Object object;
        if (element.getName().equals("Item") && (object = element.getAttributeValue("key")) != null && ((String)object).startsWith("CDataIndy") && (string = CustomDataManager.getCDataIndyId((String)object)) != null) {
            StrategyGenerator.fixCIndyValues(element, string);
        }
        if ((object = element.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                Element element2 = (Element)object.get(i);
                StrategyGenerator.fixValuesInCDataIndy(element2);
            }
        }
    }

    private static void fixCIndyValues(Element element, String string) throws GenerateException {
        CustomDataInfo customDataInfo = CustomDataManager.getDataInfo((String)string);
        if (customDataInfo == null) {
            Log.info("Cannot find custom data indicator '{}', ignoring!", (Object)string);
            return;
        }
        try {
            element.setAttribute("returnType", CustomDataTypes.translateDataType((byte)((byte)customDataInfo.dataType)));
            if (customDataInfo.dataType == 10) {
                element.setAttribute("categoryType", "simpleRules");
            } else {
                element.setAttribute("categoryType", "indicator");
            }
        }
        catch (Exception exception) {
            throw new GenerateException("Error setting custom indocator return type! DataType=" + customDataInfo.dataType, exception);
        }
        Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#Value#");
        if (element2 == null) {
            return;
        }
        try {
            String string2 = CustomDataManager.createCDataValues((int)customDataInfo.values, (CustomDataInfo)customDataInfo);
            element2.setAttribute("values", string2);
        }
        catch (Exception exception) {
            Log.error("Cannot add values to custom data indy", (Throwable)exception);
            return;
        }
    }

    private void modifyFuzzyPercentage(Element element) {
        if (this.architecture == null || !this.architecture.equals("sq4fuzzy")) {
            return;
        }
        StrategyStandardTemplateSQ4Fuzzy.ramdomizeFuzzyPercentags(element, this.fuzzyMinTrue, this.fuzzyMaxTrue, this.rng);
    }

    private void fixFuzzySignalRuleConditions(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Rules").getChild("Events");
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            List list2 = element3.getChildren();
            for (int j = 0; j < list2.size(); ++j) {
                Element element4 = (Element)list2.get(j);
                if (!element4.getAttributeValue("type").equals("SignalFuzzy")) continue;
                this.fixFuzzySignals(element4);
            }
        }
    }

    private void fixFuzzySignals(Element element) {
        int n;
        Element element2 = element.getChild("signals");
        List list = element2.getChildren("signal");
        ArrayList<Element> arrayList = new ArrayList<Element>();
        for (n = 0; n < list.size(); ++n) {
            Element element3 = (Element)list.get(n);
            arrayList.add(this.fixFuzzySignal(element3));
        }
        element2.removeChildren("signal");
        for (n = 0; n < arrayList.size(); ++n) {
            element2.addContent((Content)arrayList.get(n));
        }
    }

    private Element fixFuzzySignal(Element element) {
        Element element2 = new Element("signal");
        element2.setAttribute("variable", element.getAttributeValue("variable"));
        element2.setAttribute("minTrue", element.getAttributeValue("minTrue"));
        ArrayList<Element> arrayList = new ArrayList<Element>();
        this.getSignalRealConditionsList(element, arrayList);
        for (int i = 0; i < arrayList.size(); ++i) {
            element2.addContent((Content)((Element)arrayList.get(i)).detach());
        }
        return element2;
    }

    private void getSignalRealConditionsList(Element element, List<Element> list) {
        List list2 = element.getChildren();
        for (int i = 0; i < list2.size(); ++i) {
            Element element2 = (Element)list2.get(i);
            if (this.isRealCondition(element2)) {
                list.add(element2);
                continue;
            }
            List list3 = element2.getChildren();
            if (list3 == null) continue;
            this.getSignalRealConditionsList(element2, list);
        }
    }

    private boolean isRealCondition(Element element) {
        if (!element.getName().equals("Item")) {
            return false;
        }
        String string = element.getAttributeValue("key");
        return !string.equals("AND") && !string.equals("OR");
    }

    private void deleteMarkedRules(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Rules").getChild("Events");
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            List list2 = element3.getChildren();
            Iterator iterator = list2.iterator();
            while (iterator.hasNext()) {
                Element element4 = (Element)iterator.next();
                if (element4.getAttributeValue("type").contains("Signal")) {
                    this.replaceDeleteWithFalse(element4);
                    continue;
                }
                if (!this.shouldDeleteThisRule(element4, false)) continue;
                iterator.remove();
            }
        }
    }

    private void deleteMarkedExits(Element element) {
        Element element2 = element.getChild("Strategy");
        String string = element2.getAttributeValue("engine");
        if (string != null && !string.equals("Stockpicker") && !string.equals("Single-asset cloud strategy")) {
            return;
        }
        Element element3 = element.getChild("Strategy").getChild("Rules").getChild("Events");
        List list = element3.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            this.deleteMarkedExitElements(element4);
        }
    }

    private void deleteMarkedExitElements(Element element) {
        List list = element.getChildren();
        Iterator iterator = list.iterator();
        while (iterator.hasNext()) {
            Element element2 = (Element)iterator.next();
            if (element2.getName().equals("Exit")) {
                if (!this.shouldDeleteThisRule(element2, true)) continue;
                iterator.remove();
                continue;
            }
            this.deleteMarkedExitElements(element2);
        }
    }

    private void replaceDeleteWithFalse(Element element) {
        List list = element.getChildren();
        if (list == null) {
            return;
        }
        for (Element element2 : list) {
            if (element2.getName().equals("DeleteRule")) {
                element2.setName("Item");
                element2.setAttribute("key", "Boolean");
                element2.setAttribute("name", "(BOOL) Boolean");
                element2.setAttribute("display", "#Value#");
                element2.setAttribute("returnType", "number");
                element2.setAttribute("categoryType", "other");
                element2.setAttribute("notFirstValue", "true");
                Element element3 = new Element("Param");
                element2.addContent((Content)element3);
                element3.setAttribute("key", "#Value#");
                element3.setAttribute("name", "Value");
                element3.setAttribute("type", "boolean");
                element3.setAttribute("defaultValue", "false");
                element3.setAttribute("controlType", "booleanVar");
                element3.setText("false");
                return;
            }
            this.replaceDeleteWithFalse(element2);
        }
    }

    private boolean shouldDeleteThisRule(Element element, boolean bl) {
        List list = element.getChildren();
        if (list == null) {
            return false;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("DeleteRule")) {
                if (!bl) {
                    return !element.getName().equals("Exit");
                }
                return true;
            }
            if (!this.shouldDeleteThisRule(element2, bl)) continue;
            return true;
        }
        return false;
    }

    void findAndReplaceAndOrRndBlocks(Element element) throws GenerateException {
        RandomAndOrList randomAndOrList = new RandomAndOrList();
        this.findAndOrBlocks(element, randomAndOrList);
        randomAndOrList.fixValues();
        randomAndOrList.replaceValues(1, this.rng, "random");
        randomAndOrList.replaceValues(2, this.rng, "copied");
    }

    void findAndReplaceRandomBlocks(Element element, int n) throws GenerateException {
        int n2 = 0;
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Item") && ((String)(object = element2.getAttributeValue("key"))).startsWith("Random")) {
                String string = this.getRandomBlockId(element2);
                ReplacementConfig replacementConfig = this.replacements.get(string);
                if (!replacementConfig.shouldGenerate(this.rng)) {
                    if (replacementConfig.deleteRule) {
                        Element element3 = new Element("DeleteRule");
                        element.setContent(n2, (Content)element3);
                        this.generatedElements.put(string, element3);
                        continue;
                    }
                    element.removeContent(n2);
                    continue;
                }
                int n3 = RuleType.recognizeRuleTypeFromParents(element2);
                Element element4 = replacementConfig.generateRandomBlock(this.rng, n, n3, null);
                this.handleActionParameters(element4, element2, "random", string);
                element4.setAttribute("generated", "random");
                element4.setAttribute("randomId", string);
                if (replacementConfig.replacementSuperType == 1 || replacementConfig.replacementSuperType == 2) {
                    this.applyAttributes(element4, element2);
                    Element element5 = this.getRandomIdParam(element2);
                    if (element5 != null) {
                        element2.removeContent((Content)element5);
                    }
                    List list2 = element4.getChildren();
                    int n4 = list2.size();
                    for (int j = 0; j < n4; ++j) {
                        element2.addContent((Content)((Element)list2.get(0)).detach());
                    }
                    this.generatedElements.put(string, element2);
                } else {
                    element.setContent(n2, (Content)element4);
                    this.generatedElements.put(string, element4);
                }
            }
            if ((object = element2.getChildren()) != null) {
                this.findAndReplaceRandomBlocks(element2, this.recognizeRulePart(n, element2.getName()));
            }
            ++n2;
        }
    }

    private int recognizeRulePart(int n, String string) {
        if (n != 1) {
            return n;
        }
        if (RulePart.isConditionElement(string)) {
            return 2;
        }
        if (RulePart.isActionElement(string)) {
            return 3;
        }
        return n;
    }

    void findAndReplaceRandomParameters(Element element, int n, int n2) throws GenerateException {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Item")) {
                Object object2;
                object = element2.getAttributeValue("returnType");
                if (object == null || !((String)object).equals("order") || (object2 = element2.getAttributeValue("generated")) != null) {
                    // empty if block
                }
                object2 = ItemRandomValueRanges.getRandomValueRanges(element2);
                Element element3 = null;
                List list2 = element2.getChildren("Param");
                for (int j = 0; j < list2.size(); ++j) {
                    ReplacementConfig replacementConfig;
                    Element element4 = (Element)list2.get(j);
                    String string = element4.getAttributeValue("generate");
                    if (string == null || !string.equals("random")) continue;
                    String string2 = StrategyGenerator.findIdentifierInParams(element2, false);
                    if (string2 == null) {
                        string2 = element2.getAttributeValue("randomId");
                    }
                    if (string2 == null) {
                        this.randomGenerateParameter(element2, element4, (ItemRandomValueRanges)object2);
                        continue;
                    }
                    if (element3 == null) {
                        replacementConfig = this.replacements.get(string2);
                        element3 = replacementConfig.generateRandomBlock(this.rng, n, n2, (ItemRandomValueRanges)object2);
                    }
                    if ((replacementConfig = this.getParamElement(element4.getAttributeValue("key"), element3)) != null) {
                        this.replaceParameter(element2, (Element)replacementConfig, "random", string2);
                    }
                    this.generatedElements.put(string2, element2);
                }
            }
            if ((object = element2.getChildren()) == null) continue;
            this.findAndReplaceRandomParameters(element2, this.recognizeRulePart(n, element2.getName()), n2);
        }
    }

    private void randomGenerateParameter(Element element, Element element2, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        ReplacementParameter replacementParameter;
        Object object;
        boolean bl;
        String string = element2.getAttributeValue("key");
        String string2 = element2.getAttributeValue("type");
        String string3 = itemRandomValueRanges == null ? null : itemRandomValueRanges.getForParam(string);
        boolean bl2 = bl = string2.equals("double");
        if (string3 != null) {
            object = RandomValueConfig.parseRandomValue(string3, bl);
            if (object == null) {
                Log.error("Error parsing randomValue '" + string3 + "' in strategy template.");
                return;
            }
            if (((RandomValueConfig)object).isValid()) {
                String string4;
                double d = ((RandomValueConfig)object).generateRandomValue(this.rng, bl);
                if (bl) {
                    int n = ((RandomValueConfig)object).getDecimals(2);
                    string4 = SQUtils.d2String((double)d, (int)n);
                } else {
                    string4 = Integer.toString((int)d);
                }
                element2.setText(string4);
                return;
            }
        }
        if ((replacementParameter = this.replacements.findReplacementParamByKey((String)(object = element.getAttributeValue("key")), string)) != null) {
            String string5;
            if (bl) {
                string5 = replacementParameter.getDoubleParam(this.rng, -1.0, -1.0, null);
            } else {
                int n = replacementParameter.getIntParam(this.rng, null, null);
                string5 = Integer.toString(n);
            }
            element2.setText(string5);
            return;
        }
        BlockDefinition blockDefinition = this.blocksConfig.getBlock((String)object);
        if (blockDefinition != null) {
            BlockParameter blockParameter = blockDefinition.getParamByKey(string);
            if (blockParameter == null) {
                throw new GenerateException("Unknown parameter " + string + " in block " + (String)object + "");
            }
            String string6 = bl ? this.generateRandomDoubleParam(blockParameter) : this.generateRandomIntParam(blockParameter);
            element2.setText(string6);
        }
    }

    private String generateRandomIntParam(BlockParameter blockParameter) {
        int n = 10;
        if (blockParameter.controlType.equals("combo")) {
            String string = blockParameter.values;
            String[] stringArray = string.split(",");
            int n2 = this.rng.nextInt(stringArray.length);
            String string2 = stringArray[n2];
            String[] stringArray2 = string2.split("=");
            return stringArray2[1];
        }
        if (blockParameter.key.equals("#TimeFrom#") || blockParameter.key.equals("#TimeTo#")) {
            int n3 = Value.generateHH(this.rng, blockParameter);
            int n4 = Value.generateMM(this.rng, blockParameter);
            n = n3 * 100 + n4;
        } else if (Value.isPredefined(blockParameter.minValue) || Value.isPredefined(blockParameter.maxValue)) {
            n = blockParameter.iDefaultValue;
        } else {
            int n5;
            int n6 = (int)blockParameter.minValue;
            int n7 = (int)blockParameter.maxValue;
            int n8 = (int)blockParameter.step;
            if (n7 < n6) {
                n5 = n6;
                n6 = n7;
                n7 = n5;
            }
            if (n7 == n6) {
                n = n7;
            } else {
                n5 = (n7 - n6) / n8 + 1;
                if (n5 <= 0) {
                    // empty if block
                }
                int n9 = this.rng.nextInt(n5);
                n = n6 + n9 * n8;
            }
        }
        return Integer.toString(n);
    }

    private String generateRandomDoubleParam(BlockParameter blockParameter) {
        if (blockParameter.controlType.equals("combo")) {
            String string = blockParameter.values;
            String[] stringArray = string.split(",");
            int n = this.rng.nextInt(stringArray.length);
            String string2 = stringArray[n];
            String[] stringArray2 = string2.split("=");
            return stringArray2[1];
        }
        int n = blockParameter.decimals;
        if (blockParameter.controlType.equals("jspinnerVar") || blockParameter.controlType.equals("jspinner")) {
            if (Value.isPredefined(blockParameter.minValue) || Value.isPredefined(blockParameter.maxValue)) {
                double d = blockParameter.dDefaultValue;
            } else {
                double d;
                double d2 = blockParameter.minValue;
                double d3 = blockParameter.maxValue;
                double d4 = blockParameter.step;
                if (d2 == d3) {
                    d = d3;
                } else {
                    int n2 = (int)((d3 - d2) / d4) + 1;
                    if (n2 < 0) {
                        d2 = d2 < 0.0 ? -10000.0 : 0.0;
                        d3 = d3 > 0.0 ? 10000.0 : 0.0;
                        if (d4 < 1.0) {
                            d4 = 1.0;
                        }
                        n2 = (int)((d3 - d2) / d4) + 1;
                    }
                    int n3 = this.rng.nextInt(n2);
                    d = d2 + (double)n3 * d4;
                }
                return SQUtils.d2String((double)d, (int)n);
            }
        }
        return "10";
    }

    void fillGeneratedElements(Element element) throws GenerateException {
        List list = element.getChildren();
        if (list == null) {
            return;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Item")) {
                String string = StrategyGenerator.findIdentifierInParams(element2, false);
                if (string == null) continue;
                if (!this.generatedElements.containsKey(string)) {
                    this.generatedElements.put(string, element2);
                }
            }
            this.fillGeneratedElements(element2);
        }
    }

    void findAndReplaceSameOrOppositeParameters(Element element, StrategyWithVariables strategyWithVariables) throws GenerateException {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Item")) {
                Object object2;
                object = element2.getAttributeValue("returnType");
                if (object == null || !((String)object).equals("order") || (object2 = element2.getAttributeValue("generated")) != null) {
                    // empty if block
                }
                object2 = element2.getChildren("Param");
                for (int j = 0; j < object2.size(); ++j) {
                    Object object3;
                    Object object4;
                    String string;
                    Object object5;
                    Element element3;
                    String string2;
                    Element element4 = (Element)object2.get(j);
                    String string3 = element4.getAttributeValue("generate");
                    if (string3 == null) continue;
                    if (string3.equals("same")) {
                        string2 = element4.getAttributeValue("identification");
                        if (string2 == null) {
                            throw new GenerateException("Cannot find Replacement ID for Same parameter!");
                        }
                        element3 = (Element)this.generatedElements.get(string2);
                        if (element3 == null) {
                            throw new GenerateException(String.format("Block with Identification '%s' not found for parameter copy!", string2));
                        }
                        object5 = this.getParamElement(element4.getAttributeValue("key"), element3);
                        if (object5 == null) continue;
                        this.replaceParameter(element2, object5.clone(), "same", string2);
                        continue;
                    }
                    if (!string3.equals("opposite")) continue;
                    string2 = element4.getAttributeValue("identification");
                    if (string2 == null) {
                        throw new GenerateException("Cannot find Replacement ID for Opposite parameter!");
                    }
                    element3 = (Element)this.generatedElements.get("_Negated_" + string2);
                    if (element3 == null) {
                        object5 = (Element)this.generatedElements.get(string2);
                        if (object5 == null) {
                            throw new GenerateException(String.format("Block with Identification '%s' not found for parameter negation!", string2));
                        }
                        object5 = object5.clone();
                        string = object5.getAttributeValue("key");
                        try {
                            object4 = Blocks.getBlockObject(string, strategyWithVariables, (Element)object5);
                        }
                        catch (BlockDefinitionException blockDefinitionException) {
                            throw new GenerateException("Cannot create block '" + string + "'from given config", blockDefinitionException);
                        }
                        catch (Exception exception) {
                            throw new GenerateException("Cannot create block '" + string + "' from given config. Exception: " + exception.getClass().getSimpleName() + " : " + exception.getMessage(), exception);
                        }
                        try {
                            object3 = this.replacements.negateBlock((IBlock)object4, strategyWithVariables);
                            element3 = Blocks.generateBlockTreeXml((IBlock)object3);
                            this.generatedElements.put("_Negated_" + string2, element3);
                        }
                        catch (BlockDefinitionException | XmlStrategyException exception) {
                            throw new GenerateException(exception);
                        }
                    }
                    if ((object4 = this.getParamElement((String)(object5 = element4.getAttributeValue("key")), element3)) != null) {
                        this.replaceParameter(element2, object4.clone(), "negated", string2);
                        continue;
                    }
                    if (!((String)object5).equals("#Price#")) continue;
                    string = element2.getAttributeValue("key");
                    object3 = element3.getAttributeValue("key");
                    String string4 = element2.getAttributeValue("generated");
                    if (string.equals(object3) || string4 == null || !string4.equals("random")) continue;
                    this.copyAttributes(element3, element2);
                }
            }
            if ((object = element2.getChildren()) == null) continue;
            this.findAndReplaceSameOrOppositeParameters(element2, strategyWithVariables);
        }
    }

    private Element getParamElement(String string, Element element) {
        String string2 = element.getAttributeValue("key");
        if (string2.equals("AND") || string2.equals("OR")) {
            return this.getParamElementAndOr(string, element);
        }
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            if (!element2.getAttributeValue("key").equals(string)) continue;
            return element2;
        }
        return null;
    }

    private Element getParamElementAndOr(String string, Element element) {
        List list = element.getChildren("Item");
        if (list.size() == 0) {
            return null;
        }
        if (list.size() == 1) {
            return this.getParamElement(string, (Element)list.get(0));
        }
        int n = this.rng.nextInt(list.size());
        return this.getParamElement(string, (Element)list.get(n));
    }

    private void handleActionParameters(Element element, Element element2, String string, String string2) throws GenerateException {
        String string3 = element2.getAttributeValue("superType");
        if (string3 == null || !string3.equals("action")) {
            return;
        }
        for (Element element3 : element2.getChildren("Param")) {
            if (element3.getAttributeValue("key").equals("#Identification#")) continue;
            String string4 = element3.getText();
            List list = element3.getChildren();
            String string5 = element3.getAttributeValue("generate");
            String string6 = element3.getAttributeValue("identification");
            if (string5 == null) {
                if (string4.equals("") && list.size() <= 0) continue;
                this.replaceParameter(element, element3, "fixed", null);
                continue;
            }
            if (!string.equals("random") || !string5.equals("opposite") && !string5.equals("same")) continue;
            this.replaceParameterToGenerate(element, element3, string5, string6);
        }
    }

    private void replaceParameter(Element element, Element element2, String string, String string2) throws GenerateException {
        String string3 = element2.getAttributeValue("key");
        Element element3 = null;
        for (Element element4 : element.getChildren("Param")) {
            if (!element4.getAttributeValue("key").equals(string3)) continue;
            element3 = element4;
            break;
        }
        if (element3 == null) {
            return;
        }
        for (Element element4 : element2.getAttributes()) {
            element3.setAttribute(element4.getName(), element4.getValue());
        }
        element3.setAttribute("generated", string);
        if (string2 != null) {
            element3.setAttribute("randomId", string2);
        }
        element3.removeAttribute("generate");
        element3.removeAttribute("identification");
        element3.removeContent();
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            element3.addContent((Content)((Element)list.get(i)).clone());
        }
        String string4 = element2.getText().trim();
        if (string4 != null && !string4.equals("")) {
            element3.setText(string4);
        }
    }

    private void copyAttributes(Element element, Element element2) {
        List list = element.getAttributes();
        for (int i = 0; i < list.size(); ++i) {
            Attribute attribute = (Attribute)list.get(i);
            element2.setAttribute(attribute.getName(), attribute.getValue());
        }
        element2.setAttribute("generated", "same");
    }

    private void replaceParameterToGenerate(Element element, Element element2, String string, String string2) throws GenerateException {
        String string3 = element2.getAttributeValue("key");
        Element element3 = null;
        for (Element element4 : element.getChildren("Param")) {
            if (!element4.getAttributeValue("key").equals(string3)) continue;
            element3 = element4;
            break;
        }
        if (element3 == null) {
            return;
        }
        for (Element element4 : element2.getAttributes()) {
            element3.setAttribute(element4.getName(), element4.getValue());
        }
        element3.removeContent();
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            element3.addContent((Content)((Element)list.get(i)).clone());
        }
        String string4 = element2.getText().trim();
        if (string4 != null && !string4.equals("")) {
            element3.setText(string4);
        }
    }

    private void replaceParameterValue(Element element, String string, String string2) {
        for (Element element2 : element.getChildren("Param")) {
            if (!element2.getAttributeValue("key").equals(string)) continue;
            element2.setText(string2);
            break;
        }
    }

    private void findAndReplaceSameBlocks(Element element) throws GenerateException {
        int n = 0;
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Item") && ((String)(object = element2.getAttributeValue("key"))).startsWith("Same")) {
                String string = this.getRandomBlockId(element2);
                Element element3 = (Element)this.generatedElements.get(string);
                if (element3 == null) {
                    throw new GenerateException(String.format("Block with Identification '%s' not found for copy!", string));
                }
                if (element3.getName().equals("DeleteRule")) {
                    Element element4 = new Element("DeleteRule");
                    element.setContent(n, (Content)element4);
                    continue;
                }
                element3 = element3.clone();
                element3.setAttribute("generated", "same");
                this.handleActionParameters(element3, element2, "same", string);
                element.setContent(n, (Content)element3);
            }
            if ((object = element2.getChildren()) != null) {
                this.findAndReplaceSameBlocks(element2);
            }
            ++n;
        }
    }

    private void findAndReplaceNegatedBlocks(Element element, StrategyBase strategyBase) throws GenerateException {
        int n = 0;
        for (Element element2 : element.getChildren()) {
            Object object;
            if (element2.getName().equals("Item") && (((String)(object = element2.getAttributeValue("key"))).startsWith("Negate") || ((String)object).startsWith("Opposite"))) {
                IBlock iBlock;
                Element element3;
                String string = this.getRandomBlockId(element2);
                Element element4 = (Element)this.generatedElements.get(string);
                if (element4 == null) {
                    if (Log.isDebugEnabled()) {
                        Log.debug("Element '{}' not found for negation!", (Object)string);
                    }
                    element.removeContent(n);
                    continue;
                }
                if (element4.getName().equals("DeleteRule")) {
                    element3 = new Element("DeleteRule");
                    element.setContent(n, (Content)element3);
                    continue;
                }
                element3 = element4.clone();
                String string2 = element3.getAttributeValue("key");
                try {
                    iBlock = Blocks.getBlockObject(string2, strategyBase, element3);
                }
                catch (BlockDefinitionException blockDefinitionException) {
                    throw new GenerateException("Cannot create block '" + string2 + "' from given config. Exception", blockDefinitionException);
                }
                catch (Exception exception) {
                    throw new GenerateException("Cannot create block '" + string2 + "' from given config. Exception: " + exception.getClass().getSimpleName() + " : " + exception.getMessage(), exception);
                }
                try {
                    IBlock iBlock2 = this.replacements.negateBlock(iBlock, strategyBase);
                    Element element5 = Blocks.generateBlockTreeXml(iBlock2);
                    this.generatedElements.put("_Negated_" + string, element5);
                    this.handleOppositeActionParameters(element5, element4, element2);
                    element5.setAttribute("generated", "negated");
                    element5.setAttribute("randomId", string);
                    if (element3.getAttributeValue("returnType") != null) {
                        element5.setAttribute("returnType", element3.getAttributeValue("returnType"));
                    }
                    this.handleActionParameters(element5, element2, "negated", string);
                    element.setContent(n, (Content)element5);
                }
                catch (BlockDefinitionException | XmlStrategyException exception) {
                    throw new GenerateException(exception);
                }
            }
            if ((object = element2.getChildren()) != null) {
                this.findAndReplaceNegatedBlocks(element2, strategyBase);
            }
            ++n;
        }
    }

    private void handleOppositeActionParameters(Element element, Element element2, Element element3) {
        block4: {
            block5: {
                String string = this.getRandomBlockParamValue(element3, "#UseOwnMagicNumber#");
                if (string == null) {
                    return;
                }
                boolean bl = Boolean.parseBoolean(string);
                if (!bl) break block5;
                String string2 = this.getRandomBlockParamValue(element3, "#MagicNumber#");
                if (string2 == null) break block4;
                for (Element element4 : element.getChildren("Param")) {
                    if (!element4.getAttributeValue("key").equals("#MagicNumber#")) continue;
                    element4.setText(string2);
                    element4.setAttribute("variable", "true");
                    element4.setAttribute("variableType", "INT");
                    break block4;
                }
                break block4;
            }
            String string = this.getRandomBlockParamValue(element2, "#MagicNumber#");
            if (string != null) {
                for (Element element5 : element.getChildren("Param")) {
                    if (!element5.getAttributeValue("key").equals("#MagicNumber#")) continue;
                    element5.setText(string);
                    element5.setAttribute("variable", "true");
                    element5.setAttribute("variableType", "INT");
                    break;
                }
            }
        }
    }

    private void applyAttributes(Element element, Element element2) {
        for (Attribute attribute : element.getAttributes()) {
            element2.setAttribute(attribute.getName(), attribute.getValue());
        }
    }

    private Element getRandomIdParam(Element element) {
        for (Element element2 : element.getChildren()) {
            String string = element2.getAttributeValue("controlType");
            if (string == null || !string.equals("randomId")) continue;
            return element2;
        }
        return null;
    }

    private void saveToFile(Element element, String string) {
        try {
            XMLUtil.xmlToFile((Element)element, (File)new File(MainApp.getDataPath() + "tests/tmp/" + string + ".xml"));
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    /*
     * Unable to fully structure code
     */
    private void fixBlocksAndParams(Element var1_1) throws GenerateException {
        var2_2 = var1_1.getChildren();
        for (var3_3 = 0; var3_3 < var2_2.size(); ++var3_3) {
            var4_4 = (Element)var2_2.get(var3_3);
            var5_5 = var4_4.getAttributeValue("key");
            if (var4_4.getName().equals("Item")) {
                var6_6 = this.blocksConfig.getBlock(var5_5);
                if (var6_6 != null) {
                    try {
                        this.fixCategoryReturnType(var4_4, (BlockDefinition)var6_6);
                        var7_7 = var4_4.getAttributeValue("returnType");
                        if (var7_7 == null || !var7_7.equals("order")) ** GOTO lbl20
                        this.fixActionBlock(var4_4, (BlockDefinition)var6_6);
                    }
                    catch (Exception var7_8) {
                        throw new GenerateException(var7_8.getMessage(), var7_8);
                    }
                }
            } else if (var4_4.getName().equals("Param") && (var6_6 = var4_4.getText()) != null && var6_6.endsWith(".00")) {
                var4_4.setText(var6_6.replace(".00", ""));
            }
lbl20:
            // 6 sources

            if ((var6_6 = var4_4.getChildren()) == null) continue;
            this.fixBlocksAndParams(var4_4);
        }
    }

    private void fixCategoryReturnType(Element element, BlockDefinition blockDefinition) throws BlockDefinitionException {
        if (blockDefinition.categoryType != null) {
            element.setAttribute("categoryType", blockDefinition.categoryType);
        }
        element.setAttribute("returnType", ReturnTypes.translateReturnType(blockDefinition.returnType));
        element.removeAttribute("help");
    }

    private void fixActionBlock(Element element, BlockDefinition blockDefinition) throws Exception {
        ArrayList<Object> arrayList = new ArrayList<Object>();
        for (Object object : blockDefinition.parameters) {
            Element element2 = XMLUtil.getItemParameter((Element)element, (String)((BlockParameter)object).key, (boolean)false);
            if (element2 == null) continue;
            arrayList.add(element2);
        }
        ObjectListIterator objectListIterator = XMLUtil.getItemParameter((Element)element, (String)"#Identification#", (boolean)false);
        if (objectListIterator != null) {
            arrayList.add(objectListIterator);
        }
        element.removeChildren("Param");
        for (Element element2 : arrayList) {
            element.addContent((Content)element2);
        }
    }

    public Element generateMutatedRandomBlock(String string, Element element, int n, int n2) throws GenerateException {
        ReplacementConfig replacementConfig = this.replacements.get(string);
        return replacementConfig.generateMutatedRandomBlock(this.rng, element, n, n2);
    }

    public void freeGenerator() {
        this.free = true;
    }

    boolean isFree() {
        return this.free;
    }

    void setUsed() {
        this.free = false;
    }

    public void setRandomGenerator(IRandomGenerator iRandomGenerator) {
        this.rng = iRandomGenerator;
    }

    public Element verifyParameters(String string, Element element, Element element2) throws Exception {
        Element element3;
        if (element == null) {
            return element;
        }
        if (string == null) {
            string = this.recognizeRandomBlock(element, element2);
        }
        if (string == null) {
            return element;
        }
        ReplacementConfig replacementConfig = this.replacements.get(string);
        if (replacementConfig == null) {
            throw new Exception("Replacement config with ID '" + string + "' not found!");
        }
        String string2 = element.getName();
        if (string2.equals("Param")) {
            element3 = element.getParentElement();
            if (element3 == null && element2 != null) {
                element3 = this.cloneParentReplaceParamValue(element2, element);
            }
        } else {
            element3 = element;
        }
        if (element3 == null) {
            throw new Exception("No parent found!");
        }
        String string3 = element3.getAttributeValue("key");
        if (replacementConfig.verifyItem(string3, element3)) {
            Log.info("Passed {}", this.printParams(element3));
            return element;
        }
        Log.info("Key '" + string3 + "' verified FALSE");
        return null;
    }

    private Object printParams(Element element) {
        String string = element.getAttributeValue("key");
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            string = string + " " + element2.getText();
        }
        return string;
    }

    private Element cloneParentReplaceParamValue(Element element, Element element2) {
        element = element.clone();
        String string = element2.getAttributeValue("key");
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            String string2 = element3.getAttributeValue("key");
            if (!string.equals(string2)) continue;
            element3.setText(element2.getText());
            return element;
        }
        return element;
    }

    private String recognizeRandomBlock(Element element, Element element2) {
        String string = element.getAttributeValue("randomId");
        if (string != null) {
            return string;
        }
        if (element2 != null) {
            string = element2.getAttributeValue("randomId");
            if (string != null) {
                return string;
            }
            string = this.findRandomIdInSiblings(element2);
            if (string != null) {
                return string;
            }
        }
        if ((element = element.getParentElement()) != null) {
            string = element.getAttributeValue("randomId");
            if (string != null) {
                return string;
            }
            string = this.findRandomIdInSiblings(element);
            if (string != null) {
                return string;
            }
        }
        return null;
    }

    private String findRandomIdInSiblings(Element element) {
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("controlType");
            if (string == null || !string.equals("randomId")) continue;
            return element2.getText();
        }
        return null;
    }
}

