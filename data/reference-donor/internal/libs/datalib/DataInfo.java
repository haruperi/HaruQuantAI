/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.datalib;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import java.io.Serializable;
import org.jdom2.Content;
import org.jdom2.Element;

public class DataInfo
implements IXMLAble,
Serializable {
    public int id;
    public int sourceDataId;
    public String connection;
    public String symbol;
    public String originalSymbol;
    public String instrument;
    public String timeframe;
    public String filename;
    public long dateFrom = 0L;
    public long dateTo = 0L;
    public int rows = 0;
    public long secondsRecords;
    public int totalDays;
    public int barTimeType;
    public InstrumentInfo symbolInfo;
    public int decimals;
    public String timezone;
    public int source;
    public String uSymbol;
    public String uSymbolName;
    public boolean removeWeekends;
    public boolean show;
    public String dateFromStr;
    public String dateToStr;
    public int basketId;
    public int brokerId = -1;
    public long fileHash;

    public Element getXML() {
        Element element = new Element("DataInfo");
        XMLUtil.trySetAttr((Element)element, (String)"connection", (Object)this.connection);
        XMLUtil.trySetAttr((Element)element, (String)"symbol", (Object)this.symbol);
        XMLUtil.trySetAttr((Element)element, (String)"originalSymbol", (Object)this.originalSymbol);
        XMLUtil.trySetAttr((Element)element, (String)"id", (Object)this.id);
        XMLUtil.trySetAttr((Element)element, (String)"sourceDataId", (Object)this.sourceDataId);
        XMLUtil.trySetAttr((Element)element, (String)"instrument", (Object)this.instrument);
        XMLUtil.trySetAttr((Element)element, (String)"timeframe", (Object)this.timeframe);
        XMLUtil.trySetAttr((Element)element, (String)"timezone", (Object)this.timezone);
        XMLUtil.trySetAttr((Element)element, (String)"filename", (Object)this.filename);
        XMLUtil.trySetAttr((Element)element, (String)"dateFrom", (Object)String.valueOf(this.dateFrom));
        XMLUtil.trySetAttr((Element)element, (String)"dateTo", (Object)String.valueOf(this.dateTo));
        XMLUtil.trySetAttr((Element)element, (String)"rows", (Object)String.valueOf(this.rows));
        XMLUtil.trySetAttr((Element)element, (String)"totalDays", (Object)String.valueOf(this.totalDays));
        XMLUtil.trySetAttr((Element)element, (String)"barType", (Object)String.valueOf(this.barTimeType));
        XMLUtil.trySetAttr((Element)element, (String)"decimals", (Object)String.valueOf(this.decimals));
        XMLUtil.trySetAttr((Element)element, (String)"source", (Object)String.valueOf(this.source));
        XMLUtil.trySetAttr((Element)element, (String)"uSymbol", (Object)String.valueOf(this.uSymbol));
        XMLUtil.trySetAttr((Element)element, (String)"uSymbolName", (Object)String.valueOf(this.uSymbolName));
        XMLUtil.trySetAttr((Element)element, (String)"removeWeekends", (Object)String.valueOf(this.removeWeekends));
        XMLUtil.trySetAttr((Element)element, (String)"fileHash", (Object)String.valueOf(this.fileHash));
        XMLUtil.trySetAttr((Element)element, (String)"basketId", (Object)this.basketId);
        XMLUtil.trySetAttr((Element)element, (String)"brokerId", (Object)this.brokerId);
        if (this.symbolInfo != null) {
            Element element2 = this.symbolInfo.getXML();
            element.addContent((Content)element2);
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.connection = element.getAttributeValue("connection");
        this.symbol = element.getAttributeValue("symbol");
        this.originalSymbol = element.getAttributeValue("originalSymbol");
        this.instrument = element.getAttributeValue("instrument");
        this.timeframe = element.getAttributeValue("timeframe");
        this.filename = element.getAttributeValue("filename");
        this.dateFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"dateFrom");
        this.dateTo = XMLUtil.tryGetLongAttr((Element)element, (String)"dateTo");
        this.rows = XMLUtil.tryGetIntAttr((Element)element, (String)"rows");
        this.totalDays = XMLUtil.tryGetIntAttr((Element)element, (String)"totalDays");
        this.barTimeType = XMLUtil.tryGetIntAttr((Element)element, (String)"barType");
        this.source = XMLUtil.tryGetIntAttr((Element)element, (String)"source");
        try {
            this.decimals = XMLUtil.tryGetIntAttr((Element)element, (String)"decimals");
        }
        catch (Exception exception) {
            this.decimals = 5;
        }
        this.timezone = element.getAttributeValue("timezone");
        Element element2 = element.getChild("InstrumentInfo");
        if (element2 != null) {
            this.symbolInfo = new InstrumentInfo();
            this.symbolInfo.setFromXML(element2);
        }
        this.uSymbol = element.getAttributeValue("uSymbol");
        this.uSymbolName = element.getAttributeValue("uSymbolName");
        this.removeWeekends = XMLUtil.tryGetBoolAttr((Element)element, (String)"removeWeekends");
        this.fileHash = XMLUtil.tryGetLongAttr((Element)element, (String)"fileHash");
        this.id = XMLUtil.getIntAttr((Element)element, (String)"id", (int)-1);
        this.sourceDataId = XMLUtil.getIntAttr((Element)element, (String)"sourceDataId", (int)-1);
        this.basketId = XMLUtil.getIntAttr((Element)element, (String)"basketId", (int)-1);
        this.brokerId = XMLUtil.getIntAttr((Element)element, (String)"brokerId", (int)-1);
    }

    public DataInfo clone() {
        DataInfo dataInfo = new DataInfo();
        dataInfo.connection = this.connection;
        dataInfo.symbol = this.symbol;
        dataInfo.originalSymbol = this.originalSymbol;
        dataInfo.instrument = this.instrument;
        dataInfo.timeframe = this.timeframe;
        dataInfo.filename = this.filename;
        dataInfo.dateFrom = this.dateFrom;
        dataInfo.dateTo = this.dateTo;
        dataInfo.rows = this.rows;
        dataInfo.secondsRecords = this.secondsRecords;
        dataInfo.totalDays = this.totalDays;
        dataInfo.barTimeType = this.barTimeType;
        dataInfo.symbolInfo = this.symbolInfo != null ? this.symbolInfo.clone() : null;
        dataInfo.decimals = this.decimals;
        dataInfo.timezone = this.timezone;
        dataInfo.source = this.source;
        dataInfo.uSymbol = this.uSymbol;
        dataInfo.uSymbolName = this.uSymbolName;
        dataInfo.removeWeekends = this.removeWeekends;
        dataInfo.fileHash = this.fileHash;
        dataInfo.basketId = this.basketId;
        dataInfo.brokerId = this.brokerId;
        return dataInfo;
    }

    public String toString() {
        return "DataInfo [symbol=" + this.symbol + ", instrument=" + this.instrument + ", timeframe=" + this.timeframe + ", filename=" + this.filename + "]";
    }
}

