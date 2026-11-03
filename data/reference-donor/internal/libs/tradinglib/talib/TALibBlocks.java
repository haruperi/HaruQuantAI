/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Attribute
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.BlockDefinitionException;
import java.io.File;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TALibBlocks {
    public static final Logger Log = LoggerFactory.getLogger((String)"TALibBlocks");
    private static TALibBlocks instance;
    private HashMap<String, Element> talibBlocks = new HashMap();

    public static void init() throws Exception {
        if (instance != null) {
            throw new Exception("TALibBlocks.init() called more than once!");
        }
        instance = new TALibBlocks();
    }

    private TALibBlocks() throws Exception {
        String string = MainApp.getDataPath() + "internal/web/SQWIZARD/branding/global/config.xml";
        File file = new File(string);
        Element element = XMLUtil.fileToXmlElement((File)file);
        Element element2 = element.getChild("Blocks");
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            List list2 = element3.getChildren();
            for (int j = 0; j < list2.size(); ++j) {
                Element element4 = (Element)list2.get(j);
                List list3 = element4.getChildren();
                for (int k = 0; k < list3.size(); ++k) {
                    Element element5 = (Element)list3.get(k);
                    String string2 = element5.getAttributeValue("key");
                    if (!string2.startsWith("talib")) continue;
                    element5 = this.removeParamCategory(element5);
                    this.talibBlocks.put(string2, element5);
                }
            }
        }
        Log.debug("Loading TALib blocks finished");
    }

    private Element removeParamCategory(Element element) {
        Element element2 = element.getChild("paramCategory");
        element2.detach();
        List list = element2.getChildren();
        List list2 = element2.getAttributes();
        for (Attribute attribute : list2) {
            element2.removeAttribute(attribute);
        }
        list2 = element.getAttributes();
        for (Attribute attribute : list2) {
            element2.setAttribute(attribute.getName(), attribute.getValue());
        }
        element2.setName("Item");
        return element2;
    }

    public static Element getBlock(String string) throws BlockDefinitionException {
        return instance._getBlock(string);
    }

    private Element _getBlock(String string) throws BlockDefinitionException {
        if (this.talibBlocks.containsKey(string)) {
            return this.talibBlocks.get(string);
        }
        throw new BlockDefinitionException("Cannot find TALib block '" + string + "'");
    }
}

