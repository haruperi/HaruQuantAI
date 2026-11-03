/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.jdom2.input.SAXBuilder
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.formulas.Formulas;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlocksConfigGenerator {
    public static final Logger Log = LoggerFactory.getLogger(BlocksConfigGenerator.class);

    public void run(String string) throws Exception {
        Log.debug("Regenerating Wizard config.xml");
        Document document = this.generateBasicDocument();
        Blocks.generateBlocksXml(document.getRootElement());
        Formulas.generateFormulasXml(document.getRootElement().getChild("Global").getChild("Formulas"));
        Blocks.generateExitRulesXml(document.getRootElement().getChild("Global").getChild("ExitRules"));
        MoneyManagementMethodsList.generateMethodsXml(document.getRootElement().getChild("Global").getChild("MoneyManagement"));
        this.addTaLibsIndicators(document);
        XMLOutputter xMLOutputter = new XMLOutputter(Format.getPrettyFormat());
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(new FileOutputStream(string));
        xMLOutputter.output(document, (OutputStream)bufferedOutputStream);
        bufferedOutputStream.close();
        Log.debug("Wizard config.xml has been regenerated successfully");
    }

    private void addTaLibsIndicators(Document document) throws JDOMException, IOException, Exception {
        File file = new File(MainApp.getDataPath() + "internal/ctemplate/talibs.xml");
        if (file.exists()) {
            Element element = XMLUtil.fileToXmlElement((File)file).detach();
            Element element2 = element.getChild("Candles");
            Element element3 = element.getChild("Indicators");
            Element element4 = element.getChild("Functions");
            Element element5 = element.getChild("Prices");
            Element element6 = document.getRootElement().getChild("Blocks").getChild("Values");
            List list = element6.getChildren("Category");
            Element element7 = this.getCategoryElement(list, "Indicators");
            Element element8 = this.getCategoryElement(list, "Functions");
            Element element9 = this.getCategoryElement(list, "Price");
            Element element10 = document.getRootElement().getChild("Blocks").getChild("Conditions");
            List list2 = element10.getChildren("Category");
            Element element11 = this.getCategoryElement(list2, "CandlePatterns");
            this.addTalib(element7, element3.getChildren());
            this.addTalib(element8, element4.getChildren());
            this.addTalib(element11, element2.getChildren());
            this.addTalib(element9, element5.getChildren());
        }
    }

    private void addTalib(Element element, List<Element> list) {
        if (element == null) {
            return;
        }
        for (Element element2 : list) {
            Element element3 = element2.clone();
            element.addContent((Content)element3);
        }
    }

    private Element getCategoryElement(List<Element> list, String string) {
        for (Element element : list) {
            Attribute attribute = element.getAttribute("key");
            if (attribute == null || !string.equals(attribute.getValue())) continue;
            return element;
        }
        return null;
    }

    private Document generateBasicDocument() throws Exception {
        SAXBuilder sAXBuilder = new SAXBuilder();
        sAXBuilder.setIgnoringElementContentWhitespace(true);
        sAXBuilder.setIgnoringBoundaryWhitespace(true);
        sAXBuilder.setFeature("http://apache.org/xml/features/xinclude", true);
        File file = new File(MainApp.getDataPath() + "internal/ctemplate/config.xml");
        if (file.exists()) {
            BufferedReader bufferedReader = new BufferedReader(new InputStreamReader((InputStream)new FileInputStream(MainApp.getDataPath() + "internal/ctemplate/config.xml"), StandardCharsets.UTF_8));
            return sAXBuilder.build((Reader)bufferedReader);
        }
        throw new Exception(L.t((String)"File '%s internal/ctemplate/config.xml' doesn't exist", (Object[])new Object[]{MainApp.getDataPath()}));
    }
}

