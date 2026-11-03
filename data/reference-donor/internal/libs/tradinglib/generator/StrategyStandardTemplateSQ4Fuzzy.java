/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4;
import java.io.IOException;
import java.util.ArrayList;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyStandardTemplateSQ4Fuzzy
extends StrategyStandardTemplateSQ4 {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyStandardTemplateSQ4Fuzzy");
    private int minTrueEntry;
    private int minTrueExit;

    public StrategyStandardTemplateSQ4Fuzzy(Element element, IRandomGenerator iRandomGenerator) throws JDOMException, IOException, Exception {
        super(element, iRandomGenerator);
        Element element2 = element.getChild("WhatToBuild");
        int n = this.getIntAttribute(element2.getChild("StrategyType").getAttributeValue("minTrue"), 0, 100, 70);
        int n2 = this.getIntAttribute(element2.getChild("StrategyType").getAttributeValue("maxTrue"), 0, 100, 70);
        if (n > n2) {
            int n3 = n;
            n = n2;
            n2 = n3;
        }
        if (n == n2) {
            this.minTrueEntry = n;
            this.minTrueExit = n;
        } else {
            this.minTrueEntry = n + iRandomGenerator.nextInt(n2 - n);
            this.minTrueExit = n + iRandomGenerator.nextInt(n2 - n);
        }
    }

    public static void ramdomizeFuzzyPercentags(Element element, int n, int n2, IRandomGenerator iRandomGenerator) {
        int n3;
        int n4;
        if (n > n2) {
            int n5 = n;
            n = n2;
            n2 = n5;
        }
        if (n == n2) {
            n4 = n;
            n3 = n;
        } else {
            n4 = n + iRandomGenerator.nextInt(n2 - n);
            n3 = n + iRandomGenerator.nextInt(n2 - n);
        }
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"signal");
        block12: for (int i = 0; i < arrayList.size(); ++i) {
            Element element2 = (Element)arrayList.get(i);
            String string = element2.getAttributeValue("variable");
            if (string == null) continue;
            switch (string) {
                case "33333333-1111-1111-3333-333333333333": {
                    element2.setAttribute("minTrue", Integer.toString(n4));
                    continue block12;
                }
                case "33333333-2222-1111-3333-333333333333": {
                    element2.setAttribute("minTrue", Integer.toString(n4));
                    continue block12;
                }
                case "33333333-1111-2222-3333-333333333333": {
                    element2.setAttribute("minTrue", Integer.toString(n3));
                    continue block12;
                }
                case "33333333-2222-2222-3333-333333333333": {
                    element2.setAttribute("minTrue", Integer.toString(n3));
                }
            }
        }
    }

    private int getIntAttribute(String string, int n, int n2, int n3) {
        if (string == null) {
            return n3;
        }
        try {
            int n4 = Integer.parseInt(string);
            if (n4 < n) {
                n4 = n;
            }
            if (n4 > n2) {
                n4 = n2;
            }
            return n4;
        }
        catch (NumberFormatException numberFormatException) {
            return n3;
        }
    }

    @Override
    protected Element getSignalRule() throws JDOMException, IOException, Exception {
        Element element = super.getSignalRule();
        element.setAttribute("type", "SignalFuzzy");
        return element;
    }

    @Override
    protected Element getEntrySignalCondition(int n, String string, String string2) throws JDOMException, IOException, Exception {
        Element element = super.getEntrySignalCondition(n, string, string2);
        element.setAttribute("minTrue", Integer.toString(this.minTrueEntry));
        return element;
    }

    @Override
    protected Element getExitSignalCondition(int n, String string, String string2) throws JDOMException, IOException, Exception {
        Element element = super.getExitSignalCondition(n, string, string2);
        element.setAttribute("minTrue", Integer.toString(this.minTrueExit));
        return element;
    }
}

