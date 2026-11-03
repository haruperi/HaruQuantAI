/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.RandomPlaceholder;
import java.io.File;
import java.io.IOException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlocksConfig
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"BlocksConfig");
    private static BlocksConfig config = null;
    private static Element elConfig = null;
    private HashMap<String, Element> parameterSets = new HashMap();
    private HashMap<String, BlockDefinition> blocks = new HashMap();
    private HashMap<String, BlockDefinition> formulas = new HashMap();

    public static synchronized BlocksConfig getConfig() throws JDOMException, IOException, Exception {
        if (config == null) {
            BlocksConfig.getConfigElement();
            config = new BlocksConfig(elConfig);
        }
        return config;
    }

    public static synchronized Element getConfigElement() throws Exception {
        if (elConfig == null) {
            elConfig = BlocksConfig.loadXmlConfig();
        }
        return elConfig;
    }

    private static Element loadXmlConfig() throws Exception {
        File file = new File(SQPaths.wizardConfigPath);
        String string = SQUtils.fileToString((File)file);
        Element element = XMLUtil.stringToXmlElement((String)string);
        return element;
    }

    private BlocksConfig(Element element) throws Exception {
        this.init();
    }

    private void init() throws Exception {
        this.removeHelpDisplayAttributes(elConfig);
        this.parseParameterSets(elConfig);
        this.parseBlocks(elConfig);
        this.parseFormulas(elConfig);
    }

    private void removeHelpDisplayAttributes(Element element) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            element2.removeAttribute("help");
            this.removeHelpDisplayAttributes(element2);
        }
    }

    private void parseParameterSets(Element element) {
        for (Element element2 : element.getChild("ParameterSets").getChildren()) {
            this.parameterSets.put(element2.getAttributeValue("name"), element2);
        }
    }

    private void parseBlocks(Element element) throws Exception {
        for (Element element2 : element.getChild("Blocks").getChildren()) {
            for (Element element3 : element2.getChildren()) {
                for (Element element4 : element3.getChildren()) {
                    String string = element4.getAttributeValue("key");
                    String string2 = element4.getAttributeValue("categoryType");
                    if (string2 != null && string2.equals("randomBlock")) continue;
                    String string3 = element4.getAttributeValue("ParameterSet");
                    Element element5 = string3 != null ? this.getParameterSet(string3) : element4;
                    this.blocks.put(string, new BlockDefinition(element4, element5, element2.getName()));
                }
            }
        }
    }

    private Element getParameterSet(String string) throws Exception {
        if (string.contains(string)) {
            return this.parameterSets.get(string);
        }
        throw new Exception(L.t((String)"Parameter set '%s' doesn't exist!", (Object[])new Object[]{string}));
    }

    public BlockDefinition getBlock(String string) {
        if (string.startsWith("CBlock_")) {
            return CustomBlocks.getBlock(string);
        }
        return this.blocks.get(string);
    }

    public static ArrayList<RandomPlaceholder> getPlaceholders(String string) throws Exception {
        ArrayList<RandomPlaceholder> arrayList = new ArrayList<RandomPlaceholder>();
        Element element = XMLUtil.fileToXmlElement((File)new File(string));
        BlocksConfig.recursiveGetPlaceholders(arrayList, element);
        return arrayList;
    }

    public static void recursiveGetPlaceholders(ArrayList<RandomPlaceholder> arrayList, Element element) throws Exception {
        Log.debug("Checking tag :" + element.getName());
        ArrayList arrayList2 = XMLUtil.getNestedElements((Element)element, (String)"Item");
        block14: for (int i = 0; i < arrayList2.size(); ++i) {
            Element element2 = (Element)arrayList2.get(i);
            String string = element2.getAttributeValue("generate");
            if (string == null) continue;
            String string2 = element2.getAttributeValue("superType");
            if (string2 == null) {
                throw new Exception(L.t((String)"Item '%s' has randomTemplate=true, but it is missing attribute superType!", (Object[])new Object[]{element2.getAttributeValue("key")}));
            }
            Log.debug("FOUND PLACEHOLDER " + string2);
            switch (string2) {
                case "condition": {
                    arrayList.add(new RandomPlaceholder(BlocksConfig.getIdentification(element2), 3, 3, string));
                    continue block14;
                }
                case "comparison": {
                    arrayList.add(new RandomPlaceholder(BlocksConfig.getIdentification(element2), 2, 3, string));
                    continue block14;
                }
                case "property": {
                    arrayList.add(new RandomPlaceholder(BlocksConfig.getIdentification(element2), 1, 3, string));
                    continue block14;
                }
                case "value": {
                    arrayList.add(new RandomPlaceholder(BlocksConfig.getIdentification(element2), 4, 6, string));
                    continue block14;
                }
                case "action": {
                    arrayList.add(new RandomPlaceholder(BlocksConfig.getIdentification(element2), 5, 4, string));
                }
            }
        }
    }

    private static String getIdentification(Element element) throws Exception {
        Element element2 = element.getChild("Param");
        if (element2 == null) {
            throw new Exception(L.t((String)"Random placeholder doesn't contain identification parameter!", (Object[])new Object[0]));
        }
        if (element2.getAttributeValue("controlType") != null && element2.getAttributeValue("controlType").startsWith("randomId")) {
            return element2.getValue();
        }
        throw new Exception(L.t((String)"Random placeholder doesn't contain parameter randomId!", (Object[])new Object[0]));
    }

    public BlockDefinition getFormula(String string) {
        return this.formulas.get(string);
    }

    private void parseFormulas(Element element) throws Exception {
        for (Element element2 : element.getChild("Global").getChild("Formulas").getChildren()) {
            for (Element element3 : element2.getChildren()) {
                String string = element3.getAttributeValue("key");
                String string2 = element3.getAttributeValue("ParameterSet");
                Element element4 = string2 != null ? this.getParameterSet(string2) : element3;
                this.formulas.put(string, new BlockDefinition(element3, element4, "formula"));
            }
        }
    }

    public void reload() {
        try {
            BlocksConfig blocksConfig = BlocksConfig.getConfig();
            blocksConfig.parameterSets = new HashMap();
            blocksConfig.blocks = new HashMap();
            blocksConfig.formulas = new HashMap();
            elConfig = BlocksConfig.loadXmlConfig();
            this.init();
        }
        catch (Exception exception) {
            Log.error("Errow while reloading BlocksConfig." + exception.getMessage(), (Throwable)exception);
        }
    }
}

