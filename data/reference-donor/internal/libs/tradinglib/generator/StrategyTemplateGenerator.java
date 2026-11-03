/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.Namespace
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.IStrategyTemplate;
import com.strategyquant.tradinglib.generator.StrategyImproveTemplateSQ3;
import com.strategyquant.tradinglib.generator.StrategyImproveTemplateSQ4;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ3;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4;
import com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4Fuzzy;
import com.strategyquant.tradinglib.generator.StrategyStockpickerSingleAssetTemplate;
import com.strategyquant.tradinglib.generator.StrategyStockpickerTemplate;
import com.strategyquant.tradinglib.generator.StrategyTemplateNotFoundException;
import com.strategyquant.tradinglib.simulator.Engines;
import java.io.File;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.Namespace;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyTemplateGenerator {
    private static final Logger Log = LoggerFactory.getLogger((String)"StrategyTemplateGenerator");
    private String strategyType;
    private String taskName;
    private int engine;
    private Element elSettings;
    private IRandomGenerator rng;
    private boolean useSameIdForLongShort = true;
    private String architecture;

    public StrategyTemplateGenerator(String string, Element element, IRandomGenerator iRandomGenerator) throws GenerateException {
        this.taskName = string;
        this.elSettings = element;
        this.rng = iRandomGenerator;
        Element element2 = element.getChild("WhatToBuild");
        this.engine = StrategyTemplateGenerator.getEngine(element);
        this.strategyType = element2.getChild("StrategyType").getAttributeValue("type");
        this.architecture = element2.getChild("StrategyType").getAttributeValue("architecture");
        if (this.architecture == null) {
            this.architecture = "sq4";
        }
    }

    public static int getEngine(Element element) {
        Element element2 = element.getChild("Data");
        String string = element2.getChild("Setups").getChild("Setup").getAttributeValue("engine");
        return Engines.getEngine(string);
    }

    public Element generate() throws Exception {
        IStrategyTemplate iStrategyTemplate = null;
        if (this.strategyType.equals("multi-tf") || this.strategyType.equals("simple")) {
            if (this.engine == 1316847364) {
                iStrategyTemplate = new StrategyStockpickerTemplate(this.elSettings, this.rng);
            } else if (this.engine == -1816889229) {
                iStrategyTemplate = new StrategyStockpickerSingleAssetTemplate(this.elSettings, this.rng);
            } else if (this.architecture.equals("sq3")) {
                iStrategyTemplate = new StrategyStandardTemplateSQ3(this.elSettings, this.rng);
            } else if (this.architecture.equals("sq4")) {
                iStrategyTemplate = new StrategyStandardTemplateSQ4(this.elSettings, this.rng);
            } else if (this.architecture.equals("sq4fuzzy")) {
                iStrategyTemplate = new StrategyStandardTemplateSQ4Fuzzy(this.elSettings, this.rng);
            }
        } else if (this.strategyType.equals("improve")) {
            if (this.engine == 1316847364 || this.engine == -1816889229) {
                throw new Exception(String.format("Improver is not yet implemented for Stockpicker strategies", new Object[0]));
            }
            this.architecture = this.recognizeArchitectureFromStrategy();
            if (this.architecture != null) {
                if (this.architecture.equals("sq3")) {
                    iStrategyTemplate = new StrategyImproveTemplateSQ3(this.elSettings, this.rng);
                } else if (this.architecture.equals("sq4")) {
                    iStrategyTemplate = new StrategyImproveTemplateSQ4(this.elSettings, this.rng);
                } else if (this.architecture.equals("sq4fuzzy")) {
                    iStrategyTemplate = new StrategyImproveTemplateSQ4(this.elSettings, this.rng);
                }
            }
        } else if (this.strategyType.equals("template")) {
            Element element = StrategyTemplateGenerator.getConfiguredTemplate(this.elSettings, this.taskName);
            if (this.engine == 1316847364 || this.engine == -1816889229) {
                StrategyStockpickerTemplate.setExitsProbability(element, this.elSettings, this.rng);
            }
            this.fixXmlns(element);
            this.fixCharts(this.elSettings, element);
            this.fixRandomGroups(element);
            this.fixGeneratedBlocks(element);
            return element;
        }
        if (iStrategyTemplate == null) {
            throw new Exception(String.format("Unrecognized Strategy Type '%s' and architecture '%s'", this.strategyType, this.architecture));
        }
        iStrategyTemplate.setUseSameIdForLongShort(this.useSameIdForLongShort);
        Element element = iStrategyTemplate.generate();
        this.saveEngine(element);
        return element;
    }

    private void fixGeneratedBlocks(Element element) {
        element.setNamespace(Namespace.NO_NAMESPACE);
        String string = element.getAttributeValue("generated");
        if (string != null) {
            element.removeAttribute("generated");
            element.removeAttribute("randomId");
        }
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            this.fixGeneratedBlocks((Element)list.get(i));
        }
    }

    private void saveEngine(Element element) {
        Element element2 = element.getChild("Strategy");
        element2.setAttribute("engine", Engines.getEngineName(this.engine));
    }

    private void fixCharts(Element element, Element element2) throws Exception {
        List list = ((Element)element.getChild("Data").getChild("Setups").getChildren("Setup").get(0)).getChildren("Chart");
        Element element3 = element2.getChild("Strategy").getChild("Datas");
        if (element3.getChildren().size() > list.size()) {
            throw new Exception(L.t((String)"Strategy from template file requires %d charts, %d defined.", (Object[])new Object[]{element3.getChildren().size(), list.size()}));
        }
        element3.removeContent();
        String string = null;
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            Element element5 = new Element("data");
            element5.addContent((Content)new Element("id").setText(Integer.toString(i)));
            if (i == 0) {
                element5.addContent((Content)new Element("chart").setText("Main chart"));
                string = element4.getAttributeValue("symbol");
                element5.addContent((Content)new Element("symbol").setText("NULL"));
                element5.addContent((Content)new Element("timeFrame").setText("0"));
            } else {
                element5.addContent((Content)new Element("chart").setText(String.format("Subchart %d", i)));
                if (element4.getAttributeValue("symbol").equals(string)) {
                    element5.addContent((Content)new Element("symbol").setText("NULL"));
                } else {
                    element5.addContent((Content)new Element("symbol").setText(element4.getAttributeValue("symbol")));
                }
                element5.addContent((Content)new Element("timeFrame").setText(StrategyStandardTemplateSQ3.convertTimeframeToWizard(element4.getAttributeValue("timeframe"))));
            }
            element3.addContent((Content)element5);
        }
    }

    private void fixXmlns(Element element) {
        element.setNamespace(Namespace.NO_NAMESPACE);
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            this.fixXmlns((Element)list.get(i));
        }
    }

    private void fixRandomGroups(Element element) {
        Element element2 = element.getChild("Strategy").getChild("RandomGroups");
        if (element2 == null) {
            return;
        }
        List list = element2.getChildren("Group");
        for (int i = 0; i < list.size(); ++i) {
            this.fixRG((Element)list.get(i));
        }
    }

    private void fixRG(Element element) {
        Object object;
        block4: {
            String string;
            block3: {
                RandomValueConfig randomValueConfig;
                string = element.getName();
                if (!string.equals("Param")) break block3;
                element.removeAttribute("identification");
                object = element.getAttributeValue("randomValue");
                if (object == null || ((String)object).equals("default") || (randomValueConfig = RandomValueConfig.parseRandomValue((String)object, true)) != null) break block4;
                Log.info("Template fix - randomValue attribute has incorrect format: '{}', setting to default", object);
                element.setAttribute("randomValue", "default");
                break block4;
            }
            if (string.equals("Item")) {
                object = element.getChildren("Param");
                for (int i = 0; i < object.size(); ++i) {
                    Element element2 = (Element)object.get(i);
                    String string2 = element2.getAttributeValue("key");
                    if (!string2.equals("#Identification#")) continue;
                    element.removeContent((Content)element2);
                    break;
                }
            }
        }
        object = element.getChildren();
        for (int i = 0; i < object.size(); ++i) {
            this.fixRG((Element)object.get(i));
        }
    }

    private String recognizeArchitectureFromStrategy() throws Exception {
        Object object;
        IProgram iProgram;
        Element element;
        Element element2 = this.elSettings.getChild("WhatToBuild");
        String string = element2.getChild("StrategyType").getAttributeValue("strategyFile");
        if (!string.contains("/") && !string.contains("\\")) {
            string = MainApp.getDataPath() + "user/strategies/" + string;
        }
        Log.info("Load strategy file {}", (Object)string);
        File file = new File(string);
        if (!file.exists()) {
            throw new Exception(String.format("Improver - Strategy '%s' doesn't exist!", string));
        }
        if (string.endsWith(".xml")) {
            element = XMLUtil.fileToXmlElement((File)file);
        } else {
            iProgram = Program.get((String)"Loader");
            object = (ResultsGroup)iProgram.call("loadFile", new Object[]{string, false});
            element = ((ResultsGroup)object).getStrategyXml();
        }
        if (element == null) {
            throw new Exception(String.format("Improver - No strategy found in file '%s' !", string));
        }
        iProgram = element.getChild("Strategy");
        object = iProgram.getChild("Rules").getChild("Events").getChildren();
        for (int i = 0; i < object.size(); ++i) {
            if (!((Element)object.get(i)).getAttributeValue("key").equals("OnBarUpdate")) continue;
            List list = ((Element)object.get(i)).getChildren("Rule");
            if (list.size() < 1) break;
            Element element3 = (Element)list.get(0);
            if (element3.getAttributeValue("type").equals("Signal")) {
                return "sq4";
            }
            if (element3.getAttributeValue("type").equals("SignalFuzzy")) {
                return "sq4fuzzy";
            }
            return "sq3";
        }
        return null;
    }

    public static Element getConfiguredTemplate(Element element, String string) throws Exception {
        Element element2;
        Element element3 = element.getChild("WhatToBuild").getChild("StrategyType");
        String string2 = element3.getAttributeValue("type");
        if (!string2.equals("template")) {
            return null;
        }
        String string3 = element3.getAttributeValue("templateFile");
        if (string3 == null) {
            throw new Exception("No template file specified!");
        }
        File file = new File(string3);
        if (!file.exists()) {
            file = new File(MainApp.getDataPath() + "user/settings/StrategyTemplates/" + string3);
            if (file.exists()) {
                string3 = MainApp.getDataPath() + "user/settings/StrategyTemplates/" + string3;
            } else {
                throw new StrategyTemplateNotFoundException(string3, string);
            }
        }
        try {
            if (!string3.endsWith(".sqw")) {
                if (string3.endsWith(".sq4") || string3.endsWith(".sqx")) {
                    IProgram iProgram = Program.get((String)"Loader");
                    ResultsGroup resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{string3});
                    Element element4 = resultsGroup.getStrategyXml();
                    if (element4 == null) {
                        throw new Exception(String.format("Template file doesn't contain strategy!", new Object[0]));
                    }
                    return element4;
                }
                throw new Exception(String.format("Incorrect template file, only .sqx files can be used as templates!", new Object[0]));
            }
            element2 = XMLUtil.fileToXmlElement((File)file);
        }
        catch (Exception exception) {
            throw new Exception(String.format("Template file '%s' cannot be loaded. Error: %s!", string3, exception.getMessage()));
        }
        return element2;
    }

    public void setUseSameIdForLongShort(boolean bl) {
        this.useSameIdForLongShort = bl;
    }

    public static void addTickSizeToDataElem(Element element, String string, String string2) {
        double d = -1.0;
        DataInfo dataInfo = null;
        try {
            dataInfo = !string.equals("Same as main chart") ? DataManager.getDataInfo((String)"History", (String)string) : DataManager.getDataInfo((String)"History", (String)string2);
            if (dataInfo == null) {
                Log.info("Cannot get data decimals of unknown symbol '" + string + "'");
            } else {
                d = dataInfo.symbolInfo.tickSize;
            }
        }
        catch (Exception exception) {
            Log.error("Cannot get data decimals of symbol '" + string + "'");
        }
        Element element2 = XMLUtil.tryAddElement((Element)element, (String)"ticksize");
        element2.setText(String.valueOf(d));
    }
}

