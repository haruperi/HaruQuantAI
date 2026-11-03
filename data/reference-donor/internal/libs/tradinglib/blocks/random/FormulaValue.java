/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameterGroups;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameters;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import org.jdom2.Element;

public class FormulaValue {
    public String key;
    public int weight;
    public boolean isNoneValue;
    public ReplacementParameterGroups parameters = new ReplacementParameterGroups();
    public BlockDefinition blockDef;
    public double exitBasedType = 0.0;

    public FormulaValue(ReplacementsConfig replacementsConfig, Element element, BlocksConfig blocksConfig, ReplacementConfig replacementConfig) throws GenerateException {
        Object object;
        this.key = element.getAttributeValue("key");
        String string = element.getAttributeValue("weight");
        this.weight = string == null ? 1 : Integer.parseInt(string);
        this.isNoneValue = element.getName().equals("ValueNone");
        this.blockDef = blocksConfig.getFormula(this.key);
        if (element.getChild("Generated") != null) {
            object = new ReplacementParameters(1, replacementsConfig, blocksConfig, this.blockDef, replacementConfig, element.getChild("Generated"), null);
            this.parameters.add((ReplacementParameters)object);
        }
        if (element.getChild("Predefined") != null) {
            object = element.getChild("Predefined").getChildren();
            for (int i = 0; i < object.size(); ++i) {
                Element element2 = (Element)object.get(i);
                ReplacementParameters replacementParameters = new ReplacementParameters(2, replacementsConfig, blocksConfig, this.blockDef, replacementConfig, element2, null);
                this.parameters.add(replacementParameters);
            }
        }
        if (this.key.contains("ATRBasedValue")) {
            this.exitBasedType = -1.0;
        } else if (this.key.contains("FixedValue")) {
            this.exitBasedType = 1.0;
        }
    }
}

