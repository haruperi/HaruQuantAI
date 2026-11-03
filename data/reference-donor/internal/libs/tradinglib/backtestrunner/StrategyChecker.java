/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtestrunner;

import com.strategyquant.lib.XMLUtil;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyChecker {
    private static final Logger Log = LoggerFactory.getLogger(StrategyChecker.class);

    public static boolean strategyValid(Element element) {
        try {
            ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Rule");
            if (arrayList.size() == 0) {
                return false;
            }
            boolean bl = false;
            block2: for (int i = 0; i < arrayList.size(); ++i) {
                List list;
                Element element2;
                Element element3 = (Element)arrayList.get(i);
                String string = element3.getAttributeValue("type");
                if (string == null || (element2 = element3.getChild("Then")) == null || (list = element2.getChildren("Item")) == null) continue;
                for (int j = 0; j < list.size(); ++j) {
                    Element element4 = (Element)list.get(j);
                    String string2 = element4.getAttributeValue("mI");
                    if (string2 == null || !string2.equals("Open")) continue;
                    bl = true;
                    continue block2;
                }
            }
            return bl;
        }
        catch (Exception exception) {
            Log.error("Strategy validation failed", (Throwable)exception);
            return false;
        }
    }
}

