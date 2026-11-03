/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data;

import com.strategyquant.lib.L;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingData
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradingData");
    private OutOfSample oosRanges = new OutOfSample();
    private ArrayList<ChartSetup> chartSetups = new ArrayList();
    private String databankName;
    private SimpleDateFormat df = new SimpleDateFormat();

    public TradingData() {
        this.df.applyPattern("dd.MM.yyyy");
        this.df.setLenient(true);
    }

    public void setFromXML(Element element) throws Exception {
        ChartSetup chartSetup;
        List list;
        this.chartSetups.clear();
        this.oosRanges.clear();
        Element element2 = element.getChild("Setups");
        if (element2 != null) {
            list = element2.getChildren("Setup");
            if (list != null) {
                for (Object object : list) {
                    chartSetup = this.createChartSetup((Element)object);
                    if (chartSetup == null) continue;
                    this.chartSetups.add(chartSetup);
                }
            }
        } else {
            throw new Exception(L.t((String)"Cannot load Data setups. XML element Setups not found.", (Object[])new Object[0]));
        }
        list = element.getChild("OutOfSample");
        if (list != null) {
            List list2 = list.getChildren("Range");
            if (list2 != null) {
                Object object;
                object = list2.iterator();
                while (object.hasNext()) {
                    chartSetup = (Element)object.next();
                    this.oosRanges.addRange((Element)chartSetup);
                }
            }
        } else {
            throw new Exception(L.t((String)"Cannot load Data OOS periods. XML element OutOfSample not found.", (Object[])new Object[0]));
        }
    }

    public Element getXML() {
        Element element = new Element("Data");
        Element element2 = new Element("Setups");
        for (ChartSetup chartSetup : this.chartSetups) {
            element2.addContent((Content)chartSetup.getXML());
        }
        element.addContent((Content)element2);
        Element element3 = new Element("OutOfSample");
        element.addContent((Content)this.oosRanges.getXML());
        return element;
    }

    private ChartSetup createChartSetup(Element element) throws Exception {
        if (!element.getAttribute("use").getValue().equals("true")) {
            return null;
        }
        List list = element.getChildren("Chart");
        if (list.size() < 1) {
            throw new Exception(L.t((String)"No charts defined for a setup!", (Object[])new Object[0]));
        }
        Element element2 = (Element)list.get(0);
        String string = element2.getAttributeValue("symbol");
        String string2 = element2.getAttributeValue("timeframe");
        if (string.equals("not set") || string2.equals("not set")) {
            return null;
        }
        ChartSetup chartSetup = new ChartSetup("History", string, string2, this.recognizeDate(element.getAttributeValue("dateFrom")), this.recognizeDate(element.getAttributeValue("dateTo")), Double.parseDouble(element2.getAttributeValue("spread")), element.getAttributeValue("session"));
        for (int i = 1; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            try {
                chartSetup.addChart("History", element3.getAttributeValue("symbol"), element3.getAttributeValue("timeframe"));
                continue;
            }
            catch (Exception exception) {
                Log.error("Cannot add chart. ", (Throwable)exception);
            }
        }
        return chartSetup;
    }

    private long recognizeDate(String string) throws ParseException {
        Date date = this.df.parse(string);
        return date.getTime();
    }

    public OutOfSample getOOSRanges() {
        return this.oosRanges;
    }

    public void setOosRanges(OutOfSample outOfSample) {
        this.oosRanges = outOfSample;
    }

    public ArrayList<ChartSetup> getChartSetups() {
        return this.chartSetups;
    }

    public void setChartSetups(ArrayList<ChartSetup> arrayList) {
        this.chartSetups = arrayList;
    }

    public String getDatabankName() {
        return this.databankName;
    }

    public void setDatabankName(String string) {
        this.databankName = string;
    }
}

