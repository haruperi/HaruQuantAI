/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.generator;

import org.jdom2.Element;

public class RulePart {
    public static final int Unknown = 1;
    public static final int Condition = 2;
    public static final int Action = 3;

    public static boolean isConditionElement(String string) {
        return string.equals("If");
    }

    public static boolean isActionElement(String string) {
        return string.equals("Then");
    }

    public static int recognizeRulePartFromParents(Element element) {
        Element element2 = element.getParentElement();
        if (element2 == null) {
            return 1;
        }
        if (RulePart.isConditionElement(element2.getName())) {
            return 2;
        }
        if (RulePart.isActionElement(element2.getName())) {
            return 3;
        }
        return RulePart.recognizeRulePartFromParents(element2);
    }
}

