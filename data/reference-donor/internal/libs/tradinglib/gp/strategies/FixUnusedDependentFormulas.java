/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FixUnusedDependentFormulas
implements IEvolutionaryOperator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"FixUnusedDependentFormulas");

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        for (int i = 0; i < list.size(); ++i) {
            Node node = list.get(i);
            FixUnusedDependentFormulas.fix(node.getStrategy());
        }
        return list;
    }

    public static void fix(Element element) throws GenerateException {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Object object;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Param")) {
                Element element3;
                Element element4;
                object = element2.getAttributeValue("key");
                String string = null;
                if (((String)object).equals("#TrailingStop.TrailingActivation#")) {
                    string = "TrailingStop.TrailingStop";
                }
                if (((String)object).equals("#MoveSL2BE.SL2BEAddPips#")) {
                    string = "MoveSL2BE.MoveSL2BE";
                }
                if (string != null && (element4 = FixUnusedDependentFormulas.getDependentParamFormula(element, string)) != null && !FixUnusedDependentFormulas.isFormulaUsed(element4) && (element3 = element2.getChild("Formula")) != null) {
                    String string2 = element3.getAttributeValue("key");
                    string2 = FixUnusedDependentFormulas.setNoneFormula(string2);
                    element3.setAttribute("key", string2);
                    element3.removeContent();
                }
            }
            if ((object = element2.getChildren()) == null) continue;
            FixUnusedDependentFormulas.fix(element2);
        }
    }

    private static String setNoneFormula(String string) {
        int n = string.lastIndexOf(".");
        if (n > 0) {
            return string.substring(0, n) + ".None";
        }
        return string;
    }

    private static boolean isFormulaUsed(Element element) {
        String string = element.getAttributeValue("key");
        return !string.endsWith(".None");
    }

    private static Element getDependentParamFormula(Element element, String string) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("key");
            if (string2 == null || !string2.contains(string)) continue;
            return element2.getChild("Formula");
        }
        return null;
    }
}

