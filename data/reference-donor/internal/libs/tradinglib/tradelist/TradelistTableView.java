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
package com.strategyquant.tradinglib.tradelist;

import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.TradelistColumn;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradelistTableView
implements IXMLAble {
    private static final Logger Log = LoggerFactory.getLogger(TradelistTableView.class);
    public ArrayList<TradelistTableColumnEntry> columns = new ArrayList();
    public static final String FILE_EXTENSION = "vw";
    public static final String DEFAULT_VIEW_NAME = "Default";
    public static final int extraColumnsCount = 5;
    public String name = "?";
    public long lastChanged = 0L;

    public TradelistTableView() {
    }

    public TradelistTableView(String string) {
        this.name = string;
    }

    public String toString() {
        return this.name;
    }

    public Element getXML() {
        Element element = new Element("DatabankView");
        element.setAttribute("name", this.name);
        Element element2 = new Element("Columns");
        element.addContent((Content)element2);
        for (TradelistTableColumnEntry tradelistTableColumnEntry : this.columns) {
            element2.addContent((Content)tradelistTableColumnEntry.getXML());
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.name = element.getAttributeValue("name");
        this.columns.clear();
        Element element2 = element.getChild("Columns");
        if (element2 != null) {
            for (Element element3 : element2.getChildren("Column")) {
                TradelistTableColumnEntry tradelistTableColumnEntry = new TradelistTableColumnEntry();
                try {
                    tradelistTableColumnEntry.setFromXML(element3);
                    this.columns.add(tradelistTableColumnEntry);
                }
                catch (Exception exception) {
                    Log.error(this.name + " - " + exception.getMessage());
                }
            }
        }
    }

    public ArrayList<Object[]> getData(OrdersList ordersList, int n, int n2, boolean bl) throws Exception {
        ArrayList<Object[]> arrayList = new ArrayList<Object[]>();
        int n3 = this.columns.size();
        new Order();
        for (int i = n; i < n + n2 && i <= ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            order.Order = i + 1;
            Object[] objectArray = new Object[n3 + 5];
            for (int j = 0; j < n3; ++j) {
                TradelistTableColumnEntry tradelistTableColumnEntry = this.columns.get(j);
                try {
                    TradelistColumn tradelistColumn = tradelistTableColumnEntry.tableColumn;
                    Object object = tradelistColumn.getClass().getSimpleName().equals("Balance") && order.AccountBalanceTemp != -1.0E8f ? Float.valueOf(order.AccountBalanceTemp) : tradelistColumn.getValue(order);
                    boolean bl2 = bl || tradelistColumn.getType().equals("Text");
                    objectArray[j] = bl2 ? tradelistColumn.getFormattedValue(object) : object;
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Cannot print tradelist column value. Exc.", (Throwable)exception);
                    objectArray[j] = "N/A";
                }
            }
            objectArray[objectArray.length - 5] = order.Ticket;
            objectArray[objectArray.length - 4] = order.OpenTime;
            objectArray[objectArray.length - 3] = order.CloseTime;
            objectArray[objectArray.length - 2] = order.SampleType;
            objectArray[objectArray.length - 1] = order.Type;
            arrayList.add(objectArray);
        }
        return arrayList;
    }
}

