/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.output.XMLOutputter
 */
package com.strategyquant.wizard.desktop.indicators;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.wizard.desktop.indicators.SCustomIndicator;
import com.strategyquant.wizard.desktop.indicators.SCustomIndicatorFileParser;
import com.strategyquant.wizard.desktop.indicators.SParameter;
import java.awt.Component;
import java.io.File;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.output.XMLOutputter;

public class CustomIndicatorFileImporter {
    private Component parent;

    public CustomIndicatorFileImporter(Component component) {
        this.parent = component;
    }

    public String load(File file) {
        Element element = new Element("customIndicators");
        try {
            if (file.isDirectory() || !file.getName().contains(".mq4") && !file.getName().contains(".xml")) {
                MainApp.showErrorDialog((String)"File must be mq4 or xml");
                return null;
            }
            SCustomIndicator sCustomIndicator = SCustomIndicatorFileParser.parse(file);
            Element element2 = this.getCustomIndicatorNode(sCustomIndicator);
            element.addContent((Content)element2);
            return new XMLOutputter().outputString(element);
        }
        catch (Exception exception) {
            MainApp.showErrorDialog((String)("Error while parsing mq4 file:" + exception.getMessage()));
            return null;
        }
    }

    private Element getCustomIndicatorNode(SCustomIndicator sCustomIndicator) throws Exception {
        Element element = new Element("CustomIndicator").setAttribute("fileName", sCustomIndicator.fileName).setAttribute("shortName", sCustomIndicator.shortName).setAttribute("longName", sCustomIndicator.longName);
        element.setAttribute("returnType", sCustomIndicator.returnType);
        Element element2 = new Element("outputs");
        element.addContent((Content)element2);
        int n = 1;
        for (String object : sCustomIndicator.outputList) {
            element2.addContent((Content)new Element("output").setAttribute("index", Integer.toString(n)).setAttribute("name", object));
            ++n;
        }
        Element element3 = new Element("params");
        element.addContent((Content)element3);
        for (SParameter sParameter : sCustomIndicator.parameterList) {
            Element element4 = new Element("param").setAttribute("index", String.valueOf(sParameter.index)).setAttribute("name", sParameter.name).setAttribute("type", sParameter.type);
            element4.setAttribute("defaultValue", sParameter.value);
            element3.addContent((Content)element4);
        }
        return element;
    }
}

