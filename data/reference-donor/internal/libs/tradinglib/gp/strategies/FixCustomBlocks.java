/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.StrategyGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FixCustomBlocks
implements IEvolutionaryOperator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"FixCustomBlocks");

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        for (int i = 0; i < list.size(); ++i) {
            Node node = list.get(i);
            this.fix(node.getStrategy());
        }
        return list;
    }

    private void fix(Element element) throws GenerateException {
        StrategyGenerator.fixValuesInCDataIndy(element);
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        this.fillCBMap(element, hashMap);
        Element element2 = element.getChild("Strategy");
        Element element3 = element2.getChild("CustomBlocks");
        if (element3 != null) {
            element2.removeChild("CustomBlocks");
        }
        element3 = new Element("CustomBlocks");
        element3.setAttribute("genby", "Neg");
        element2.addContent((Content)element3);
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
}

