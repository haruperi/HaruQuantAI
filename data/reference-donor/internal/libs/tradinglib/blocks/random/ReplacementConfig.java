/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.BlockSuperTypes;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.ItemRandomValueRanges;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementBlock;
import com.strategyquant.tradinglib.blocks.random.ReplacementBlocks;
import com.strategyquant.tradinglib.blocks.random.ReplacementChartConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementChartsConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameters;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.CheckersList;
import com.strategyquant.tradinglib.generator.GenerateException;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntArrayList;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementConfig {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementConfig");
    public Int2ObjectOpenHashMap<ReplacementBlocks> blocksByType = new Int2ObjectOpenHashMap();
    public ObjectArrayList<ReplacementBlock> allBlocks = new ObjectArrayList();
    public ObjectArrayList<ReplacementBlock> priceBlocks = new ObjectArrayList();
    public ObjectArrayList<ReplacementBlock> priceRangeBlocks = new ObjectArrayList();
    public int replacementSuperType;
    private IntArrayList availableBooleanTypes = new IntArrayList();
    private int andWeight;
    private int orWeight;
    private ReplacementChartsConfig chartsConfig = null;
    public String randomId;
    SettingsMap buildSettings;
    private double probability;
    public boolean deleteRule;
    private CheckersList checkersList;
    private String cachedRV;
    private RandomValueConfig cachedRVConfig;

    public ReplacementConfig(ReplacementsConfig replacementsConfig, BlocksConfig blocksConfig, Element element, SettingsMap settingsMap, CheckersList checkersList) throws GenerateException {
        ReplacementBlock replacementBlock;
        String string;
        Element element2;
        int n;
        this.buildSettings = settingsMap;
        this.checkersList = checkersList;
        this.replacementSuperType = BlockSuperTypes.translate(element.getAttributeValue("type"));
        if (this.replacementSuperType < 0) {
            throw new GenerateException("Block supertype '" + element.getAttributeValue("type") + "' is not recognized!");
        }
        this.randomId = element.getAttributeValue("identification");
        int n2 = this.loadIntAttribute(element, "probability", 100);
        this.probability = (double)n2 / 100.0;
        Element element3 = element.getChild("Charts");
        if (element3 == null) {
            if (this.replacementSuperType == 3 || this.replacementSuperType == 4 || this.replacementSuperType == 1) {
                throw new GenerateException("Block with type ='" + element.getAttributeValue("type") + "' doesn't have <Charts> settings!");
            }
        } else {
            this.chartsConfig = new ReplacementChartsConfig(element3, this.probability);
        }
        this.andWeight = this.loadIntAttribute(element, "andWeight", 1);
        this.orWeight = this.loadIntAttribute(element, "orWeight", 1);
        this.deleteRule = this.loadBoolAttribute(element, "deleteRule", false);
        List list = element.getChild("Blocks").getChildren();
        for (n = 0; n < list.size(); ++n) {
            element2 = (Element)list.get(n);
            string = element2.getAttributeValue("key");
            replacementBlock = new ReplacementBlock(replacementsConfig, string, blocksConfig, element2, this);
            if (replacementBlock == null || replacementBlock.blockDef == null) {
                throw new GenerateException("Block '" + string + "' was not found!");
            }
            this.allBlocks.add((Object)replacementBlock);
            if (replacementBlock.blockDef.superType != 2 && replacementBlock.blockDef.superType != 3 && replacementBlock.blockDef.superType != 1 || this.availableBooleanTypes.contains(replacementBlock.blockDef.superType)) continue;
            this.availableBooleanTypes.add(replacementBlock.blockDef.superType);
        }
        if (this.replacementSuperType == 5) {
            list = element.getChild("StopLimitLevels").getChildren();
            for (n = 0; n < list.size(); ++n) {
                element2 = (Element)list.get(n);
                string = element2.getAttributeValue("key");
                replacementBlock = new ReplacementBlock(replacementsConfig, string, blocksConfig, element2, this);
                if (replacementBlock == null || replacementBlock.blockDef == null) {
                    throw new GenerateException("Block '" + string + "' was not found!");
                }
                if (replacementBlock.blockDef.superType != 4 || replacementBlock.blockDef.returnType != 2) {
                    throw new GenerateException("Block '" + string + "' is not price level!");
                }
                this.priceBlocks.add((Object)replacementBlock);
            }
            list = element.getChild("StopLimitRanges").getChildren();
            for (n = 0; n < list.size(); ++n) {
                element2 = (Element)list.get(n);
                string = element2.getAttributeValue("key");
                replacementBlock = new ReplacementBlock(replacementsConfig, string, blocksConfig, element2, this);
                if (replacementBlock == null || replacementBlock.blockDef == null) {
                    throw new GenerateException("Block '" + string + "' was not found!");
                }
                if (replacementBlock.blockDef.superType != 4 || replacementBlock.blockDef.returnType != 7) {
                    throw new GenerateException("Block '" + string + "' is not price range!");
                }
                this.priceRangeBlocks.add((Object)replacementBlock);
            }
        }
        if (this.probability != 0.0 && this.replacementSuperType == 3 && this.availableBooleanTypes.size() == 0) {
            throw new GenerateException("You haven't selected any building blocks that can be used to construct conditions for random placeholder'" + this.randomId + "!");
        }
    }

    private boolean loadBoolAttribute(Element element, String string, boolean bl) {
        String string2 = element.getAttributeValue(string);
        return string2 != null ? Boolean.parseBoolean(string2) : bl;
    }

    private int loadIntAttribute(Element element, String string, int n) {
        String string2 = element.getAttributeValue(string);
        return string2 != null ? Integer.parseInt(string2) : n;
    }

    public Element generateRandomBlock(IRandomGenerator iRandomGenerator, int n, int n2, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (this.replacementSuperType == 3) {
            return this.generateRandomConditionBlock(iRandomGenerator, 0, n, n2, itemRandomValueRanges);
        }
        return this.generateRandomSimpleBlock(iRandomGenerator, 0, n, n2, itemRandomValueRanges);
    }

    private Element generateRandomConditionBlock(IRandomGenerator iRandomGenerator, int n, int n2, int n3, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        ReplacementChartConfig replacementChartConfig2;
        if (this.chartsConfig == null) {
            throw new GenerateException("chartsConfig cannot be null for condition!");
        }
        int n4 = 0;
        for (ReplacementChartConfig replacementChartConfig2 : this.chartsConfig) {
            int n5;
            int n6 = n3 == 2 ? replacementChartConfig2.minExitConditions : replacementChartConfig2.minConditions;
            int n7 = n5 = n3 == 2 ? replacementChartConfig2.maxExitConditions : replacementChartConfig2.maxConditions;
            if (n6 == n5) {
                replacementChartConfig2.setConditionsToGenerate(n3, n6);
            } else {
                replacementChartConfig2.setConditionsToGenerate(n3, this.getConditionsToGenerate(iRandomGenerator, n6, n5));
            }
            n4 += replacementChartConfig2.getConditionsToGenerate(n3);
        }
        if (n4 == 0) {
            if (n3 != 2) {
                return this.createAlwaysTrue();
            }
            return this.createAlwaysFalse();
        }
        if (n4 == 1) {
            return this.generateBooleanBlock(iRandomGenerator, this.getFirstChartWithConditionToGenerate(n3), n, n2, n3, itemRandomValueRanges);
        }
        Element element = this.generateAndOrBlock(this.getAndOrNameByWeight(iRandomGenerator));
        replacementChartConfig2 = this.getFirstChartWithConditionToGenerate(n3);
        element.addContent((Content)this.generateBooleanBlock(iRandomGenerator, replacementChartConfig2, n, n2, n3, itemRandomValueRanges));
        replacementChartConfig2.decreaseConditionsToGenerate(n3);
        while (true) {
            if (this.countConditionsToGenerate(n3) == 1) {
                replacementChartConfig2 = this.getFirstChartWithConditionToGenerate(n3);
                element.addContent((Content)this.generateBooleanBlock(iRandomGenerator, replacementChartConfig2, n, n2, n3, itemRandomValueRanges));
                return element;
            }
            replacementChartConfig2 = this.getFirstChartWithConditionToGenerate(n3);
            element.addContent((Content)this.generateBooleanBlock(iRandomGenerator, replacementChartConfig2, n, n2, n3, itemRandomValueRanges));
            replacementChartConfig2.decreaseConditionsToGenerate(n3);
            Element element2 = this.generateAndOrBlock(this.getAndOrNameByWeight(iRandomGenerator));
            element2.addContent((Content)element);
            element = element2;
        }
    }

    private Element createAlwaysFalse() {
        Element element = new Element("Item");
        element.setAttribute("key", "AlwaysFalse");
        element.setAttribute("name", "Always False");
        element.setAttribute("display", "Always False");
        element.setAttribute("mI", "BarAndTime");
        element.setAttribute("returnType", "boolean");
        element.setAttribute("categoryType", "simpleRules");
        return element;
    }

    private Element createAlwaysTrue() {
        Element element = new Element("Item");
        element.setAttribute("key", "AlwaysTrue");
        element.setAttribute("name", "Always True");
        element.setAttribute("display", "Always True");
        element.setAttribute("mI", "BarAndTime");
        element.setAttribute("returnType", "boolean");
        element.setAttribute("categoryType", "simpleRules");
        return element;
    }

    private int getConditionsToGenerate(IRandomGenerator iRandomGenerator, int n, int n2) {
        int n3;
        n = Math.min(n, 30);
        n2 = Math.min(n2, 30);
        int n4 = n;
        int n5 = n2 - n + 1;
        if (n5 == 1) {
            return n4 + iRandomGenerator.nextInt(1);
        }
        int n6 = 0;
        for (n3 = 0; n3 < n5; ++n3) {
            n6 = (int)((double)n6 + Math.pow(2.0, n3));
        }
        n3 = iRandomGenerator.nextInt(n6 + 1);
        n6 = 0;
        for (int i = 0; i < n5; ++i) {
            if (n3 > (n6 = (int)((double)n6 + Math.pow(2.0, i)))) continue;
            return n4 + (n5 - i - 1);
        }
        return n4 += iRandomGenerator.nextInt(n2 - n + 1);
    }

    private int countConditionsToGenerate(int n) {
        int n2 = 0;
        for (ReplacementChartConfig replacementChartConfig : this.chartsConfig) {
            n2 += replacementChartConfig.getConditionsToGenerate(n);
        }
        return n2;
    }

    private ReplacementChartConfig getFirstChartWithConditionToGenerate(int n) throws GenerateException {
        for (ReplacementChartConfig replacementChartConfig : this.chartsConfig) {
            if (replacementChartConfig.getConditionsToGenerate(n) <= 0) continue;
            return replacementChartConfig;
        }
        return null;
    }

    private Element generateRandomSimpleBlock(IRandomGenerator iRandomGenerator, int n, int n2, int n3, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        ReplacementChartConfig replacementChartConfig = this.getChartConfig(iRandomGenerator);
        return this.generateRandomBlock(this.replacementSuperType, iRandomGenerator, replacementChartConfig, false, n, n2, n3, itemRandomValueRanges);
    }

    private ReplacementChartConfig getChartConfig(IRandomGenerator iRandomGenerator) {
        if (this.chartsConfig == null) {
            return null;
        }
        if (this.chartsConfig.size() == 1) {
            return (ReplacementChartConfig)this.chartsConfig.get(0);
        }
        if (this.replacementSuperType == 5) {
            return (ReplacementChartConfig)this.chartsConfig.get(0);
        }
        return (ReplacementChartConfig)this.chartsConfig.get(iRandomGenerator.nextInt(this.chartsConfig.size()));
    }

    private String getAndOrNameByWeight(IRandomGenerator iRandomGenerator) {
        int n = iRandomGenerator.nextInt(this.andWeight + this.orWeight);
        if (n < this.andWeight) {
            return "AND";
        }
        return "OR";
    }

    private Element generateAndOrBlock(String string) {
        Element element = new Element("Item");
        element.setAttribute("key", string);
        return element;
    }

    private Element generateBooleanBlock(IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, int n, int n2, int n3, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (this.availableBooleanTypes.size() == 1) {
            return this.generateRandomBlock(this.availableBooleanTypes.getInt(0), iRandomGenerator, replacementChartConfig, false, n, n2, n3, itemRandomValueRanges);
        }
        int n4 = 0;
        while (true) {
            if (n4 > 100) {
                throw new GenerateException("Cannot generate correct block with this configuration, all possibilities refused by strategy verification");
            }
            int n5 = iRandomGenerator.nextInt(this.availableBooleanTypes.size());
            Element element = this.generateRandomBlock(this.availableBooleanTypes.getInt(n5), iRandomGenerator, replacementChartConfig, false, n, n2, false, n3, itemRandomValueRanges);
            if (element != null) {
                return element;
            }
            ++n4;
        }
    }

    private Element generateRandomBlock(int n, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, boolean bl, int n2, int n3, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        return this.generateRandomBlock(n, iRandomGenerator, replacementChartConfig, bl, n2, n3, true, n4, itemRandomValueRanges);
    }

    private Element generateRandomBlock(int n, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, boolean bl, int n2, int n3, boolean bl2, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (n2 > 10) {
            throw new GenerateException("Current depth is bigger than maximal depth!");
        }
        ReplacementBlocks replacementBlocks = this.getReplacementBlocksByType(n, -1, bl, n3, replacementChartConfig.chartIndex);
        int n5 = 0;
        while (true) {
            Element element;
            if (n5 > 1000) {
                if (bl2) {
                    throw new GenerateException("Cannot generate correct block with this configuration, all possibilities refused by strategy verification.");
                }
                return null;
            }
            ReplacementBlock replacementBlock = replacementBlocks.chooseRandomly(iRandomGenerator, n2);
            Element element2 = replacementBlock.getXml();
            String string = element2.getAttributeValue("keepParams");
            if (string != null && string.equals("true")) {
                element = element2.clone();
                this.fixSubchartsInSubblocks(element, n, replacementChartConfig);
            } else {
                element = this.cloneBlockElementWithoutChildren(element2);
                element.setName("Item");
                this.generateBlockParameters(replacementBlock, element, iRandomGenerator, n, replacementChartConfig, n2 + 1, n3, n4, itemRandomValueRanges);
            }
            if (this.checkersList.check(element)) {
                element.setAttribute("retries", Integer.toString(n5));
                return element;
            }
            ++n5;
        }
    }

    private void fixSubchartsInSubblocks(Element element, int n, ReplacementChartConfig replacementChartConfig) {
        if (n != 2) {
            return;
        }
        if (replacementChartConfig.chartIndex == 0) {
            return;
        }
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Param", (String)"key", (String)"#Chart#");
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element2 = (Element)arrayList.get(i);
            String string = element2.getText();
            if (string == null || !string.equals("0")) continue;
            element2.setText(Integer.toString(replacementChartConfig.chartIndex));
        }
    }

    private void removeGenerateAttributes(Element element) {
        element.removeAttribute("generate");
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            this.removeGenerateAttributes((Element)list.get(i));
        }
    }

    public Element generateSpecialBlock(IRandomGenerator iRandomGenerator, int n, int n2, int n3, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        ReplacementChartConfig replacementChartConfig = this.getChartConfig(iRandomGenerator);
        ReplacementBlock replacementBlock = this.chooseSpecialRandomly(iRandomGenerator, n);
        Element element = this.cloneBlockElementWithoutChildren(replacementBlock.getXml());
        element.setName("Item");
        this.generateBlockParameters(replacementBlock, element, iRandomGenerator, 4, replacementChartConfig, n2, n3, n4, itemRandomValueRanges);
        return element;
    }

    private ReplacementBlock chooseSpecialRandomly(IRandomGenerator iRandomGenerator, int n) throws GenerateException {
        ObjectArrayList<ReplacementBlock> objectArrayList;
        if (n == 2) {
            if (this.priceBlocks.size() == 0) {
                throw new GenerateException("There is no Price block defined!");
            }
            objectArrayList = this.priceBlocks;
        } else {
            if (this.priceRangeBlocks.size() == 0) {
                throw new GenerateException("There is no Price Range block defined!");
            }
            objectArrayList = this.priceRangeBlocks;
        }
        if (objectArrayList.size() == 1) {
            return (ReplacementBlock)objectArrayList.get(0);
        }
        int n2 = iRandomGenerator.nextInt(objectArrayList.size());
        return (ReplacementBlock)objectArrayList.get(n2);
    }

    private void generateBlockParameters(ReplacementBlock replacementBlock, Element element, IRandomGenerator iRandomGenerator, int n, ReplacementChartConfig replacementChartConfig, int n2, int n3, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (replacementBlock.parameters == null || replacementBlock.parameters.size() == 0) {
            return;
        }
        ReplacementParameters replacementParameters = replacementBlock.parameters.chooseRandomly(iRandomGenerator, replacementChartConfig, itemRandomValueRanges);
        ArrayList<ReplacementBlock> arrayList = null;
        for (ReplacementParameter iterator : replacementParameters.parameters) {
            if (iterator.generation == 3) continue;
            switch (iterator.blockParam.type) {
                case "value": {
                    boolean bl;
                    if (this.replacementSuperType != 3 || (iterator.blockParam.key.equals("#Indicator#") && (n == 1 || n == 4) || iterator.blockParam.key.startsWith("#Indicator") && (n == 1 || n == 4 || n == 2)) && !(bl = this.hasReplacementBlocksByType(4, -1, false, n3, replacementChartConfig.chartIndex))) break;
                    arrayList = this.addValueParam(arrayList, iterator, element, iRandomGenerator, n, replacementChartConfig, n2, n3, n4, itemRandomValueRanges);
                    break;
                }
                case "int": {
                    iterator.addIntParam(element, iRandomGenerator, replacementChartConfig, -1, itemRandomValueRanges);
                    break;
                }
                case "double": {
                    iterator.addDoubleParam(element, iRandomGenerator, itemRandomValueRanges);
                    break;
                }
                case "string": {
                    iterator.addStringParam(element, iRandomGenerator);
                    break;
                }
                case "boolean": {
                    iterator.addBooleanParam(element, iRandomGenerator);
                    break;
                }
                case "data": {
                    iterator.addDataParam(element, iRandomGenerator, replacementChartConfig);
                    break;
                }
                default: {
                    Log.error("Adding parameter of unknown type: " + iterator.blockParam.type);
                }
            }
        }
        if (replacementParameters.containsFormulas) {
            Object object = this.generateProfitTargetParam(replacementParameters, element, iRandomGenerator, replacementChartConfig, n3, n4);
            for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
                if (replacementParameter.generation != 3 || replacementParameter.formulaDependentOn != null || replacementParameter.blockParam.key.equals("#ProfitTarget.ProfitTarget#")) continue;
                replacementParameter.addFormulaParam(element, iRandomGenerator, replacementParameters.parameters, replacementChartConfig, n3, (double[])object, n4);
            }
            for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
                if (replacementParameter.generation != 3 || replacementParameter.formulaDependentOn == null) continue;
                replacementParameter.addFormulaParam(element, iRandomGenerator, replacementParameters.parameters, replacementChartConfig, n3, (double[])object, n4);
            }
            replacementParameters.fixParametersOrder(element);
        }
    }

    private double[] generateProfitTargetParam(ReplacementParameters replacementParameters, Element element, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, int n, int n2) throws GenerateException {
        if (!replacementParameters.containsProfitTarget) {
            return null;
        }
        for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
            if (!replacementParameter.blockParam.key.equals("#ProfitTarget.ProfitTarget#")) continue;
            replacementParameter.addFormulaParam(element, iRandomGenerator, replacementParameters.parameters, replacementChartConfig, n, null, n2);
            List list = element.getChildren();
            for (int i = 0; i < list.size(); ++i) {
                List list2;
                Element element2 = (Element)list.get(i);
                if (!element2.getAttributeValue("key").equals("#ProfitTarget.ProfitTarget#")) continue;
                Element element3 = element2.getChild("Formula");
                if (element3 == null) {
                    return null;
                }
                if (element3.getAttributeValue("key").equals("SQ.Formulas.SLPT.ATRBasedValue")) {
                    list2 = element3.getChildren();
                    double d = -1.0;
                    double d2 = -1.0;
                    for (int j = 0; j < list2.size(); ++j) {
                        String string;
                        Element element4 = (Element)list2.get(j);
                        if (element4.getAttributeValue("key").equals("#Value#")) {
                            string = element4.getText();
                            d = Double.parseDouble(string);
                        }
                        if (!element4.getAttributeValue("key").equals("#AtrPeriod#")) continue;
                        string = element4.getText();
                        d2 = Integer.parseInt(string);
                    }
                    return new double[]{-1.0, d, d2};
                }
                if (!element3.getAttributeValue("key").equals("SQ.Formulas.SLPT.FixedValue")) continue;
                list2 = element3.getChildren();
                for (int j = 0; j < list2.size(); ++j) {
                    Element element5 = (Element)list2.get(j);
                    if (!element5.getAttributeValue("key").equals("#Value#")) continue;
                    String string = element5.getText();
                    return new double[]{1.0, Double.parseDouble(string), 0.0};
                }
            }
        }
        return null;
    }

    private ArrayList<ReplacementBlock> addValueParam(ArrayList<ReplacementBlock> arrayList, ReplacementParameter replacementParameter, Element element, IRandomGenerator iRandomGenerator, int n, ReplacementChartConfig replacementChartConfig, int n2, int n3, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        if (n == 1 || n == 4) {
            Element element2 = this.generateRandomBlock(4, iRandomGenerator, replacementChartConfig, false, n2, n3, n4, itemRandomValueRanges);
            Element element3 = new Element("Block");
            element3.setAttribute("key", replacementParameter.blockParam.key);
            element3.addContent((Content)element2);
            element3.setAttribute("generated", "random");
            element3.setAttribute("randomId", this.randomId);
            element.addContent((Content)element3);
            return arrayList;
        }
        if (n == 2) {
            return this.addValueParamInComparison(arrayList, element, replacementParameter, iRandomGenerator, 4, replacementChartConfig, n2, n3, n4, itemRandomValueRanges);
        }
        if (n == 3) {
            throw new GenerateException("It shouldn't get here");
        }
        throw new GenerateException("Generating VALUE param for unknown supertype: " + n);
    }

    private ArrayList<ReplacementBlock> addValueParamInComparison(ArrayList<ReplacementBlock> arrayList, Element element, ReplacementParameter replacementParameter, IRandomGenerator iRandomGenerator, int n, ReplacementChartConfig replacementChartConfig, int n2, int n3, int n4, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        Element element2;
        ReplacementBlock replacementBlock;
        Object object;
        boolean bl;
        boolean bl2 = bl = arrayList == null;
        if (bl) {
            object = this.getReplacementBlocksByType(n, -1, bl, n3, replacementChartConfig.chartIndex);
            replacementBlock = ((ReplacementBlocks)object).chooseRandomly(iRandomGenerator, n2);
            element2 = this.cloneBlockElementWithoutChildren(replacementBlock.getXml());
            element.setName("Item");
            this.generateBlockParameters(replacementBlock, element2, iRandomGenerator, n, replacementChartConfig, n2 + 1, n3, n4, itemRandomValueRanges);
        } else {
            object = arrayList.get(0);
            ReplacementBlocks replacementBlocks = this.getReplacementBlocksByType(n, ((ReplacementBlock)object).blockDef.returnType, bl, n3, replacementChartConfig.chartIndex);
            replacementBlock = replacementBlocks.chooseRandomly(iRandomGenerator, n2);
            element2 = this.cloneBlockElementWithoutChildren(replacementBlock.getXml());
            element.setName("Item");
            if (((ReplacementBlock)object).blockDef.isIndicator && replacementBlock.blockDef.key.equals("Number")) {
                ReplacementParameters replacementParameters = replacementBlock.parameters.chooseRandomly(iRandomGenerator, replacementChartConfig, itemRandomValueRanges);
                ReplacementParameter replacementParameter2 = replacementParameters.parameters.get(0);
                if (replacementParameter2.generation == 2) {
                    this.generatorIndicatorComparisonValue((ReplacementBlock)object, replacementBlock, element2, replacementParameter2, iRandomGenerator);
                } else {
                    replacementParameter2.addDoubleParam(element2, iRandomGenerator, itemRandomValueRanges);
                }
            } else {
                this.generateBlockParameters(replacementBlock, element2, iRandomGenerator, n, replacementChartConfig, n2 + 1, n3, n4, itemRandomValueRanges);
            }
        }
        object = new Element("Block");
        object.setAttribute("key", replacementParameter.blockParam.key);
        object.addContent((Content)element2);
        element.addContent((Content)object);
        if (arrayList == null) {
            arrayList = new ArrayList();
        }
        arrayList.add(replacementBlock);
        return arrayList;
    }

    private void generatorIndicatorComparisonValue(ReplacementBlock replacementBlock, ReplacementBlock replacementBlock2, Element element, ReplacementParameter replacementParameter, IRandomGenerator iRandomGenerator) {
        double d;
        double d2 = replacementBlock.indicatorMin;
        double d3 = replacementBlock.indicatorMax;
        double d4 = replacementBlock.indicatorStep;
        if (d4 != 0.0) {
            int n = (int)((d3 - d2) / d4) + 1;
            if (n < 0) {
                d2 = d2 < 0.0 ? -10000.0 : 0.0;
                d3 = d3 > 0.0 ? 10000.0 : 0.0;
                if (d4 < 1.0) {
                    d4 = 1.0;
                }
                n = (int)((d3 - d2) / d4) + 1;
            }
            int n2 = iRandomGenerator.nextInt(n);
            d = d2 + (double)n2 * d4;
        } else {
            d = d2 + (d3 - d2) * iRandomGenerator.nextDouble();
        }
        Element element2 = new Element("Param");
        element2.setAttribute("key", replacementParameter.blockParam.key);
        element2.setAttribute("controlType", replacementParameter.blockParam.controlType);
        element2.setAttribute("type", replacementParameter.blockParam.type);
        element2.addContent(SQUtils.d2String((double)d, (int)replacementParameter.blockParam.decimals));
        element.addContent((Content)element2);
    }

    private ReplacementBlocks getReplacementBlocksByType(int n, int n2, boolean bl, int n3, int n4) throws GenerateException {
        ReplacementBlocks replacementBlocks;
        int n5 = SQUtils.betterHashNumbers((int[])new int[]{n, n2, bl ? 1000 : 2000, n3, n4});
        if (!this.blocksByType.containsKey(n5)) {
            replacementBlocks = this.createReplacementBlocks(n, n2, bl, n3, n4);
            if (replacementBlocks.size() == 0) {
                throw new GenerateException(String.format("No available %s blocks found for chart #%d at %s", BlockSuperTypes.translate(n), n4, this.randomId));
            }
            this.blocksByType.put(n5, (Object)replacementBlocks);
        } else {
            replacementBlocks = (ReplacementBlocks)this.blocksByType.get(n5);
        }
        return replacementBlocks;
    }

    private boolean hasReplacementBlocksByType(int n, int n2, boolean bl, int n3, int n4) throws GenerateException {
        ReplacementBlocks replacementBlocks;
        int n5 = SQUtils.betterHashNumbers((int[])new int[]{n, n2, bl ? 1000 : 2000, n3, n4});
        if (!this.blocksByType.containsKey(n5)) {
            replacementBlocks = this.createReplacementBlocks(n, n2, bl, n3, n4);
            if (replacementBlocks.size() == 0) {
                return false;
            }
        } else {
            replacementBlocks = (ReplacementBlocks)this.blocksByType.get(n5);
        }
        return replacementBlocks.size() > 0;
    }

    private ReplacementBlocks createReplacementBlocks(int n, int n2, boolean bl, int n3, int n4) throws GenerateException {
        ReplacementBlocks replacementBlocks = new ReplacementBlocks();
        for (int i = 0; i < this.allBlocks.size(); ++i) {
            ReplacementBlock replacementBlock = (ReplacementBlock)this.allBlocks.get(i);
            if (n != replacementBlock.blockDef.superType || n2 > 0 && replacementBlock.blockDef.returnType != n2 || !replacementBlock.key.startsWith("CDataIndy") && !replacementBlock.key.startsWith("CBlock") && !this.checkChartGeneration(replacementBlock, n4)) continue;
            if (n == 5) {
                replacementBlocks.add(replacementBlock);
                continue;
            }
            if (n == 2) {
                replacementBlocks.add(replacementBlock);
                continue;
            }
            if (n == 4) {
                if (bl) {
                    if (replacementBlock.blockDef.notFirstValue) continue;
                    replacementBlocks.add(replacementBlock);
                    continue;
                }
                replacementBlocks.add(replacementBlock);
                continue;
            }
            if (n == 1) {
                replacementBlocks.add(replacementBlock);
                continue;
            }
            if (n == 3) {
                replacementBlocks.add(replacementBlock);
                continue;
            }
            throw new GenerateException("Undefined superType: " + n);
        }
        return replacementBlocks;
    }

    private boolean checkChartGeneration(ReplacementBlock replacementBlock, int n) {
        ReplacementParameter replacementParameter = replacementBlock.parameters.getChartParam();
        if (replacementParameter == null) {
            return true;
        }
        if (replacementParameter.generation == 1) {
            String string = replacementParameter.blockParam.getParamAttribute("defaultValue");
            if (string == null || string.equals("")) {
                return true;
            }
            if (string.equals(Integer.toString(n))) {
                return true;
            }
            Log.info("Chart param for block {}  doesn't equal this chart index); {} != {}", new Object[]{replacementBlock.blockDef.key, string, n});
            return false;
        }
        return true;
    }

    private Element cloneBlockElementWithoutChildren(Element element) {
        Element element2 = new Element(element.getName());
        for (Attribute attribute : element.getAttributes()) {
            element2.setAttribute(attribute.clone());
        }
        element2.setAttribute("generated", "random");
        element2.setAttribute("randomId", this.randomId);
        return element2;
    }

    public boolean shouldGenerate(IRandomGenerator iRandomGenerator) {
        return iRandomGenerator.probability(this.probability);
    }

    public boolean hasStopLimitOrder() {
        for (ReplacementBlock replacementBlock : this.allBlocks) {
            for (BlockParameter blockParameter : replacementBlock.blockDef.parameters) {
                if (!blockParameter.key.equals("#Price#")) continue;
                return true;
            }
        }
        return false;
    }

    public boolean hasPriceAndRangeBlocks() {
        return this.priceBlocks.size() > 0 && this.priceRangeBlocks.size() > 0;
    }

    public Element generateMutatedRandomBlock(IRandomGenerator iRandomGenerator, Element element, int n, int n2) throws GenerateException {
        int n3 = 0;
        while (n3 <= 100) {
            ReplacementBlock replacementBlock = this.getBlockByKey(element.getAttributeValue("key"));
            ReplacementChartConfig replacementChartConfig = (ReplacementChartConfig)this.chartsConfig.get(0);
            this.generateBlockParameters(replacementBlock, element, iRandomGenerator, replacementBlock.blockDef.superType, replacementChartConfig, 0, n, n2, null);
            if (this.checkersList.check(element)) {
                element.setAttribute("retries", Integer.toString(n3));
                return element;
            }
            ++n3;
        }
        return null;
    }

    private ReplacementBlock getBlockByKey(String string) throws GenerateException {
        int n;
        for (n = 0; n < this.allBlocks.size(); ++n) {
            if (!((ReplacementBlock)this.allBlocks.get((int)n)).key.equals(string)) continue;
            return (ReplacementBlock)this.allBlocks.get(n);
        }
        for (n = 0; n < this.priceBlocks.size(); ++n) {
            if (!((ReplacementBlock)this.priceBlocks.get((int)n)).key.equals(string)) continue;
            return (ReplacementBlock)this.priceBlocks.get(n);
        }
        for (n = 0; n < this.priceRangeBlocks.size(); ++n) {
            if (!((ReplacementBlock)this.priceRangeBlocks.get((int)n)).key.equals(string)) continue;
            return (ReplacementBlock)this.priceRangeBlocks.get(n);
        }
        throw new GenerateException(String.format("Cannot find block with key %s", string));
    }

    double generateValueFromRandomValue(String string, ItemRandomValueRanges itemRandomValueRanges, IRandomGenerator iRandomGenerator, boolean bl) {
        if (itemRandomValueRanges == null) {
            return bl ? Double.MAX_VALUE : 2.147483647E9;
        }
        String string2 = itemRandomValueRanges.getForParam(string);
        if (string2 == null) {
            return bl ? Double.MAX_VALUE : 2.147483647E9;
        }
        RandomValueConfig randomValueConfig = this.getRandomValueConfig(string2, bl);
        if (!randomValueConfig.isValid()) {
            return bl ? Double.MAX_VALUE : 2.147483647E9;
        }
        return randomValueConfig.generateRandomValue(iRandomGenerator, bl);
    }

    private RandomValueConfig getRandomValueConfig(String string, boolean bl) {
        if (this.cachedRV == null || !this.cachedRV.equals(string)) {
            this.cachedRV = string;
            this.cachedRVConfig = this.createRandomValueConfig(string, bl);
        }
        return this.cachedRVConfig;
    }

    private RandomValueConfig createRandomValueConfig(String string, boolean bl) {
        RandomValueConfig randomValueConfig = RandomValueConfig.parseRandomValue(string, bl);
        if (randomValueConfig != null) {
            return randomValueConfig;
        }
        Log.error("Error parsing randomValue '" + string + "' in strategy template.");
        return new RandomValueConfig(false);
    }

    public int getDecimals(String string, ItemRandomValueRanges itemRandomValueRanges, int n) {
        if (itemRandomValueRanges == null) {
            return n;
        }
        String string2 = itemRandomValueRanges.getForParam(string);
        if (string2 == null) {
            return n;
        }
        RandomValueConfig randomValueConfig = this.getRandomValueConfig(string2, true);
        if (!randomValueConfig.isValid()) {
            return n;
        }
        return randomValueConfig.getDecimals(n);
    }

    public int getDecimals(double d, int n) {
        int n2;
        BigDecimal bigDecimal = BigDecimal.valueOf(d);
        int n3 = bigDecimal.scale();
        if (n3 > (n2 = n)) {
            n2 = n3;
        }
        if (n2 > 6) {
            n2 = 6;
        }
        return n2;
    }

    public ReplacementBlock findBlockByKey(String string) {
        for (int i = 0; i < this.allBlocks.size(); ++i) {
            ReplacementBlock replacementBlock = (ReplacementBlock)this.allBlocks.get(i);
            if (!replacementBlock.blockDef.key.equals(string)) continue;
            return replacementBlock;
        }
        return null;
    }

    public boolean checkPriceRangeBlockExists() {
        return this.priceRangeBlocks.size() > 0;
    }

    public boolean verifyItem(String string, Element element) throws GenerateException {
        ReplacementBlock replacementBlock = this.getBlockByKey(string);
        return replacementBlock.verifyItem(element);
    }
}

