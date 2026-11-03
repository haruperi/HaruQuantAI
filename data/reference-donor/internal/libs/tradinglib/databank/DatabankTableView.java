/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankTableView
implements IXMLAble {
    private static final Logger Log = LoggerFactory.getLogger(DatabankTableView.class);
    public ArrayList<DatabankTableColumnEntry> columns = new ArrayList();
    public String name = "?";

    public DatabankTableView() {
    }

    public DatabankTableView(String string) {
        this.name = string;
    }

    public String toString() {
        return this.name;
    }

    public String getName() {
        return this.name;
    }

    public Element getXML() {
        Element element = new Element("DatabankView");
        element.setAttribute("name", this.name);
        Element element2 = new Element("Columns");
        element.addContent((Content)element2);
        for (DatabankTableColumnEntry databankTableColumnEntry : this.columns) {
            element2.addContent((Content)databankTableColumnEntry.getXML());
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.name = element.getAttributeValue("name");
        this.columns.clear();
        Element element2 = element.getChild("Columns");
        if (element2 != null) {
            for (Element element3 : element2.getChildren("Column")) {
                DatabankTableColumnEntry databankTableColumnEntry = new DatabankTableColumnEntry();
                try {
                    databankTableColumnEntry.setFromXML(element3);
                    this.columns.add(databankTableColumnEntry);
                }
                catch (Exception exception) {
                    Log.error("View: " + this.name + " - cannot load column. Reason: " + exception.getMessage());
                }
            }
        }
    }
}

