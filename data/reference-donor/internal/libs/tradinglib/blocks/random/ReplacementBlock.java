/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameterGroups;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameters;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.BlockSettingsConverter;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementBlock {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementBlock");
    public int weight;
    public String key;
    public ReplacementParameterGroups parameters = new ReplacementParameterGroups();
    public BlockDefinition blockDef;
    private ReplacementConfig replacementConfig;
    private boolean hasBlockChildren;
    public double indicatorMin;
    public double indicatorMax;
    public double indicatorStep;
    private String cdataId;
    private int cdataType;
    private Element xml;

    public ReplacementBlock(ReplacementsConfig replacementsConfig, String string, BlocksConfig blocksConfig, Element element, ReplacementConfig replacementConfig) throws GenerateException {
        this.replacementConfig = replacementConfig;
        this.key = string;
        if (this.key.startsWith("CDataIndy")) {
            this.initCustomDataIndy(element, replacementsConfig, blocksConfig);
            return;
        }
        this.weight = Integer.parseInt(element.getAttributeValue("weight"));
        this.blockDef = blocksConfig.getBlock(string);
        if (this.blockDef == null) {
            throw new GenerateException(String.format("Block '%s' cannot be found!", string));
        }
        String string2 = element.getAttributeValue("keepParams");
        this.xml = string2 == null || !string2.equals("true") ? this.blockDef.getXml() : this.createCorrectBlockElement(element, this.blockDef.getXml());
        try {
            this.indicatorMin = this.loadDoubleAttribute(element, "indicatorMin", this.blockDef.indicatorMin);
            this.indicatorMax = this.loadDoubleAttribute(element, "indicatorMax", this.blockDef.indicatorMax);
            this.indicatorStep = this.loadDoubleAttribute(element, "indicatorStep", this.blockDef.indicatorStep);
        }
        catch (NumberFormatException numberFormatException) {
            String string3 = XMLUtil.elementToString((Element)element);
            throw new NumberFormatException("Problem parsing double, XML: " + string3);
        }
        if (element.getChild("Generated") != null) {
            ReplacementParameters replacementParameters = new ReplacementParameters(1, replacementsConfig, blocksConfig, this.blockDef, replacementConfig, element.getChild("Generated"), element.getChild("Formulas"));
            this.hasBlockChildren = replacementParameters.hasBlockChildren();
            this.parameters.add(replacementParameters);
        }
        if (element.getChild("Predefined") != null) {
            List list = element.getChild("Predefined").getChildren();
            for (int i = 0; i < list.size(); ++i) {
                Element element2 = (Element)list.get(i);
                ReplacementParameters replacementParameters = new ReplacementParameters(2, replacementsConfig, blocksConfig, this.blockDef, replacementConfig, element2, null);
                this.parameters.add(replacementParameters);
            }
        }
    }

    private Element createCorrectBlockElement(Element element, Element element2) throws GenerateException {
        Element element3 = new Element("Item");
        XMLUtil.copyAttributes((Element)element, (Element)element3, (boolean)false);
        XMLUtil.copyAttributes((Element)element2, (Element)element3, (boolean)false);
        Element element4 = element.getChild("Generated");
        if (element4 == null) {
            throw new GenerateException("Incorrect block format for random group!");
        }
        List list = element4.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element5 = (Element)list.get(i);
            element3.addContent((Content)element5.clone());
        }
        return element3;
    }

    private void initCustomDataIndy(Element element, ReplacementsConfig replacementsConfig, BlocksConfig blocksConfig) throws GenerateException {
        this.weight = Integer.parseInt(element.getAttributeValue("weight"));
        this.cdataId = element.getAttributeValue("id");
        this.cdataType = Integer.parseInt(element.getAttributeValue("dataType"));
        CustomDataInfo customDataInfo = CustomDataManager.getDataInfo((String)this.cdataId);
        if (customDataInfo == null) {
            throw new GenerateException("Cannot find custom data indicator '" + this.cdataId + "', ignoring!");
        }
        this.blockDef = this.createBlockDefForCDataIndy(customDataInfo);
        this.xml = this.blockDef.getXml();
        ReplacementParameters replacementParameters = new ReplacementParameters(3, replacementsConfig, blocksConfig, this.replacementConfig, customDataInfo.values, this.blockDef, Integer.parseInt(element.getAttributeValue("weight")), customDataInfo);
        this.hasBlockChildren = false;
        this.parameters.add(replacementParameters);
    }

    private BlockDefinition createBlockDefForCDataIndy(CustomDataInfo customDataInfo) throws GenerateException {
        BlockDefinition blockDefinition = new BlockDefinition(this.cdataId, this.cdataType);
        blockDefinition.key = "CDataIndy_" + this.cdataId;
        blockDefinition.name = this.cdataId;
        Element element = BlockSettingsConverter.createCDataShiftParamElement();
        blockDefinition.parameters.add((Object)new BlockParameter(element));
        element = BlockSettingsConverter.createCDataValueParamElement(customDataInfo.values, customDataInfo);
        blockDefinition.parameters.add((Object)new BlockParameter(element));
        switch (this.cdataType) {
            case 1: {
                blockDefinition.superType = 4;
                blockDefinition.returnType = 2;
                break;
            }
            case 2: {
                blockDefinition.superType = 4;
                blockDefinition.returnType = 1;
                break;
            }
            case 3: {
                blockDefinition.superType = 4;
                blockDefinition.returnType = 7;
                break;
            }
            case 10: {
                blockDefinition.superType = 3;
                blockDefinition.returnType = 3;
                break;
            }
            case 11: {
                blockDefinition.superType = 3;
                blockDefinition.returnType = 3;
            }
        }
        return blockDefinition;
    }

    private double loadDoubleAttribute(Element element, String string, double d) {
        String string2 = element.getAttributeValue(string);
        return string2 != null && !string2.equals("undefined") ? Double.parseDouble(string2) : d;
    }

    public boolean hasBlockChildren() {
        return this.hasBlockChildren;
    }

    public Element getXml() {
        return this.xml;
    }

    public ReplacementParameter findReplacementParamByKey(String string) {
        for (int i = 0; i < this.parameters.size(); ++i) {
            ReplacementParameters replacementParameters = (ReplacementParameters)this.parameters.get(i);
            ReplacementParameter replacementParameter = replacementParameters.findReplacementParamByKey(string);
            if (replacementParameter == null) continue;
            return replacementParameter;
        }
        return null;
    }

    public boolean verifyItem(Element element) throws GenerateException {
        for (int i = 0; i < this.parameters.size(); ++i) {
            ReplacementParameters replacementParameters = (ReplacementParameters)this.parameters.get(i);
            if (!replacementParameters.verifyItem(element)) continue;
            return true;
        }
        return false;
    }
}

