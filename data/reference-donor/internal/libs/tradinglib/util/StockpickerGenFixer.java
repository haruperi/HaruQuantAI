/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.util;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.simulator.Engines;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockpickerGenFixer {
    public static final Logger Log = LoggerFactory.getLogger((String)"StockpickerGenFixer");

    public static void fixEntryExitTriggers(IRandomGenerator iRandomGenerator, Element element, int n, int n2) throws Exception {
        element.setAttribute("entryTriggeredAt", StockpickerGenFixer.translateEntryExitType(iRandomGenerator, n));
        element.setAttribute("exitTriggeredAt", StockpickerGenFixer.translateEntryExitType(iRandomGenerator, n2));
    }

    private static String translateEntryExitType(IRandomGenerator iRandomGenerator, int n) throws Exception {
        if (n == 0) {
            switch (iRandomGenerator.nextInt(3)) {
                case 1: {
                    n = 15;
                    break;
                }
                case 2: {
                    n = 5;
                    break;
                }
                default: {
                    n = 10;
                }
            }
        }
        switch (n) {
            case 15: {
                return "BeforeBarOpen";
            }
            case 5: {
                return "OnBarOpen";
            }
            case 10: {
                return "OnBarClose";
            }
        }
        throw new Exception("Unknown order type: " + n);
    }

    public static void fixExits(IRandomGenerator iRandomGenerator, Element element, int n, int n2) throws Exception {
        int n3 = StockpickerGenFixer.getProbabilityFromAttribute(element, "probabilityExitRule", 0);
        int n4 = StockpickerGenFixer.getProbabilityFromAttribute(element, "probabilityEODRule", 0);
        ArrayList arrayList = new ArrayList();
        XMLUtil.findAll((Element)element, (String)"Exit", arrayList);
        if (arrayList.size() > 0) {
            for (Element element2 : arrayList) {
                String string = element2.getParentElement().getAttributeValue("name");
                int n5 = string.equalsIgnoreCase("long") ? n : n2;
                String string2 = StockpickerGenFixer.translateEndOfDay(iRandomGenerator, n5, n4);
                String string3 = element2.getAttributeValue("atEndOfDay");
                if (string3 != null) {
                    element2.setAttribute("atEndOfDay", string2);
                    continue;
                }
                StockpickerGenFixer.probabilityExitRemove(iRandomGenerator, element2, n3);
            }
        }
    }

    private static String translateEndOfDay(IRandomGenerator iRandomGenerator, int n, int n2) throws Exception {
        if (n2 == 0) {
            return "None";
        }
        if (n2 < 100 && iRandomGenerator.nextInt(100) < n2) {
            return "None";
        }
        return "DayClose";
    }

    private static void probabilityExitRemove(IRandomGenerator iRandomGenerator, Element element, int n) {
        boolean bl = false;
        int n2 = -1;
        if (n == 0) {
            bl = true;
        } else if (n < 100 && (n2 = iRandomGenerator.nextInt(100)) < n) {
            bl = true;
        }
        if (bl && !StockpickerGenFixer.wasGenerated(element)) {
            bl = false;
        }
        if (bl) {
            element.removeContent();
        }
    }

    private static boolean wasGenerated(Element element) {
        boolean bl = false;
        List list = element.getChildren();
        for (Element element2 : list) {
            String string = element2.getAttributeValue("generated");
            if (string == null || string.equals("none")) continue;
            bl = true;
            break;
        }
        return bl;
    }

    private static int getProbabilityFromAttribute(Element element, String string, int n) {
        String string2 = element.getAttributeValue(string);
        if (string2 == null) {
            return n;
        }
        return Integer.parseInt(string2);
    }

    public static void fixMaxOpenPositions(Element element, int n, int n2) {
        if (XMLUtil.getBooleanAttr((Element)element, (String)"singleAsset", (boolean)false)) {
            n = 1;
            n2 = 1;
        }
        if (n <= 0 && n2 <= 0) {
            return;
        }
        ArrayList arrayList = new ArrayList();
        XMLUtil.findAll((Element)element, (String)"Rule", arrayList);
        block0: for (Element element2 : arrayList) {
            String string = element2.getAttributeValue("type");
            if (string == null || !string.equals("StockpickerPS")) continue;
            String string2 = element2.getAttributeValue("name");
            int n3 = string2.equalsIgnoreCase("Position Score Long") ? 1 : -1;
            ArrayList arrayList2 = new ArrayList();
            XMLUtil.findAllWithKey((Element)element2, (String)"Item", (String)"AssignVariable", arrayList2);
            for (Element element3 : arrayList2) {
                if (XMLUtil.findFirstWithKey((Element)element3, (String)"Param", (String)"#MaxOpenPositions#") == null) continue;
                Element element4 = XMLUtil.findFirstWithKey((Element)element3, (String)"Param", (String)"#Value#");
                if (element4 == null) continue block0;
                if (n3 == 1) {
                    element4.setText(Integer.toString(n));
                    continue block0;
                }
                element4.setText(Integer.toString(n2));
                continue block0;
            }
        }
    }

    public static int recognizeEngine(Element element) {
        Element element2 = element.getChild("Strategy");
        String string = element2.getAttributeValue("engine");
        return Engines.getEngine(string);
    }
}

