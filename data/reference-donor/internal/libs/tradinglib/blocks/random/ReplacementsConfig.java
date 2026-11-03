/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementBlock;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameter;
import com.strategyquant.tradinglib.generator.Checkers;
import com.strategyquant.tradinglib.generator.CheckersList;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.Negaters;
import com.strategyquant.tradinglib.strategy.xml.XmlStrategyException;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Element;

public class ReplacementsConfig
extends HashMap<String, ReplacementConfig> {
    public NegatersList negatersList;
    public CheckersList checkersList = Checkers.list();

    public ReplacementsConfig(Element element, BlocksConfig blocksConfig, IRandomGenerator iRandomGenerator, SettingsMap settingsMap) throws GenerateException {
        this.negatersList = Negaters.list();
        for (Element element2 : element.getChildren()) {
            ReplacementConfig replacementConfig = new ReplacementConfig(this, blocksConfig, element2, settingsMap, this.checkersList);
            this.put(element2.getAttributeValue("identification"), replacementConfig);
        }
    }

    public IBlock negateBlock(IBlock iBlock, StrategyBase strategyBase) throws BlockDefinitionException, XmlStrategyException {
        return this.negatersList.negate(iBlock, strategyBase);
    }

    public void checkAllExist(ArrayList<String> arrayList) throws GenerateException {
        for (int i = 0; i < arrayList.size(); ++i) {
            if (this.containsKey(arrayList.get(i))) continue;
            throw new GenerateException(String.format("Bad configuration - identifier '%s' referenced in Random block or parameter doesn't exist in ReplacementsConfig!", arrayList.get(i)));
        }
    }

    public ReplacementConfig get(String string) throws GenerateException {
        if (!this.containsKey(string)) {
            throw new GenerateException("No config for placeholder '" + string + "'");
        }
        return (ReplacementConfig)super.get(string);
    }

    public ReplacementParameter findReplacementParamByKey(String string, String string2) {
        for (ReplacementConfig replacementConfig : this.values()) {
            ReplacementBlock replacementBlock = replacementConfig.findBlockByKey(string);
            if (replacementBlock == null) continue;
            return replacementBlock.findReplacementParamByKey(string2);
        }
        return null;
    }
}

