/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.tradelist;

import com.strategyquant.lib.L;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.TradelistColumn;
import com.strategyquant.tradinglib.tradelist.TradelistColumnsList;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradelistTableColumnEntry
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"TableColumnEntry");
    public TradelistColumn tableColumn;

    public TradelistTableColumnEntry() {
    }

    public TradelistTableColumnEntry(TradelistColumn tradelistColumn) {
        this.tableColumn = tradelistColumn;
    }

    public String getColumnEntryName() {
        return this.tableColumn.getName();
    }

    public Object getValue(Order order) {
        try {
            return this.tableColumn.getValue(order);
        }
        catch (Exception exception) {
            Log.error("Error processing databank column '" + this.tableColumn.getClass().getSimpleName(), (Throwable)exception);
            return "N/A";
        }
    }

    public Element getXML() {
        Element element = new Element("Column");
        element.setAttribute("class", this.tableColumn.getClass().getSimpleName());
        element.setAttribute("name", this.tableColumn.getName());
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        String string = element.getAttributeValue("class");
        this.tableColumn = (TradelistColumn)TradelistColumnsList.get().createNew(string);
        if (this.tableColumn == null) {
            throw new Exception(L.t((String)"Invalid databank column '%s'.", (Object[])new Object[]{string}));
        }
    }
}

