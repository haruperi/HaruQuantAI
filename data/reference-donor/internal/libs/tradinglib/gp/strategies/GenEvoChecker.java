/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.XMLUtil;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GenEvoChecker {
    public static final Logger Log = LoggerFactory.getLogger((String)"GenEvoChecker");

    public static Element fixZeroPeriodsAndExits(Element element) {
        if (element == null) {
            return null;
        }
        List list = element.getChildren();
        if (list == null || list.isEmpty()) {
            return element;
        }
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Param")) {
                string = element2.getAttributeValue("key");
                if (string != null && string.equals("#Period#") && !GenEvoChecker.verifyParam(element2)) {
                    return null;
                }
            } else if (element2.getName().equals("Formula")) {
                string = element2.getAttributeValue("key");
                if (string.equals("SQ.Formulas.SLPT.FixedValue")) {
                    if (!GenEvoChecker.verifyFormulaParam(element2, "#Value#")) {
                        return null;
                    }
                } else if (string.equals("SQ.Formulas.SLPT.ATRBasedValue")) {
                    if (!GenEvoChecker.verifyFormulaParam(element2, "#Value#")) {
                        return null;
                    }
                    if (!GenEvoChecker.verifyFormulaParam(element2, "#AtrPeriod#")) {
                        return null;
                    }
                }
            }
            GenEvoChecker.fixZeroPeriodsAndExits(element2);
        }
        return element;
    }

    private static boolean verifyFormulaParam(Element element, String string) {
        Element element2 = XMLUtil.getItemParameterNoException((Element)element, (String)string);
        if (element2 != null) {
            return GenEvoChecker.verifyParam(element2);
        }
        return true;
    }

    private static boolean verifyParam(Element element) {
        String string;
        String string2 = element.getAttributeValue("variable");
        if (!(string2 != null && string2.equals("true") || (string = element.getText()) == null || string.isBlank())) {
            try {
                double d = Double.parseDouble(string);
                if (d == 0.0) {
                    return false;
                }
            }
            catch (NumberFormatException numberFormatException) {
                return true;
            }
        }
        return true;
    }

    public static boolean passedRRRCheck(Element element, boolean bl, double d, double d2) {
        double d3;
        if (!bl) {
            return true;
        }
        Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#StopLoss.StopLoss#");
        if (element2 == null) {
            return true;
        }
        Element element3 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#ProfitTarget.ProfitTarget#");
        if (element3 == null) {
            return true;
        }
        Element element4 = element2.getChild("Formula");
        if (element4 == null) {
            return true;
        }
        String string = element4.getAttributeValue("key");
        Element element5 = element3.getChild("Formula");
        if (element5 == null) {
            return true;
        }
        String string2 = element4.getAttributeValue("key");
        if (!string.equals(string2)) {
            return true;
        }
        Element element6 = XMLUtil.findFirstWithKey((Element)element4, (String)"Param", (String)"#Value#");
        if (element6 == null) {
            return true;
        }
        Element element7 = XMLUtil.findFirstWithKey((Element)element5, (String)"Param", (String)"#Value#");
        if (element7 == null) {
            return true;
        }
        double d4 = GenEvoChecker.parseSLPTValue(element6.getText());
        double d5 = d4 / (d3 = GenEvoChecker.parseSLPTValue(element7.getText()));
        return !(d5 < d) && !(d5 > d2);
    }

    public static boolean passedRRRCheck2(Element element, boolean bl, double d, double d2) {
        double d3;
        if (!bl) {
            return true;
        }
        Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#StopLoss.StopLoss#");
        if (element2 == null) {
            return true;
        }
        Element element3 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#ProfitTarget.ProfitTarget#");
        if (element3 == null) {
            return true;
        }
        Element element4 = element2.getChild("Formula");
        if (element4 == null) {
            return true;
        }
        String string = element4.getAttributeValue("key");
        Element element5 = element3.getChild("Formula");
        if (element5 == null) {
            return true;
        }
        String string2 = element4.getAttributeValue("key");
        if (!string.equals(string2)) {
            return true;
        }
        Element element6 = XMLUtil.findFirstWithKey((Element)element4, (String)"Param", (String)"#Value#");
        if (element6 == null) {
            return true;
        }
        Element element7 = XMLUtil.findFirstWithKey((Element)element5, (String)"Param", (String)"#Value#");
        if (element7 == null) {
            return true;
        }
        double d4 = GenEvoChecker.parseSLPTValue(element6.getText());
        double d5 = d4 / (d3 = GenEvoChecker.parseSLPTValue(element7.getText()));
        if (d5 < d || d5 > d2) {
            Log.info("RRR mutation bad detected {} (limit {})= {} / {}", new Object[]{d5, d, d4, d3});
            return false;
        }
        return true;
    }

    private static double parseSLPTValue(String string) {
        try {
            return Double.parseDouble(string);
        }
        catch (Exception exception) {
            return 0.0;
        }
    }
}

