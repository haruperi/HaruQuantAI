/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Attribute
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.indicator.IndicatorBase;
import java.lang.reflect.Field;
import org.jdom2.Attribute;

public class IndicatorDisplayFormatter {
    public static String format(IndicatorBase indicatorBase, BlockDefinition blockDefinition) {
        int n;
        Object object;
        Field[] fieldArray;
        Attribute attribute = blockDefinition.getXml().getAttribute("display");
        if (attribute == null) {
            return blockDefinition.getName();
        }
        String string = attribute.getValue();
        Field[] fieldArray2 = fieldArray = indicatorBase.getClass().getDeclaredFields();
        int n2 = fieldArray2.length;
        for (int i = 0; i < n2; ++i) {
            object = fieldArray2[i];
            try {
                Object object2 = ((Field)object).get(indicatorBase);
                String string2 = object2 == null ? "" : object2.toString();
                String string3 = "#" + ((Field)object).getName() + "#";
                string = string.replace(string3, string2);
                continue;
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        while ((n = string.indexOf("#")) != -1 && (n2 = string.indexOf("#", n + 1)) != -1) {
            String string4 = string.substring(0, n);
            object = n2 > string.length() ? "" : string.substring(n2 + 1);
            string = string4 + (String)object;
        }
        return string.replace(".[]", "").replace("[]", "");
    }
}

