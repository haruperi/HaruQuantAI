/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.gp.strategies.BuildSettings;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SelectedBlockGroups {
    public static final Logger Log = LoggerFactory.getLogger((String)"SelectedBlockGroups");
    private ArrayList<String> entryBlocks = new ArrayList();
    private ArrayList<String> stopLimitLevelBlocks = new ArrayList();

    public SelectedBlockGroups(BuildSettings buildSettings) {
        this.fillAllBlocks(buildSettings.getReplacements(), false);
        this.fillNegatedBlocks();
    }

    private void fillNegatedBlocks() {
        String string;
        String string2;
        int n;
        for (n = 0; n < this.entryBlocks.size(); ++n) {
            string2 = this.entryBlocks.get(n);
            string = Blocks.getOppositeBlockKey(string2);
            if (string == null || this.entryBlocks.contains(string)) continue;
            this.entryBlocks.add(string);
        }
        for (n = 0; n < this.stopLimitLevelBlocks.size(); ++n) {
            string2 = this.stopLimitLevelBlocks.get(n);
            string = Blocks.getOppositeBlockKey(string2);
            if (string == null || this.stopLimitLevelBlocks.contains(string)) continue;
            this.stopLimitLevelBlocks.add(string);
        }
    }

    private void fillAllBlocks(Element element, boolean bl) {
        if (element.getName().equals("StopLimitLevels") || element.getName().equals("StopLimitRanges")) {
            bl = true;
        }
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getName();
            if (string2.equals("Block") && (string = element2.getAttributeValue("key")) != null) {
                if (bl) {
                    if (!this.stopLimitLevelBlocks.contains(string)) {
                        this.stopLimitLevelBlocks.add(string);
                    }
                } else if (!this.entryBlocks.contains(string)) {
                    this.entryBlocks.add(string);
                }
            }
            this.fillAllBlocks(element2, bl);
        }
    }

    public boolean passed(Element element, boolean bl) {
        Object object;
        if (element.getName().equals("Formula") && ((String)(object = element.getAttributeValue("key"))).equals("SQ.Formulas.Price.UseFormula")) {
            bl = true;
        }
        object = element.getChildren();
        for (int i = 0; i < object.size(); ++i) {
            String string;
            String string2;
            Element element2 = (Element)object.get(i);
            String string3 = element2.getName();
            if (string3.equals("Item") && (string2 = element2.getAttributeValue("generated")) != null && (string = element2.getAttributeValue("key")) != null && !string.equals("Boolean") && !string.equals("AND") && !string.equals("OR") && (bl ? !this.stopLimitLevelBlocks.contains(string) : !this.entryBlocks.contains(string))) {
                return false;
            }
            if (this.passed(element2, bl)) continue;
            return false;
        }
        return true;
    }
}

