/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.GeneratorBase;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.util.StockpickerGenFixer;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlockSettingsConverter {
    private static final Logger Log = LoggerFactory.getLogger(BlockSettingsConverter.class);
    private static final String NAME_PRICES = "Prices";
    private static final String NAME_PRICES_DOT = "Prices.";
    private static final String NAME_RANDOM_INDICATOR_SIGNALS = "Indicators";
    private static final String NAME_RANDOM_INDICATOR_SIGNALS_DOT = "Indicators.";
    private final int engine;
    private Element elCharts;
    private Element elOrderTypes;
    private Element elExitTypes;
    private Element wizardConfig;
    private Int2ObjectOpenHashMap<Element> mapAllBlocksInConfig;
    private HashMap<String, ArrayList<Element>> mapRandomGroupBlocks;
    private String andWeight;
    private String orWeight;
    private String exitRuleProbability;
    private String marketSides;
    private boolean entrySymmetry;
    private boolean exitSymmetry;
    private boolean containsExitRule;
    private boolean longEntryImprovement = false;
    private boolean shortEntryImprovement = false;
    private boolean longExitImprovement = false;
    private boolean shortExitImprovement = false;
    private boolean longActionImprovement = false;
    private boolean shortActionImprovement = false;
    private Element strategyTemplate;
    private String strategyType;
    private List<Element> arrayBuildingBlocks;
    private List<Element> arrayBuildingBlocksArtifical;

    public BlockSettingsConverter(Element element, Element element2) throws GenerateException {
        Element element3 = element.getChild("Blocks");
        this.strategyTemplate = element2;
        Element element4 = element.getChild("WhatToBuild");
        if (element4 == null) {
            throw new GenerateException("Builder project config doesn't contain <WhatToBuild>");
        }
        this.engine = StrategyTemplateGenerator.getEngine(element);
        this.strategyType = element4.getChild("StrategyType").getAttributeValue("type");
        Element element5 = element4.getChild("MarketSides");
        this.marketSides = element5.getAttributeValue("type");
        this.entrySymmetry = false;
        this.exitSymmetry = false;
        if (this.marketSides.equals("both")) {
            this.entrySymmetry = Boolean.parseBoolean(element5.getChildText("EntrySymmetry"));
            this.exitSymmetry = Boolean.parseBoolean(element5.getChildText("ExitSymmetry"));
        }
        this.elCharts = this.convertToCharts(element4.getChild("RulesComplexity"));
        this.initBuildingBlocks(element3.getChild("BuildingBlocks"));
        this.initCustomDataIndy(element3.getChild("CustomData"));
        this.elOrderTypes = element3.getChild("OrderTypes");
        this.elExitTypes = element3.getChild("ExitTypes");
        this.containsExitRule = this.checkContainsExitRule(element3);
        if ((this.andWeight == null || this.andWeight.equals("0")) && (this.orWeight == null || this.orWeight.equals("0"))) {
            this.andWeight = "1";
            this.orWeight = "0";
        }
        if (this.strategyType.equals("improve")) {
            this.loadPartsToImprove(element);
        }
        this.loadRandomGroups(element2);
        this.getWizardConfig();
        this.applyGlobalSLPTSettings(element, element3);
    }

    private void loadRandomGroups(Element element) {
        int n;
        Element element2 = element.getChild("Strategy").getChild("RandomGroups");
        if (element2 == null) {
            return;
        }
        if (this.mapRandomGroupBlocks == null) {
            this.mapRandomGroupBlocks = new HashMap();
        }
        List list = element2.getChildren();
        for (n = 0; n < list.size(); ++n) {
            Element element3 = (Element)list.get(n);
            List list2 = element3.getChildren();
            ArrayList<Element> arrayList = new ArrayList<Element>(list2.size());
            for (int i = 0; i < list2.size(); ++i) {
                Element element4 = (Element)list2.get(i);
                Element element5 = this.convertRandomGroupItemToBlock(element4);
                if (element5 == null) continue;
                arrayList.add(element5);
            }
            String string = element3.getAttributeValue("id");
            if (string == null || string.equals("")) {
                Log.error("Some random group doesn't have ID!");
                continue;
            }
            this.mapRandomGroupBlocks.put(string, arrayList);
        }
        for (n = 0; n < 50 && this.convertRandomBlocksInGroup(); ++n) {
        }
    }

    private boolean convertRandomBlocksInGroup() {
        boolean bl = false;
        for (ArrayList<Element> arrayList : this.mapRandomGroupBlocks.values()) {
            ArrayList<Element> arrayList2 = null;
            Iterator<Element> iterator = arrayList.iterator();
            while (iterator.hasNext()) {
                Element element = iterator.next();
                try {
                    ArrayList<Element> arrayList3;
                    Element element2 = element.getChild("Generated");
                    String string = this.getRandomGroupId(element2);
                    if (string == null || (arrayList3 = this.mapRandomGroupBlocks.get(string)) == null) continue;
                    iterator.remove();
                    bl = true;
                    if (arrayList2 == null) {
                        arrayList2 = new ArrayList<Element>();
                    }
                    arrayList2.addAll(arrayList3);
                }
                catch (GenerateException generateException) {}
            }
            if (arrayList2 == null) continue;
            arrayList.addAll(arrayList2);
        }
        return bl;
    }

    private Element convertRandomGroupItemToBlock(Element element) {
        List list;
        Element element2;
        Element element3 = new Element("Block");
        String string = element.getAttributeValue("key");
        if (string == null) {
            return null;
        }
        element3.setAttribute("key", string);
        element3.setAttribute("use", "true");
        element3.setAttribute("weight", "1");
        Element element4 = new Element("Generated");
        element4.setAttribute("weight", "1");
        element3.addContent((Content)element4);
        Element element5 = CustomBlocks.getElement(string);
        Element element6 = element;
        List list2 = element6.getChildren("Param");
        if (list2.size() > 0) {
            for (int i = 0; i < list2.size(); ++i) {
                Element element7 = (Element)list2.get(i);
                element2 = this.convertRandomGroupItemParamToBlock(element7, element5);
                element4.addContent((Content)element2);
            }
        }
        if ((list = element6.getChildren("Block")).size() > 0) {
            list2 = element.getChildren("Block");
            element3.setAttribute("keepParams", "true");
            for (int i = 0; i < list2.size(); ++i) {
                element2 = (Element)list2.get(i);
                Element element8 = this.convertRandomGroupItemParamToBlock(element2, element5);
                element8.setAttribute("keepParams", "true");
                element4.addContent((Content)element8);
            }
        }
        Element element9 = new Element("Predefined");
        element3.addContent((Content)element9);
        return element3;
    }

    private Element convertRandomGroupItemParamToBlock(Element element, Element element2) {
        Element element3;
        block14: {
            element3 = element.clone();
            String string = element3.getAttributeValue("key");
            if (string.equals("#Chart#")) {
                element3.setAttribute("generation", "random");
                element3.setAttribute("allCharts", "true");
            } else {
                String string2 = element.getAttributeValue("generate");
                if (string2 == null || !string2.equals("random")) {
                    element3.setAttribute("generation", "fixed");
                } else {
                    element3.setAttribute("generation", "random");
                    String string3 = element.getAttributeValue("randomValue");
                    if (string3 != null) {
                        element3.setAttribute("randomValue", string3);
                    }
                    if (element2 != null) {
                        try {
                            Element element4 = XMLUtil.getItemParameter((Element)element2, (String)string, (boolean)false);
                            if (element4 == null) break block14;
                            String string4 = this.copyAttr(element4, element3, "minValue");
                            String string5 = this.copyAttr(element4, element3, "maxValue");
                            String string6 = this.copyAttr(element4, element3, "step");
                            if (string4.equals("0") && string5.equals("0") && string6.equals("0")) {
                                String string7 = element4.getAttributeValue("genMinValue");
                                if (string7 != null) {
                                    element3.setAttribute("minValue", string7);
                                }
                                if ((string7 = element4.getAttributeValue("genMaxValue")) != null) {
                                    element3.setAttribute("maxValue", string7);
                                }
                                element3.setAttribute("step", "1");
                            }
                        }
                        catch (Exception exception) {}
                    } else {
                        String string8 = element3.getAttributeValue("genMinValue");
                        if (string8 != null) {
                            element3.setAttribute("minValue", string8);
                        }
                        if ((string8 = element3.getAttributeValue("genMaxValue")) != null) {
                            element3.setAttribute("maxValue", string8);
                        }
                    }
                }
            }
        }
        return element3;
    }

    private String copyAttr(Element element, Element element2, String string) {
        String string2;
        if (element != null && element2 != null && string != null && (string2 = element.getAttributeValue(string)) != null) {
            element2.setAttribute(string, string2);
            return string2;
        }
        return "";
    }

    private void initBuildingBlocks(Element element) {
        List list = element.getChildren();
        this.arrayBuildingBlocks = new ArrayList<Element>();
        this.arrayBuildingBlocksArtifical = new ArrayList<Element>();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("key");
            if (string == null) continue;
            if (string.contains("talib_MAVP")) {
                element2.setAttribute("use", "false");
            }
            if (string.equals("AND")) {
                this.andWeight = element2.getAttributeValue("weight");
            }
            if (string.equals("OR")) {
                this.orWeight = element2.getAttributeValue("weight");
            }
            if (!string.contains(".")) {
                this.arrayBuildingBlocks.add(element2);
                continue;
            }
            this.arrayBuildingBlocksArtifical.add(element2);
        }
        if (this.andWeight == null) {
            this.andWeight = "0";
        }
        if (this.orWeight == null) {
            this.orWeight = "0";
        }
    }

    private void initCustomDataIndy(Element element) throws GenerateException {
        if (element == null) {
            return;
        }
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("use");
            if (string2 == null || !string2.equals("true")) continue;
            String string3 = element2.getAttributeValue("name");
            CustomDataInfo customDataInfo = CustomDataManager.getDataInfo((String)string3);
            if (customDataInfo == null) {
                Log.info("Cannot find custom data indicator '{}', ignoring!", (Object)string3);
                continue;
            }
            String string4 = element2.getAttributeValue("weight");
            Element element3 = this.convertCDataIndyToNBlock(customDataInfo, string4, string = element2.getAttributeValue("required"));
            if (element3 == null) continue;
            this.arrayBuildingBlocks.add(element3);
        }
    }

    private Element convertCDataIndyToNBlock(CustomDataInfo customDataInfo, String string, String string2) throws GenerateException {
        Element element = new Element("Block");
        element.setAttribute("key", "CDataIndy_" + customDataInfo.name);
        element.setAttribute("id", customDataInfo.name);
        element.setAttribute("use", "true");
        element.setAttribute("weight", string);
        element.setAttribute("dataType", Integer.toString(customDataInfo.dataType));
        element.addContent((Content)BlockSettingsConverter.createCDataShiftParamElement());
        element.addContent((Content)BlockSettingsConverter.createCDataValueParamElement(customDataInfo.values, customDataInfo));
        return element;
    }

    public static Element createCDataShiftParamElement() {
        Element element = new Element("Param");
        element.setAttribute("key", "#Shift#");
        element.setAttribute("type", "int");
        element.setAttribute("name", "Shift");
        element.setAttribute("step", "1");
        element.setAttribute("maxValue", "-1000002");
        element.setAttribute("minValue", "-1000001");
        element.setAttribute("generation", "random");
        element.setAttribute("controlType", "jspinnerVar");
        element.setAttribute("defaultValue", "1");
        return element;
    }

    public static Element createCDataValueParamElement(int n, CustomDataInfo customDataInfo) throws GenerateException {
        String string;
        Element element = new Element("Param");
        element.setAttribute("key", "#Value#");
        element.setAttribute("type", "int");
        element.setAttribute("name", "Value");
        element.setAttribute("controlType", "combo");
        element.setAttribute("defaultValue", "0");
        try {
            string = CustomDataManager.createCDataValues((int)n, (CustomDataInfo)customDataInfo);
        }
        catch (Exception exception) {
            throw new GenerateException(exception);
        }
        element.setAttribute("values", string);
        return element;
    }

    private void loadPartsToImprove(Element element) {
        Element element2;
        Element element3;
        Element element4;
        boolean bl = true;
        boolean bl2 = true;
        Element element5 = element.getChild("WhatToBuild");
        if (element5 != null && (element4 = element5.getChild("MarketSides")) != null) {
            element3 = element4.getChild("EntrySymmetry");
            if (element3 != null && element3.getText().equals("false")) {
                bl = true;
            }
            if ((element2 = element4.getChild("ExitSymmetry")) != null && element2.getText().equals("false")) {
                bl2 = true;
            }
        }
        if ((element3 = element.getChild("PartsToImprove")) != null) {
            Element element6;
            Element element7;
            element2 = element3.getChild("EntryRules");
            element4 = element2.getChild("LongImprovement");
            if (element4.getAttributeValue("use").equals("true")) {
                this.longEntryImprovement = true;
            }
            if ((element4 = element2.getChild("ShortImprovement")).getAttributeValue("use").equals("true")) {
                this.shortEntryImprovement = true;
            }
            if (bl && (this.longEntryImprovement || this.shortEntryImprovement)) {
                this.longEntryImprovement = true;
                this.longEntryImprovement = true;
            }
            if ((element4 = (element7 = element3.getChild("OrderTypes")).getChild("LongImprovement")).getAttributeValue("use").equals("true")) {
                this.longActionImprovement = true;
            }
            if ((element4 = element7.getChild("ShortImprovement")).getAttributeValue("use").equals("true")) {
                this.shortActionImprovement = true;
            }
            if ((element6 = element3.getChild("ExitRules")).getAttributeValue("symmetry").equals("true")) {
                element4 = element6.getChild("LongImprovement");
                if (element4.getAttributeValue("use").equals("true")) {
                    this.longExitImprovement = true;
                }
            } else {
                element4 = element6.getChild("ShortImprovement");
                if (element4.getAttributeValue("use").equals("true")) {
                    this.shortExitImprovement = true;
                }
            }
            if (bl2 && (this.longExitImprovement || this.shortExitImprovement)) {
                this.longExitImprovement = true;
                this.shortExitImprovement = true;
            }
        }
    }

    public Element convert() throws GenerateException {
        if (this.strategyType.equals("template")) {
            return this.createTemplateReplacements();
        }
        return this.createStandardReplacements();
    }

    private Element createTemplateReplacements() throws GenerateException {
        Element element = new Element("Replacements");
        element.setAttribute("type", "advanced");
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        GeneratorBase.checkUniqueRandomIdentifiers(this.strategyTemplate, hashMap);
        for (Map.Entry<String, Element> entry : hashMap.entrySet()) {
            Object object;
            String string = entry.getKey();
            Element element2 = entry.getValue();
            String string2 = element2.getAttributeValue("key");
            String string3 = element2.getAttributeValue("categoryType");
            String string4 = element2.getAttributeValue("superType");
            if (string4 != null) {
                if (string4.equals("condition")) {
                    object = this.createConditionReplacement(string, element2);
                    element.addContent((Content)object);
                    continue;
                }
                if (string4.equals("action")) {
                    object = this.createEntryReplacement(string, element2, 0);
                    element.addContent((Content)object);
                    continue;
                }
                if (string4.equals("value")) {
                    object = this.createValueReplacement(string, element2);
                    element.addContent((Content)object);
                    continue;
                }
            }
            if (string3 != null) {
                if (!string3.equals("other") || string2.startsWith("talib_")) {
                    object = this.createConditionReplacement(string, element2);
                    element.addContent((Content)object);
                    continue;
                }
                try {
                    Element element3;
                    object = Blocks.get(string2);
                    Class<?> clazz = object.getClass();
                    if (Blocks.checkContains(clazz, "ActionBlock")) {
                        element3 = this.createEntryReplacement(string, element2, 0);
                        element.addContent((Content)element3);
                        continue;
                    }
                    element3 = this.createConditionReplacement(string, element2);
                    element.addContent((Content)element3);
                    continue;
                }
                catch (BlockDefinitionException blockDefinitionException) {
                    throw new GenerateException(blockDefinitionException.getMessage());
                }
            }
            throw new GenerateException(String.format("Cannot find identifier type for %s !", string));
        }
        return element;
    }

    private Element createStandardReplacements() throws GenerateException {
        int n;
        Element element;
        Element element2 = new Element("Replacements");
        element2.setAttribute("type", "advanced");
        if (this.strategyType.equals("improve")) {
            if (this.longEntryImprovement) {
                element = this.createConditionReplacement("RandomConditionLong", null);
                element2.addContent((Content)element);
            }
        } else if (this.marketSides.equals("both") || this.marketSides.equals("long")) {
            element = this.createConditionReplacement("RandomConditionLong", null);
            element2.addContent((Content)element);
        }
        if (this.strategyType.equals("improve")) {
            if (this.shortEntryImprovement) {
                element = this.createConditionReplacement("RandomConditionShort", null);
                element2.addContent((Content)element);
            }
        } else if (this.marketSides.equals("short") || this.marketSides.equals("both") && !this.entrySymmetry) {
            element = this.createConditionReplacement("RandomConditionShort", null);
            element2.addContent((Content)element);
        }
        if (this.containsExitRule || this.longExitImprovement || this.shortExitImprovement) {
            if (this.marketSides.equals("both") || this.marketSides.equals("long") || this.longExitImprovement) {
                element = this.createExitReplacement("RandomConditionLongExit");
                element2.addContent((Content)element);
            }
            if (this.marketSides.equals("short") || this.marketSides.equals("both") && !this.exitSymmetry || this.shortExitImprovement) {
                element = this.createExitReplacement("RandomConditionShortExit");
                element2.addContent((Content)element);
            }
        }
        if (this.marketSides.equals("both") || this.marketSides.equals("long") || this.longActionImprovement || this.longExitImprovement) {
            element = this.createEntryReplacement("RandomActionLong", null, 1);
            element2.addContent((Content)element);
        }
        if (this.marketSides.equals("short") || this.marketSides.equals("both") && (!this.entrySymmetry || !this.exitSymmetry) || this.shortActionImprovement || this.shortExitImprovement) {
            element = this.createEntryReplacement("RandomActionShort", null, -1);
            element2.addContent((Content)element);
        }
        if ((n = StockpickerGenFixer.recognizeEngine(this.strategyTemplate)) == 1316847364 || n == -1816889229) {
            Element element3 = this.createValueReplacement("RandomPSValue", null);
            element2.addContent((Content)element3);
        }
        return element2;
    }

    private Element createEntryReplacement(String string, Element element, int n) throws GenerateException {
        Element element2 = new Element("Replacement");
        element2.setAttribute("identification", string);
        element2.setAttribute("type", "action");
        element2.setAttribute("probability", "100");
        element2.addContent((Content)this.elCharts.clone());
        this.addOrderTypeBlocks(element2, element, n);
        this.addStopLimitEntryBlocks(element2, "Stop/Limit Price Levels", null);
        this.addStopLimitEntryBlocks(element2, "Stop/Limit Price Ranges", null);
        return element2;
    }

    private boolean addStopLimitEntryBlocks(Element element, String string, Element element2) {
        String string2 = string + ".";
        if (element2 == null) {
            element2 = new Element("StopLimit" + string.replace("Stop/Limit Price ", ""));
            element.addContent((Content)element2);
        }
        boolean bl = false;
        for (int i = 0; i < this.arrayBuildingBlocksArtifical.size(); ++i) {
            String string3;
            Element element3 = this.arrayBuildingBlocksArtifical.get(i);
            if (!element3.getAttributeValue("use").equals("true") || !(string3 = element3.getAttributeValue("key")).contains(string)) continue;
            Element element4 = element3.clone();
            element4.setAttribute("key", string3.replace(string2, ""));
            element2.addContent((Content)element4);
            bl = true;
        }
        return bl;
    }

    private void addOrderTypeBlocks(Element element, Element element2, int n) throws GenerateException {
        String string;
        Element element3 = new Element("Blocks");
        element.addContent((Content)element3);
        String string2 = null;
        if (element2 != null && (string = element2.getAttributeValue("isParameter")) != null && string.equals("true")) {
            string2 = element2.getAttributeValue("key");
        }
        int n2 = 0;
        List list = this.elOrderTypes.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            if ((string2 != null || !element4.getAttributeValue("use").equals("true")) && !element4.getAttributeValue("key").equals(string2)) continue;
            Element element5 = element4.clone();
            this.replaceFormulas(element5, element2);
            this.updateNonFormulaExitTypeParams(element5);
            this.tryAddDirectionParam(element5, n);
            this.tryAddMagicNumberParam(element5);
            if (this.engine == 1316847364 || this.engine == -1816889229) {
                this.setFixedSPFormulas(element5);
            }
            element3.addContent((Content)element5);
            ++n2;
        }
        if (n2 == 0) {
            throw new GenerateException(String.format("Bad Configuration - You generate block '%s' randomly in your template, but it is not chosen in Building Blocks settings!", string2));
        }
    }

    private void updateNonFormulaExitTypeParams(Element element) throws GenerateException {
        String string;
        ArrayList<Element> arrayList = new ArrayList<Element>();
        List list = this.elExitTypes.getChildren("Block");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            string = element2.getAttributeValue("type");
            if (string != null && string.equals("formula")) continue;
            arrayList.add(element2.clone());
        }
        Element element3 = element.getChild("Generated");
        if (element3 != null) {
            list = element3.getChildren("Param");
            block1: for (int i = 0; i < list.size(); ++i) {
                string = (Element)list.get(i);
                String string2 = string.getAttributeValue("key");
                String string3 = string2.replace("#", "");
                for (int j = 0; j < arrayList.size(); ++j) {
                    Element element4 = (Element)arrayList.get(j);
                    if (!element4.getAttributeValue("key").equals(string3)) continue;
                    String string4 = element4.getAttributeValue("use");
                    if (string4 == null || string4.equals("false")) {
                        string.setAttribute("weight", "0");
                        string.setAttribute("minValue", "0");
                        string.setAttribute("maxValue", "0");
                        continue block1;
                    }
                    String string5 = this.getSubParamKey(string3);
                    Element element5 = XMLUtil.findFirstWithKey((Element)element4, (String)"Param", (String)string5);
                    if (element5 != null) {
                        String string6 = element5.getAttributeValue("generation");
                        String string7 = element5.getAttributeValue("minValue");
                        String string8 = element5.getAttributeValue("maxValue");
                        String string9 = element5.getAttributeValue("step");
                        String string10 = element5.getAttributeValue("values");
                        String string11 = element5.getAttributeValue("defaultValue");
                        string.setAttribute("generation", string6);
                        if (string6.equals("random")) {
                            String string12;
                            if (string7 != null) {
                                string.setAttribute("minValue", string7);
                            }
                            if (string8 != null) {
                                string.setAttribute("maxValue", string8);
                            }
                            if (string9 != null) {
                                string.setAttribute("step", string9);
                            }
                            if (string10 != null) {
                                string.setAttribute("values", string10);
                            }
                            if (!string3.equals("ExitAfterBars.ExitAfterBars") || (string12 = element4.getAttributeValue("probability")) == null) continue block1;
                            string.setAttribute("probability", string12);
                            continue block1;
                        }
                        string.setAttribute("defaultValue", string11);
                        continue block1;
                    }
                    Log.error("Cannot get parameters of exit type block with key '" + string3 + "'");
                    continue block1;
                }
            }
        }
    }

    private String getSubParamKey(String string) {
        String[] stringArray = string.split("\\.");
        if (stringArray == null || stringArray.length != 2) {
            return string;
        }
        return "#" + stringArray[1] + "#";
    }

    private void tryAddDirectionParam(Element element, int n) throws GenerateException {
        Element element2;
        Element element3 = element.getChild("Generated");
        if (element3 != null && (element2 = this.getItemsParam(element.getAttributeValue("key"), "#Direction#")) != null) {
            Element element4 = new Element("Param");
            element4.setAttribute("key", "#Direction#");
            element4.setAttribute("generation", "fixed");
            if (n != 0) {
                element4.setAttribute("defaultValue", Integer.toString(n));
            } else {
                element4.setAttribute("defaultValue", element2.getAttributeValue("defaultValue"));
            }
            element3.addContent((Content)element4);
        }
    }

    private void tryAddMagicNumberParam(Element element) throws GenerateException {
        Element element2;
        Element element3 = element.getChild("Generated");
        if (element3 != null && (element2 = this.getItemsParam(element.getAttributeValue("key"), "#MagicNumber#")) != null) {
            Element element4 = new Element("Param");
            element4.setAttribute("key", "#MagicNumber#");
            element4.setAttribute("generation", "fixed");
            element4.setAttribute("defaultValue", "MagicNumber");
            element3.addContent((Content)element4);
        }
    }

    private Element getItemsParam(String string, String string2) throws GenerateException {
        Element element;
        if (this.mapAllBlocksInConfig.containsKey(string.hashCode()) && (element = (Element)this.mapAllBlocksInConfig.get(string.hashCode())).getAttributeValue("key").equals(string)) {
            ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Param");
            for (int i = 0; i < arrayList.size(); ++i) {
                Element element2 = (Element)arrayList.get(i);
                if (!element2.getAttributeValue("key").equals(string2)) continue;
                Element element3 = element2.clone();
                return element3.detach();
            }
        }
        return null;
    }

    private Element getWizardConfig() throws GenerateException {
        if (this.wizardConfig != null) {
            return this.wizardConfig;
        }
        File file = new File(SQPaths.wizardConfigPath);
        if (!file.exists()) {
            throw new GenerateException("Wizard config file not found.");
        }
        try {
            this.wizardConfig = XMLUtil.fileToXmlElement((File)file);
            ArrayList arrayList = XMLUtil.getNestedElements((Element)this.wizardConfig.getChild("Blocks"), (String)"Item");
            this.mapAllBlocksInConfig = new Int2ObjectOpenHashMap();
            for (int i = 0; i < arrayList.size(); ++i) {
                Element element = (Element)arrayList.get(i);
                String string = element.getAttributeValue("key");
                if (string == null) continue;
                if (this.mapAllBlocksInConfig.containsKey(string.hashCode())) {
                    throw new GenerateException("Key '" + string + "' already exists in map - duplicate hash value!");
                }
                this.mapAllBlocksInConfig.put(string.hashCode(), (Object)element);
            }
            return this.wizardConfig;
        }
        catch (Exception exception) {
            throw new GenerateException(exception);
        }
    }

    private Element getWizardExitRule(String string) throws GenerateException {
        for (Element element : XMLUtil.getNestedElements((Element)this.getWizardConfig(), (String)"ExitRule")) {
            if (!element.getAttributeValue("key").equals(string)) continue;
            return element.clone().clone();
        }
        return null;
    }

    private Element createExitReplacement(String string) throws GenerateException {
        Element element = new Element("Replacement");
        element.setAttribute("identification", string);
        element.setAttribute("type", "condition");
        element.setAttribute("probability", this.exitRuleProbability);
        element.setAttribute("deleteRule", "true");
        element.setAttribute("andWeight", this.andWeight);
        element.setAttribute("orWeight", this.orWeight);
        element.addContent((Content)this.elCharts.clone());
        Element element2 = new Element("Blocks");
        element.addContent((Content)element2);
        if (!this.exitRuleProbability.equals("0")) {
            this.addConditionBlocks(element2);
        }
        return element;
    }

    private Element createConditionReplacement(String string, Element element) throws GenerateException {
        String string2;
        String string3;
        Element element2 = new Element("Replacement");
        element2.setAttribute("identification", string);
        element2.setAttribute("probability", "100");
        element2.setAttribute("andWeight", this.andWeight);
        element2.setAttribute("orWeight", this.orWeight);
        Element element3 = new Element("Blocks");
        element2.addContent((Content)element3);
        if (element != null) {
            string3 = this.getRandomGroupId(element);
            if (string3 != null) {
                Object object;
                if (this.mapRandomGroupBlocks != null && !this.mapRandomGroupBlocks.containsKey(string3)) {
                    throw new GenerateException("Template contains reference to random block group ID: " + string3 + "', but this group doesn't exist!");
                }
                ArrayList<Element> arrayList = this.mapRandomGroupBlocks.get(string3);
                for (int i = 0; i < arrayList.size(); ++i) {
                    object = arrayList.get(i).clone();
                    element3.addContent((Content)object);
                }
                String string4 = element.getAttributeValue("superType");
                if (string4 != null && string4.equals("value")) {
                    element2.setAttribute("type", "value");
                } else {
                    element2.setAttribute("type", "condition");
                }
                object = this.getChartIndex(element);
                Element element4 = object == null ? this.randomGroupCloneSelectedChart("0", this.elCharts) : this.randomGroupCloneSelectedChart((String)object, this.elCharts);
                List list = element4.getChildren();
                for (int i = 0; i < list.size(); ++i) {
                    Element element5 = (Element)list.get(i);
                    element5.setAttribute("minConditions", "1");
                    element5.setAttribute("maxConditions", "1");
                }
                element2.addContent((Content)element4);
                return element2;
            }
            string2 = element.getAttributeValue("isParameter");
            if (string2 != null && string2.equals("true")) {
                element2.addContent((Content)this.getChartsWithOneCondition(this.elCharts));
                Element element6 = this.getBlock(element.getAttributeValue("key"));
                this.tryAddDirectionParam(element6, 0);
                this.tryAddMagicNumberParam(element6);
                element3.addContent((Content)element6);
                this.fixRandomParametersInBlock(element6);
                String string5 = element.getAttributeValue("returnType");
                if (string5.equals("boolean")) {
                    element2.setAttribute("type", "condition");
                } else {
                    element2.setAttribute("type", "value");
                }
                return element2;
            }
        }
        string2 = (string3 = this.getChartIndex(element)) == null ? this.elCharts.clone() : this.randomGroupCloneSelectedChart(string3, this.elCharts);
        element2.addContent((Content)string2);
        element2.setAttribute("type", "condition");
        this.addConditionBlocks(element3);
        return element2;
    }

    private void fixRandomParametersInBlock(Element element) {
        Object object;
        if (element.getName().equals("Param") && (object = element.getAttributeValue("generation")) != null && ((String)object).equals("random")) {
            double d = this.getDoubleAttribute(element, "minValue", -1.0);
            double d2 = this.getDoubleAttribute(element, "maxValue", -1.0);
            double d3 = this.getDoubleAttribute(element, "genMinValue", -9999999.0);
            double d4 = this.getDoubleAttribute(element, "genMaxValue", -9999999.0);
            if (d3 != -9999999.0 && d != -1.0) {
                element.setAttribute("minValue", element.getAttributeValue("genMinValue"));
            }
            if (d4 != -9999999.0 && d2 != -1.0) {
                element.setAttribute("maxValue", element.getAttributeValue("genMaxValue"));
            }
        }
        object = element.getChildren();
        for (int i = 0; i < object.size(); ++i) {
            this.fixRandomParametersInBlock((Element)object.get(i));
        }
    }

    private double getDoubleAttribute(Element element, String string, double d) {
        String string2 = element.getAttributeValue(string);
        if (string2 == null) {
            return d;
        }
        try {
            return Double.parseDouble(string2);
        }
        catch (NumberFormatException numberFormatException) {
            return d;
        }
    }

    private Element createValueReplacement(String string, Element element) throws GenerateException {
        String string2;
        String string3;
        Element element2 = new Element("Replacement");
        element2.setAttribute("identification", string);
        element2.setAttribute("probability", "100");
        element2.setAttribute("andWeight", this.andWeight);
        element2.setAttribute("orWeight", this.orWeight);
        element2.setAttribute("type", "value");
        Element element3 = new Element("Blocks");
        element2.addContent((Content)element3);
        if (element != null) {
            string3 = this.getRandomGroupId(element);
            if (string3 != null) {
                Element element4;
                if (!this.mapRandomGroupBlocks.containsKey(string3)) {
                    throw new GenerateException("Template contains reference to random block group ID: " + string3 + "', but this group doesn't exist!");
                }
                ArrayList<Element> arrayList = this.mapRandomGroupBlocks.get(string3);
                for (int i = 0; i < arrayList.size(); ++i) {
                    element4 = arrayList.get(i).clone();
                    element3.addContent((Content)element4);
                }
                String string4 = this.getChartIndex(element);
                element4 = string4 == null ? this.elCharts.clone() : this.randomGroupCloneSelectedChart(string4, this.elCharts);
                List list = element4.getChildren();
                for (int i = 0; i < list.size(); ++i) {
                    Element element5 = (Element)list.get(i);
                    element5.setAttribute("minConditions", "1");
                    element5.setAttribute("maxConditions", "1");
                }
                element2.addContent((Content)element4);
                return element2;
            }
            string2 = element.getAttributeValue("isParameter");
            if (string2 != null && string2.equals("true")) {
                element2.addContent((Content)this.getChartsWithOneCondition(this.elCharts));
                Element element6 = this.getBlock(element.getAttributeValue("key"));
                this.tryAddDirectionParam(element6, 0);
                this.tryAddMagicNumberParam(element6);
                element3.addContent((Content)element6);
                String string5 = element.getAttributeValue("returnType");
                if (string5.equals("boolean")) {
                    element2.setAttribute("type", "condition");
                } else {
                    element2.setAttribute("type", "value");
                }
                return element2;
            }
        }
        string2 = (string3 = this.getChartIndex(element)) == null ? this.elCharts.clone() : this.randomGroupCloneSelectedChart(string3, this.elCharts);
        element2.addContent((Content)string2);
        if (string.equals("RandomPSValue")) {
            this.addStopLimitEntryBlocks(element2, "Stop/Limit Price Levels", element3);
            this.addStopLimitEntryBlocks(element2, "Stop/Limit Price Ranges", element3);
            this.addNormalBlocks(element3);
        } else {
            boolean bl = this.addStopLimitEntryBlocks(element2, "Stop/Limit Price Levels", element3);
        }
        return element2;
    }

    private void addNormalBlocks(Element element) {
        String string;
        Element element2;
        int n;
        HashSet<String> hashSet = new HashSet<String>();
        List list = element.getChildren();
        for (n = 0; n < list.size(); ++n) {
            element2 = (Element)list.get(n);
            string = element2.getAttributeValue("key");
            hashSet.add(string);
        }
        for (n = 0; n < this.arrayBuildingBlocksArtifical.size(); ++n) {
            Object object;
            String string2;
            element2 = this.arrayBuildingBlocksArtifical.get(n);
            if (!element2.getAttributeValue("use").equals("true")) continue;
            string = element2.getAttributeValue("key");
            if (string.contains(NAME_PRICES) && !hashSet.contains(string2 = string.replace(NAME_PRICES_DOT, ""))) {
                object = element2.clone();
                object.setAttribute("key", string2);
                element.addContent((Content)object);
            }
            if (!string.contains(NAME_RANDOM_INDICATOR_SIGNALS) || hashSet.contains(string2 = string.replace(NAME_RANDOM_INDICATOR_SIGNALS_DOT, "")) || (object = element2.getAttributeValue("category")) == null || !((String)object).equals("indicators") && !((String)object).equals("prices")) continue;
            Element element3 = element2.clone();
            element3.setAttribute("key", string2);
            element.addContent((Content)element3);
        }
    }

    private Element randomGroupCloneSelectedChart(String string, Element element) {
        Element element2 = new Element("Charts");
        List list = element.getChildren();
        int n = Integer.parseInt(string);
        if (list.size() <= n) {
            n = 0;
            Log.error("Random group uses chart index " + string + ", but there are not enough charts. Continuing with main chart.");
        }
        Element element3 = ((Element)list.get(n)).clone();
        element3.setAttribute("chartIndex", string);
        element2.addContent((Content)element3);
        return element2;
    }

    private String getRandomGroupId(Element element) throws GenerateException {
        try {
            Element element2 = XMLUtil.getItemParameter((Element)element, (String)"#Group#", (boolean)false);
            if (element2 == null) {
                return null;
            }
            String string = element2.getText();
            if (string == null || string.equals("")) {
                return null;
            }
            return string;
        }
        catch (Exception exception) {
            throw new GenerateException("Exception", exception);
        }
    }

    private String getChartIndex(Element element) throws GenerateException {
        if (element == null) {
            return null;
        }
        try {
            Element element2 = XMLUtil.getItemParameter((Element)element, (String)"#Chart#", (boolean)false);
            if (element2 == null) {
                return null;
            }
            String string = element2.getText();
            if (string == null || string.equals("") || string.equals("Any")) {
                return null;
            }
            return string;
        }
        catch (Exception exception) {
            throw new GenerateException("Exception", exception);
        }
    }

    private void addConditionBlocks(Element element) throws GenerateException {
        Object object;
        int n;
        boolean bl = false;
        for (n = 0; n < this.arrayBuildingBlocks.size(); ++n) {
            Element element2 = this.arrayBuildingBlocks.get(n);
            if (!element2.getAttributeValue("use").equals("true") || ((String)(object = element2.getAttributeValue("key"))).equals("AND") || ((String)object).equals("OR")) continue;
            if (((String)object).equals("BarHour") || ((String)object).equals("BarMinute")) {
                bl = true;
            }
            Element element3 = element2.clone();
            this.tryAddDirectionParam(element3, 0);
            this.tryAddMagicNumberParam(element3);
            element.addContent((Content)element3);
        }
        n = 0;
        boolean bl2 = false;
        object = new IntOpenHashSet();
        for (int i = 0; i < this.arrayBuildingBlocksArtifical.size(); ++i) {
            Element element4;
            String string;
            Element element5 = this.arrayBuildingBlocksArtifical.get(i);
            if (!element5.getAttributeValue("use").equals("true")) continue;
            String string2 = element5.getAttributeValue("key");
            if (string2.contains(NAME_PRICES) && !object.contains((string = string2.replace(NAME_PRICES_DOT, "")).hashCode())) {
                element4 = element5.clone();
                element4.setAttribute("key", string);
                element.addContent((Content)element4);
                n = 1;
                object.add(string.hashCode());
            }
            if (!string2.contains(NAME_RANDOM_INDICATOR_SIGNALS) || object.contains((string = string2.replace(NAME_RANDOM_INDICATOR_SIGNALS_DOT, "")).hashCode())) continue;
            element4 = element5.clone();
            element4.setAttribute("key", string);
            element.addContent((Content)element4);
            try {
                int n2 = Blocks.getReturnType(Blocks.get(string));
                if (n2 == 1 || n2 == 6) {
                    bl2 = true;
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            object.add(string.hashCode());
        }
        if (bl || bl2) {
            this.addNumberBlock(element);
        }
    }

    private void addNumberBlock(Element element) {
        Element element2 = new Element("Block");
        element2.setAttribute("key", "Number");
        element2.setAttribute("weight", "1");
        element2.setAttribute("use", "true");
        element2.setAttribute("category", "operators");
        Element element3 = new Element("Generated");
        element2.addContent((Content)element3);
        Element element4 = new Element("Param");
        element4.setAttribute("key", "#Number#");
        element4.setAttribute("name", "Number");
        element4.setAttribute("type", "double");
        element4.setAttribute("generation", "random");
        element4.setAttribute("weight", "1");
        element4.setAttribute("minValue", "0");
        element4.setAttribute("maxValue", "59");
        element4.setAttribute("step", "1");
        element3.addContent((Content)element4);
        element.addContent((Content)element2);
    }

    private Element getChartsWithOneCondition(Element element) {
        Element element2 = new Element("Charts");
        for (Element element3 : element.getChildren()) {
            Element element4 = element3.clone();
            element4.setAttribute("minConditions", "1");
            element4.setAttribute("maxConditions", "1");
            element4.setAttribute("minExitConditions", "1");
            element4.setAttribute("maxExitConditions", "1");
            element2.addContent((Content)element4);
        }
        return element2;
    }

    private Element getBlock(String string) throws GenerateException {
        Object object;
        Element element = null;
        for (int i = 0; i < this.arrayBuildingBlocks.size(); ++i) {
            element = this.arrayBuildingBlocks.get(i);
            object = element.getAttributeValue("key");
            if (!((String)object).equals(string)) continue;
            return element.clone();
        }
        element = null;
        if (this.mapAllBlocksInConfig.containsKey(string.hashCode())) {
            Object object22;
            Element element2 = (Element)this.mapAllBlocksInConfig.get(string.hashCode());
            element = new Element("Item");
            for (Object object22 : element2.getAttributes()) {
                element.setAttribute(object22.getName(), object22.getValue());
            }
            element.setAttribute("weight", "1");
            element.setAttribute("use", "true");
            object = new Element("Generated");
            object.setAttribute("weight", "1");
            element.addContent((Content)object);
            object22 = XMLUtil.getNestedElements((Element)element2, (String)"Param");
            for (int i = 0; i < object22.size(); ++i) {
                Element element3 = (Element)object22.get(i);
                element3 = element3.clone();
                element3.setAttribute("generation", "random");
                element3.setAttribute("weight", "1");
                object.addContent((Content)element3.clone());
            }
        }
        if (element == null) {
            throw new GenerateException(String.format("Bad configuration - Cannot find block '%s' in config!", string));
        }
        return element;
    }

    private void setFixedSPFormulas(Element element) throws GenerateException {
        Element element2 = element.getChild("Generated");
        if (element2 != null) {
            for (Element element3 : element2.getChildren("Param")) {
                String string = element3.getAttributeValue("key");
                if (!string.contains("MoveSL2BE") && !string.contains("TrailingStop")) continue;
                element3.setAttribute("generation", "fixed");
            }
        }
    }

    private void replaceFormulas(Element element, Element element2) throws GenerateException {
        String string = element.getAttributeValue("key");
        Element element3 = element.getChild("Formulas");
        if (element3 != null) {
            for (Element element4 : element3.getChildren("Formula")) {
                String string2;
                Element element5;
                String string3 = element4.getAttributeValue("key");
                if (string3.equalsIgnoreCase("#ProfitTarget.ProfitTarget#")) {
                    boolean bl;
                    boolean bl2 = bl = true;
                }
                if ((element5 = this.getFormulaReplacement(string, string3)) != null) {
                    element4.removeContent();
                    string2 = element5.getAttributeValue("probability");
                    if (string2 != null) {
                        element4.setAttribute("probability", string2);
                    }
                    for (Element element6 : element5.getChildren()) {
                        element4.addContent((Content)element6.clone().detach());
                    }
                    this.fixFormulaRandomValues(element4, element2);
                    continue;
                }
                string2 = this.getDependence(string, string3);
                if (string2 != null) {
                    element4.setAttribute("dependentOn", string2);
                }
                element4.setAttribute("probability", "0");
            }
        }
    }

    private void fixFormulaRandomValues(Element element, Element element2) {
        RandomValueConfig randomValueConfig;
        if (element2 == null) {
            return;
        }
        String string = element.getAttributeValue("key");
        Element element3 = null;
        try {
            element3 = XMLUtil.getItemParameter((Element)element2, (String)string, (boolean)false);
        }
        catch (Exception exception) {
            throw new RuntimeException(exception);
        }
        if (element3 == null) {
            return;
        }
        String string2 = element3.getAttributeValue("generate");
        if (string2 == null || !string2.equalsIgnoreCase("random")) {
            return;
        }
        String string3 = element3.getAttributeValue("randomValue");
        if (string3 == null || string3.equalsIgnoreCase("default") || string3.equalsIgnoreCase("")) {
            return;
        }
        boolean bl = false;
        String string4 = element3.getAttributeValue("type");
        if (string4 != null && string4.equalsIgnoreCase("double")) {
            bl = true;
        }
        if ((randomValueConfig = RandomValueConfig.parseRandomValue(string3, bl)) == null) {
            return;
        }
        for (Element element4 : element.getChildren()) {
            Element element5;
            Element element6;
            String string5 = element4.getAttributeValue("key");
            if (string5 == null || !string5.contains(".FixedValue") || (element6 = element4.getChild("Generated")) == null || (element5 = element6.getChild("Param")) == null) continue;
            String string6 = element5.getAttributeValue("generation");
            if (string6 == null || !string6.equalsIgnoreCase("random")) {
                return;
            }
            randomValueConfig.setMinMaxStepAttributes(element5);
        }
    }

    private Element getFormulaReplacement(String string, String string2) throws GenerateException {
        string2 = string2.replace("#", "");
        for (Element element : this.elExitTypes.getChildren("Block")) {
            Object object;
            if (!element.getAttributeValue("key").equals(string2)) continue;
            Element element2 = element.clone().detach();
            element2.setName("Formula");
            if (element.getAttributeValue("use").equals("true")) {
                element2.setAttribute("probability", element.getAttributeValue("probability"));
                object = element2.getChildren("Value");
                Element element3 = this.getWizardExitRule(string2);
                if (element3 != null) {
                    Iterator iterator = object.iterator();
                    while (iterator.hasNext()) {
                        Element element4 = (Element)iterator.next();
                        String string3 = element4.getAttributeValue("key");
                        if (element4.getChild("Generated") != null) continue;
                        for (Element element5 : element3.getChildren("Item")) {
                            Element element6;
                            if (!element5.getAttributeValue("key").equals(string3) || (element6 = this.transformFormulaElem(element5)) == null) continue;
                            element4.addContent((Content)element6);
                        }
                    }
                }
            } else {
                element2.setAttribute("probability", "0");
            }
            object = this.getNoneValueElem(string, string2);
            if (object != null) {
                element2.addContent((Content)object.clone().detach());
            }
            return element2;
        }
        Element element = this.getWizardFormulaElem(string2);
        if (element != null) {
            return element;
        }
        return null;
    }

    private Element getNoneValueElem(String string, String string2) throws GenerateException {
        String string3;
        Element element;
        String string4 = "#" + string2 + "#";
        Element element2 = this.getItemsParam(string, string4);
        if (element2 != null && (element = this.getWizardFormulaElem(string3 = element2.getAttributeValue("controlType"))) != null) {
            return element.getChild("ValueNone");
        }
        return null;
    }

    private Element getWizardFormulaElem(String string) throws GenerateException {
        for (Element element : XMLUtil.getNestedElements((Element)this.getWizardConfig(), (String)"Formula")) {
            if (!element.getAttributeValue("key").equals(string)) continue;
            Element element2 = element.clone().detach();
            element2.removeContent();
            for (Element element3 : element.getChildren("Item")) {
                Element element4 = element3.clone().detach();
                String string2 = element4.getAttributeValue("ignoreInBuilder");
                String string3 = element4.getAttributeValue("noneValue");
                if (string3 != null && string3.equals("true")) {
                    element4.setName("ValueNone");
                    element4.removeAttribute("name");
                    element4.removeAttribute("noneValue");
                    element2.addContent((Content)element4);
                    continue;
                }
                if (string2 != null && string2.equals("true")) continue;
                element4.setName("Value");
                element4.setAttribute("weight", "1");
                element4.setAttribute("use", "true");
                Element element5 = this.transformFormulaElem(element4);
                if (element5 != null) {
                    element4.addContent((Content)element5);
                }
                element4.removeContent((Content)element4.getChild("paramCategory"));
                element2.addContent((Content)element4);
            }
            return element2;
        }
        return null;
    }

    private Element transformFormulaElem(Element element) {
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Param");
        if (arrayList.size() == 0) {
            return null;
        }
        Element element2 = new Element("Generated");
        element2.setAttribute("weight", "1");
        for (Element element3 : arrayList) {
            Element element4 = element3.clone().detach();
            String string = element4.getAttributeValue("genMinValue");
            String string2 = element4.getAttributeValue("genMaxValue");
            if (string != null) {
                element4.removeAttribute("genMinValue");
                element4.setAttribute("minValue", string);
            }
            if (string2 != null) {
                element4.removeAttribute("genMaxValue");
                element4.setAttribute("maxValue", string2);
            }
            element4.removeAttribute("postfix");
            element4.removeAttribute("exitMethod");
            element4.removeAttribute("controlType");
            String string3 = element.getAttributeValue("key").equals("SQ.Formulas.Size.DefineOwnSize") ? "fixed" : "random";
            element4.setAttribute("generation", string3);
            element2.addContent((Content)element4);
        }
        return element2;
    }

    private String getDependence(String string, String string2) throws GenerateException {
        Element element = this.getItemsParam(string, string2);
        if (element != null) {
            return element.getAttributeValue("dependentOn");
        }
        return null;
    }

    private Element convertToCharts(Element element) {
        List list;
        Element element2 = new Element("Charts");
        boolean bl = false;
        String string = element.getAttributeValue("useDifferentSettings");
        if (string != null) {
            bl = string.equals("true");
        }
        if ((list = element.getChildren("Chart")).size() > 0) {
            Element element3 = (Element)list.get(0);
            String string2 = element3.getAttributeValue("minConditions");
            String string3 = element3.getAttributeValue("maxConditions");
            String string4 = element3.getAttributeValue("minExitConditions");
            String string5 = element3.getAttributeValue("maxExitConditions");
            String string6 = XMLUtil.tryGetAttr((Element)element3, (String)"minExitTypes", (String)"1");
            String string7 = XMLUtil.tryGetAttr((Element)element3, (String)"maxExitTypes", (String)"5");
            String string8 = XMLUtil.tryGetAttr((Element)element3, (String)"minPeriod", (String)"2");
            String string9 = XMLUtil.tryGetAttr((Element)element3, (String)"maxPeriod", (String)"2");
            String string10 = XMLUtil.tryGetAttr((Element)element3, (String)"minShift", (String)"1");
            String string11 = XMLUtil.tryGetAttr((Element)element3, (String)"maxShift", (String)"1");
            int n = Integer.parseInt(string10);
            int n2 = Integer.parseInt(string11);
            if (Engines.isTradestationEngine(this.engine)) {
                if (n2 > 0) {
                    string10 = "0";
                }
            } else if (n2 > 1) {
                string10 = "1";
            }
            for (int i = 0; i < list.size(); ++i) {
                Element element4 = (Element)list.get(i);
                Element element5 = new Element("Chart");
                if (!bl) {
                    element5.setAttribute("minConditions", string2);
                    element5.setAttribute("maxConditions", string3);
                    if (string4 != null) {
                        element5.setAttribute("minExitConditions", string4);
                    } else {
                        element5.setAttribute("minExitConditions", string4);
                    }
                    if (string5 != null) {
                        element5.setAttribute("maxExitConditions", string5);
                    } else {
                        element5.setAttribute("maxExitConditions", string3);
                    }
                    element5.setAttribute("minExitTypes", string6);
                    element5.setAttribute("maxExitTypes", string7);
                    element5.setAttribute("minPeriod", string8);
                    element5.setAttribute("maxPeriod", string9);
                    element5.setAttribute("minShift", string10);
                    element5.setAttribute("maxShift", string11);
                } else {
                    element5.setAttribute("minConditions", element4.getAttributeValue("minConditions"));
                    element5.setAttribute("maxConditions", element4.getAttributeValue("maxConditions"));
                    if (element4.getAttributeValue("minExitConditions") != null) {
                        element5.setAttribute("minExitConditions", element4.getAttributeValue("minExitConditions"));
                    } else {
                        element5.setAttribute("minExitConditions", element4.getAttributeValue("minConditions"));
                    }
                    if (element4.getAttributeValue("maxExitConditions") != null) {
                        element5.setAttribute("maxExitConditions", element4.getAttributeValue("maxExitConditions"));
                    } else {
                        element5.setAttribute("maxExitConditions", element4.getAttributeValue("maxConditions"));
                    }
                    element5.setAttribute("minExitTypes", string6);
                    element5.setAttribute("maxExitTypes", string7);
                    element5.setAttribute("minPeriod", XMLUtil.tryGetAttr((Element)element4, (String)"minPeriod", (String)"2"));
                    element5.setAttribute("maxPeriod", XMLUtil.tryGetAttr((Element)element4, (String)"maxPeriod", (String)"2"));
                    if (Engines.isTradestationEngine(this.engine)) {
                        element5.setAttribute("minShift", string10);
                    } else {
                        element5.setAttribute("minShift", XMLUtil.tryGetAttr((Element)element4, (String)"minShift", (String)"1"));
                    }
                    element5.setAttribute("maxShift", element4.getAttributeValue("maxShift", "1"));
                }
                element2.addContent((Content)element5);
            }
        }
        return element2;
    }

    private boolean checkContainsExitRule(Element element) {
        Element element2 = element.getChild("ExitTypes");
        for (Element element3 : element2.getChildren()) {
            if (!element3.getAttributeValue("key").equals("_ExitRule_")) continue;
            this.exitRuleProbability = element3.getAttributeValue("probability");
            String string = element3.getAttributeValue("use");
            if (string != null && string.equals("false")) {
                this.exitRuleProbability = "0";
            }
            return true;
        }
        if (this.exitRuleProbability == null) {
            this.exitRuleProbability = "0";
        }
        return false;
    }

    private void applyGlobalSLPTSettings(Element element, Element element2) {
        Element element3 = element.getChild("WhatToBuild").getChild("SLPTOptions");
        boolean bl = XMLUtil.getBoolean((Element)element3, (String)"SLATR", (boolean)false);
        boolean bl2 = XMLUtil.getBoolean((Element)element3, (String)"SLFixedPips", (boolean)false);
        boolean bl3 = XMLUtil.getBoolean((Element)element3, (String)"SLPercent", (boolean)false);
        boolean bl4 = XMLUtil.getBoolean((Element)element3, (String)"SeparatedSettings", (boolean)false);
        boolean bl5 = bl;
        boolean bl6 = bl2;
        boolean bl7 = bl3;
        if (bl4) {
            bl5 = XMLUtil.getBoolean((Element)element3, (String)"PTATR", (boolean)false);
            bl6 = XMLUtil.getBoolean((Element)element3, (String)"PTFixedPips", (boolean)false);
            bl7 = XMLUtil.getBoolean((Element)element3, (String)"PTPercent", (boolean)false);
        }
        List list = element2.getChild("ExitTypes").getChildren();
        this.updateExitType(list, "StopLoss.StopLoss", "SQ.Formulas.SLPT.ATRBasedValue", bl);
        this.updateExitType(list, "StopLoss.StopLoss", "SQ.Formulas.SLPT.FixedValue", bl2);
        this.updateExitType(list, "StopLoss.StopLoss", "SQ.Formulas.SLPT.PctValue", bl3);
        this.updateExitType(list, "ProfitTarget.ProfitTarget", "SQ.Formulas.SLPT.ATRBasedValue", bl5);
        this.updateExitType(list, "ProfitTarget.ProfitTarget", "SQ.Formulas.SLPT.FixedValue", bl6);
        this.updateExitType(list, "ProfitTarget.ProfitTarget", "SQ.Formulas.SLPT.PctValue", bl7);
    }

    private void updateExitType(List<Element> list, String string, String string2, boolean bl) {
        for (int i = 0; i < list.size(); ++i) {
            Element element = list.get(i);
            if (!element.getAttributeValue("key").equals(string)) continue;
            Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Value", (String)string2);
            if (element2 != null) {
                element2.setAttribute("use", bl ? "true" : "false");
            }
            return;
        }
    }
}

