/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.task.settings.blocks;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.generator.BlockSettingsConverter;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import java.io.File;
import java.io.IOException;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConfigConverter {
    public static final Logger Log = LoggerFactory.getLogger((String)"ConfigConverter");
    private String taskName;

    public ConfigConverter(String string) {
        this.taskName = string;
    }

    public Element convertSimpleBuildingBlocks(Element element, IRandomGenerator iRandomGenerator) throws JDOMException, IOException, Exception {
        Element element2 = new Element("Settings");
        Element element3 = null;
        for (Element element4 : element.getChildren()) {
            if (!element4.getName().equals("Blocks")) {
                element2.addContent((Content)element4.clone());
                continue;
            }
            element3 = element4;
        }
        if (element3 == null) {
            throw new Exception(L.t((String)"Builder project config doesn't contain Blocks element.", (Object[])new Object[0]));
        }
        element = element.clone();
        XMLUtil.xmlToFile((Element)element, (File)new File(MainApp.getDataPath() + "tests/tmp/simpleBuilderConfig.xml"));
        Element element5 = this.getCorrectStrategyTemplate(element, iRandomGenerator);
        element2.addContent((Content)element5);
        XMLUtil.xmlToFile((Element)element5, (File)new File(MainApp.getDataPath() + "tests/tmp/StrTemplateBefore.xml"));
        element2.addContent((Content)this.convertToFullFormat(element, element5));
        this.deleteRandomGroupsElement(element2);
        XMLUtil.xmlToFile((Element)element2, (File)new File(MainApp.getDataPath() + "tests/tmp/fullBuilderConfig.xml"));
        return element2;
    }

    private void deleteRandomGroupsElement(Element element) {
        Element element2 = element.getChild("StrategyFile").getChild("Strategy");
        element2.removeChild("RandomGroups");
    }

    private Element getCorrectStrategyTemplate(Element element, IRandomGenerator iRandomGenerator) throws Exception {
        StrategyTemplateGenerator strategyTemplateGenerator = new StrategyTemplateGenerator(this.taskName, element, iRandomGenerator);
        return strategyTemplateGenerator.generate().detach();
    }

    private Element convertToFullFormat(Element element, Element element2) throws Exception {
        BlockSettingsConverter blockSettingsConverter = new BlockSettingsConverter(element.clone(), element2);
        Element element3 = blockSettingsConverter.convert();
        this.fixIchimokuChikouSpan(element3);
        BlocksConfig blocksConfig = BlocksConfig.getConfig();
        this.fixSPParamIssues(element3, blocksConfig);
        return element3;
    }

    private void fixSPParamIssues(Element element, BlocksConfig blocksConfig) {
        Object object;
        List list = element.getChildren();
        if (list != null && list.size() > 0) {
            for (int i = 0; i < list.size(); ++i) {
                object = (Element)list.get(i);
                this.fixSPParamIssues((Element)object, blocksConfig);
            }
        }
        if (element.getName().equals("Block")) {
            String string = element.getAttributeValue("key");
            if (string == null || !string.startsWith("talib_")) {
                return;
            }
            object = blocksConfig.getBlock(string);
            if (object == null) {
                return;
            }
            this.fixSPParamIssuesOnItemParams(element, (BlockDefinition)object);
        }
    }

    private void fixSPParamIssuesOnItemParams(Element element, BlockDefinition blockDefinition) {
        String string;
        List list = element.getChildren();
        if (list != null && list.size() > 0) {
            for (int i = 0; i < list.size(); ++i) {
                string = (Element)list.get(i);
                this.fixSPParamIssuesOnItemParams((Element)string, blockDefinition);
            }
        }
        if (element.getName().equals("Param")) {
            Element element2 = element;
            string = element2.getAttributeValue("key");
            if (string == null) {
                return;
            }
            BlockParameter blockParameter = blockDefinition.getParamByKey(string);
            if (blockParameter == null) {
                return;
            }
            if (blockParameter.paramType != null && blockParameter.paramType.equals("period")) {
                String string2 = element2.getAttributeValue("minValue");
                if (string2 == null) {
                    return;
                }
                double d = Double.parseDouble(string2);
                if (d >= 0.0 && d < 2.0) {
                    if (Log.isDebugEnabled()) {
                        Log.debug("Corrected min period value from {} to 2, param: {}", (Object)string2, (Object)XMLUtil.elementToString((Element)element2));
                    }
                    element2.setAttribute("minValue", "2");
                }
            }
        }
    }

    private void fixIchimokuChikouSpan(Element element) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            if (element2.getName().equals("Param") && (string = element2.getAttributeValue("values")) != null && string.contains(",ChikouSpan=4")) {
                string = string.replace(",ChikouSpan=4", "");
                element2.setAttribute("values", string);
                continue;
            }
            this.fixIchimokuChikouSpan(element2);
        }
    }
}

