/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.SQUtils;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.List;
import org.jdom2.Element;

public class ItemRandomValueRanges {
    private Int2ObjectOpenHashMap<String> map;

    public static ItemRandomValueRanges getRandomValueRanges(Element element) {
        List list = element.getChildren("Param");
        ItemRandomValueRanges itemRandomValueRanges = null;
        for (int i = 0; i < list.size(); ++i) {
            String string;
            String string2;
            Element element2 = (Element)list.get(i);
            String string3 = element2.getAttributeValue("generate");
            if (string3 == null || !string3.equals("random")) continue;
            if (element.getAttributeValue("key").equals("Number") && element2.getAttributeValue("key").equals("#Number#")) {
                string2 = element2.getText();
                string = element2.getAttributeValue("randomValue");
                if (string2.contains(":") && !string.contains(":")) {
                    string = string2;
                }
            } else {
                string = element2.getAttributeValue("randomValue");
            }
            if (string == null || string.equals("") || string.equals("default")) continue;
            string2 = element2.getAttributeValue("key");
            if (itemRandomValueRanges == null) {
                itemRandomValueRanges = new ItemRandomValueRanges();
            }
            itemRandomValueRanges.add(string2, string);
        }
        return itemRandomValueRanges;
    }

    private void add(String string, String string2) {
        if (this.map == null) {
            this.map = new Int2ObjectOpenHashMap();
        }
        this.map.put(SQUtils.betterHashCode((String)string), (Object)string2);
    }

    public String getForParam(String string) {
        if (this.map == null) {
            return null;
        }
        return (String)this.map.get(SQUtils.betterHashCode((String)string));
    }
}

