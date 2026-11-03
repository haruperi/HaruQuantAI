/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.generator.StrategyStockpickerTemplate;
import java.io.File;
import java.io.IOException;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyStockpickerSingleAssetTemplate
extends StrategyStockpickerTemplate {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyStockpickerTemplate");

    public StrategyStockpickerSingleAssetTemplate(Element element, IRandomGenerator iRandomGenerator) {
        super(element, iRandomGenerator);
    }

    @Override
    protected void addRules(Element element) throws Exception {
        this.addRules(element, "entryexitrule.xml");
        this.addPositionScoreRule(element, "positionscorerulelong.xml");
        this.addPositionScoreRule(element, "positionscoreruleshort.xml");
    }

    private void addPositionScoreRule(Element element, String string) throws JDOMException, IOException, Exception {
        Element element2 = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/ctemplate/build/sp/" + string)).detach();
        element.addContent((Content)element2);
    }

    @Override
    public Element generate() throws Exception {
        Element element = super.generate();
        Element element2 = element.getChild("Strategy");
        element2.setAttribute("singleAsset", "true");
        this.setExitsProbability(element);
        return element;
    }
}

