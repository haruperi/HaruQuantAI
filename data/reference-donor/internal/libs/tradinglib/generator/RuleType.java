/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.generator;

import org.jdom2.Element;

public class RuleType {
    public static final int Unknown = 0;
    public static final int Entry = 1;
    public static final int Exit = 2;

    public static boolean isConditionElement(String string) {
        return string.equals("If");
    }

    public static boolean isActionElement(String string) {
        return string.equals("Then");
    }

    public static int recognizeRuleTypeFromParents(Element element) {
        int n = 0;
        ++n;
        Element element2 = element.getParentElement();
        if (element2 == null) {
            return 0;
        }
        String string = element2.getName();
        if (string.equals("signal")) {
            return RuleType.recognizeTypeFromSignal(element2);
        }
        if (string.equals("Rule")) {
            return RuleType.recognizeTypeFromRule(element2);
        }
        if (string.equals("Rules")) {
            return 0;
        }
        if (n > 20) {
            return 0;
        }
        return RuleType.recognizeRuleTypeFromParents(element2);
    }

    private static int recognizeTypeFromRule(Element element) {
        String string = element.getAttributeValue("name");
        if (string == null) {
            return 0;
        }
        if ((string = string.toLowerCase()).contains("entry")) {
            return 1;
        }
        if (string.contains("exit")) {
            return 2;
        }
        return 0;
    }

    private static int recognizeTypeFromSignal(Element element) {
        String string = element.getAttributeValue("variable");
        if (string == null) {
            return 0;
        }
        switch (string) {
            case "33333333-1111-1111-3333-333333333333": 
            case "33333333-2222-1111-3333-333333333333": {
                return 1;
            }
            case "33333333-1111-2222-3333-333333333333": 
            case "33333333-2222-2222-3333-333333333333": {
                return 2;
            }
        }
        return 0;
    }
}

