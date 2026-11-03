/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.input.SAXBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Loader.impl.SQ3;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.plugin.Loader.impl.SQ3.SQFileLoaderSQ3Xml;
import com.strategyquant.tradinglib.ResultsGroup;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.input.SAXBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQ3FileLoaderOldXml {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQFileLoaderOldXml");

    public ResultsGroup load(String filePath, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement) throws Exception {
        File file = new File(filePath);
        SAXBuilder builder = new SAXBuilder();
        BufferedReader in = new BufferedReader(new InputStreamReader((InputStream)new FileInputStream(file), StandardCharsets.UTF_8));
        Document document = builder.build((Reader)in);
        Element rootNode = document.getRootElement();
        AbstractBroker broker = MainApp.getLicenseInfo().getBroker();
        if (broker != null) {
            broker.modifyOldStrategyXML(rootNode);
        }
        ResultsGroup strategyResults = new ResultsGroup(SQUtils.stripExtension((String)file.getName()));
        if (rootNode.getChild("Strategy") == null && rootNode.getChild("ResultsData") != null) {
            strategyResults.specialValues().setString("SourceType", "EA Analyzer 3");
        } else {
            strategyResults.specialValues().setString("SourceType", "EA StrategyQuant 3");
            SQFileLoaderSQ3Xml loader = new SQFileLoaderSQ3Xml();
            loader.load(strategyResults, rootNode, exceptionOnMissingInstrument, missingInstrumentReplacement);
        }
        return strategyResults;
    }
}

