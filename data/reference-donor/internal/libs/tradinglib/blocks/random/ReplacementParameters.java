/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementParameters {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementParameters");
    public static final byte Generated = 1;
    public static final byte Predefined = 2;
    public static final byte CDataIndy = 3;
    public byte generationType;
    public int weight;
    private BlockDefinition blockDef;
    public ArrayList<ReplacementParameter> parameters = new ArrayList();
    private ReplacementConfig replacementConfig;
    private BlocksConfig blocksConfig;
    public boolean containsFormulas;
    public boolean containsProfitTarget;
    private boolean hasBlockChildren;

    public ReplacementParameters(byte by, ReplacementsConfig replacementsConfig, BlocksConfig blocksConfig, BlockDefinition blockDefinition, ReplacementConfig replacementConfig, Element element, Element element2) throws GenerateException {
        if (blockDefinition == null) {
            throw new GenerateException("Block def cannot be null");
        }
        this.generationType = by;
        this.blockDef = blockDefinition;
        this.replacementConfig = replacementConfig;
        this.blocksConfig = blocksConfig;
        try {
            this.weight = Integer.parseInt(XMLUtil.getAttr((Element)element, (String)"weight", (String)"1"));
        }
        catch (Exception exception) {
            this.weight = 1;
        }
        if (by == 1) {
            this.parseGeneratedConfig(element, element2, replacementsConfig);
        } else {
            this.parsePredefinedConfig(element, element2, replacementsConfig);
        }
        this.containsFormulas = false;
        this.containsProfitTarget = false;
        this.hasBlockChildren = false;
        for (int i = 0; i < this.parameters.size(); ++i) {
            ReplacementParameter replacementParameter = this.parameters.get(i);
            if (replacementParameter.generation == 3) {
                this.containsFormulas = true;
            }
            if (replacementParameter.blockParam.key.contains("ProfitTarget.")) {
                this.containsProfitTarget = true;
            }
            if (replacementParameter.blockParam.type.equals("value")) {
                this.hasBlockChildren = true;
            }
            if (this.containsFormulas && this.containsProfitTarget && this.hasBlockChildren) break;
        }
    }

    public ReplacementParameters(byte by, ReplacementsConfig replacementsConfig, BlocksConfig blocksConfig, ReplacementConfig replacementConfig, int n, BlockDefinition blockDefinition, int n2, CustomDataInfo customDataInfo) throws GenerateException {
        this.generationType = by;
        this.blockDef = blockDefinition;
        this.replacementConfig = replacementConfig;
        this.blocksConfig = blocksConfig;
        this.containsFormulas = false;
        this.containsProfitTarget = false;
        this.hasBlockChildren = false;
        ReplacementParameter replacementParameter = ReplacementParameter.createCDataIndyShiftParam(blockDefinition, replacementsConfig, replacementConfig);
        this.parameters.add(replacementParameter);
        replacementParameter = ReplacementParameter.createCDataIndyValueParam(n, blockDefinition, replacementsConfig, replacementConfig, customDataInfo);
        this.parameters.add(replacementParameter);
    }

    private void parsePredefinedConfig(Element element, Element element2, ReplacementsConfig replacementsConfig) throws GenerateException {
        for (BlockParameter blockParameter : this.blockDef.parameters) {
            ReplacementParameter replacementParameter = new ReplacementParameter(1, replacementsConfig, blockParameter, this.blocksConfig, this.blockDef, this.replacementConfig);
            List list = element.getChildren();
            for (int i = 0; i < list.size(); ++i) {
                Element element3 = (Element)list.get(i);
                if (!element3.getAttributeValue("key").equals(blockParameter.key)) continue;
                replacementParameter.initFromGeneratedParam(this.blockDef.key, element3, element2);
                break;
            }
            this.parameters.add(replacementParameter);
        }
    }

    private void parseGeneratedConfig(Element element, Element element2, ReplacementsConfig replacementsConfig) throws GenerateException {
        for (int i = 0; i < this.blockDef.parameters.size(); ++i) {
            BlockParameter blockParameter = (BlockParameter)this.blockDef.parameters.get(i);
            ReplacementParameter replacementParameter = new ReplacementParameter(2, replacementsConfig, blockParameter, this.blocksConfig, this.blockDef, this.replacementConfig);
            List list = element.getChildren();
            for (int j = 0; j < list.size(); ++j) {
                Element element3 = (Element)list.get(j);
                if (!element3.getAttributeValue("key").equals(blockParameter.key)) continue;
                replacementParameter.initFromGeneratedParam(this.blockDef.key, element3, element2);
                break;
            }
            this.parameters.add(replacementParameter);
        }
    }

    public void fixParametersOrder(Element element) throws GenerateException {
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        for (Element object : element.getChildren()) {
            hashMap.put(object.getAttributeValue("key"), object);
        }
        for (ReplacementParameter replacementParameter : this.parameters) {
            Element element2 = (Element)hashMap.get(replacementParameter.blockParam.key);
            if (element2 == null) {
                throw new GenerateException("Block parameters map doesn't contain parameter with key '" + replacementParameter.blockParam.key + "'");
            }
            element2.detach();
            element.addContent((Content)element2);
        }
    }

    public boolean hasBlockChildren() {
        return this.hasBlockChildren;
    }

    public ReplacementParameter getChartParam() {
        for (int i = 0; i < this.parameters.size(); ++i) {
            ReplacementParameter replacementParameter = this.parameters.get(i);
            if (!replacementParameter.blockParam.type.equals("data")) continue;
            return replacementParameter;
        }
        return null;
    }

    public ReplacementParameter findReplacementParamByKey(String string) {
        for (int i = 0; i < this.parameters.size(); ++i) {
            ReplacementParameter replacementParameter = this.parameters.get(i);
            if (!replacementParameter.blockParam.key.equals(string)) continue;
            return replacementParameter;
        }
        return null;
    }

    public boolean verifyItem(Element element) throws GenerateException {
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("key");
            String string2 = element2.getAttributeValue("randomValue");
            if (string2 != null && (string2.equals("") || string2.equals("default"))) {
                string2 = null;
            }
            if (!(string2 != null ? !this.verifyRandomValue(element2, string2) : !this.verifyParamConfig(element2))) continue;
            return false;
        }
        return true;
    }

    private boolean verifyParamConfig(Element element) throws GenerateException {
        String string = element.getAttributeValue("key");
        ReplacementParameter replacementParameter = this.findReplacementParamByKey(string);
        if (replacementParameter == null) {
            Log.info("ReplacementParam for '" + string + "' not found!");
            return true;
        }
        return replacementParameter.verifyParam(string, element);
    }

    private boolean verifyRandomValue(Element element, String string) {
        String string2 = element.getAttributeValue("type");
        boolean bl = string2.equals("double");
        try {
            RandomValueConfig randomValueConfig = RandomValueConfig.parseRandomValue(string, bl);
            if (randomValueConfig == null) {
                Log.error("Error parsing randomValue '" + string + "' in strategy template.");
                return true;
            }
            String string3 = element.getText();
            if (string3 != null && !string3.isBlank()) {
                double d = bl ? Double.parseDouble(string3) : (double)Integer.parseInt(string3);
                return randomValueConfig.isInValidRange(d);
            }
        }
        catch (Exception exception) {
            Log.error("Exception ", (Throwable)exception);
        }
        return true;
    }
}

