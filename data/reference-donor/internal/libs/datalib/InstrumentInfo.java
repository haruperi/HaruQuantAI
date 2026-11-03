/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import java.io.Serializable;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InstrumentInfo
implements IXMLAble,
Serializable {
    public static final Logger Log = LoggerFactory.getLogger(InstrumentInfo.class);
    public String connection;
    public String instrument;
    public int broker = -1;
    public String description;
    public double tickSize;
    public double tickStep;
    public double tickValueInMoney;
    public String filename;
    public long dateFrom = 0L;
    public long dateTo = 0L;
    public int rows;
    public int totalDays;
    public double defaultSpread;
    public double defaultSlippage;
    public double minDistance;
    public int decimals;
    public String timeframe;
    public double pointValue;
    public int dataType;
    public boolean recognizedFromOrders = false;
    public String alias;
    public String exchange;
    public String country;
    public String sector;
    public String commissions;
    public String swap;
    public double orderSizeMultiplier = 1.0;
    public double orderSizeStep = 0.0;

    public InstrumentInfo() {
    }

    public InstrumentInfo(Element element) {
        this.setFromXML(element);
    }

    public Element getXML() {
        Element element = new Element("InstrumentInfo");
        XMLUtil.trySetAttr((Element)element, (String)"connection", (Object)this.connection);
        XMLUtil.trySetAttr((Element)element, (String)"instrument", (Object)this.instrument);
        XMLUtil.trySetAttr((Element)element, (String)"description", (Object)this.description);
        XMLUtil.trySetAttr((Element)element, (String)"tickSize", (Object)String.valueOf(this.tickSize));
        XMLUtil.trySetAttr((Element)element, (String)"tickStep", (Object)String.valueOf(this.tickStep));
        XMLUtil.trySetAttr((Element)element, (String)"minDistance", (Object)String.valueOf(this.minDistance));
        XMLUtil.trySetAttr((Element)element, (String)"tickValueInMoney", (Object)String.valueOf(this.tickValueInMoney));
        XMLUtil.trySetAttr((Element)element, (String)"filename", (Object)this.filename);
        XMLUtil.trySetAttr((Element)element, (String)"dateFrom", (Object)String.valueOf(this.dateFrom));
        XMLUtil.trySetAttr((Element)element, (String)"dateTo", (Object)String.valueOf(this.dateTo));
        XMLUtil.trySetAttr((Element)element, (String)"rows", (Object)String.valueOf(this.rows));
        XMLUtil.trySetAttr((Element)element, (String)"totalDays", (Object)String.valueOf(this.totalDays));
        XMLUtil.trySetAttr((Element)element, (String)"defaultSpread", (Object)String.valueOf(this.defaultSpread));
        XMLUtil.trySetAttr((Element)element, (String)"defaultSlippage", (Object)String.valueOf(this.defaultSlippage));
        XMLUtil.trySetAttr((Element)element, (String)"decimals", (Object)String.valueOf(this.decimals));
        XMLUtil.trySetAttr((Element)element, (String)"timeframe", (Object)this.timeframe);
        XMLUtil.trySetAttr((Element)element, (String)"commissions", (Object)String.valueOf(this.commissions));
        XMLUtil.trySetAttr((Element)element, (String)"pointValue", (Object)String.valueOf(this.pointValue));
        XMLUtil.trySetAttr((Element)element, (String)"dataType", (Object)String.valueOf(this.dataType));
        XMLUtil.trySetAttr((Element)element, (String)"recognizedFromOrders", (Object)String.valueOf(this.recognizedFromOrders));
        XMLUtil.trySetAttr((Element)element, (String)"alias", (Object)this.alias);
        XMLUtil.trySetAttr((Element)element, (String)"exchange", (Object)this.exchange);
        XMLUtil.trySetAttr((Element)element, (String)"country", (Object)this.country);
        XMLUtil.trySetAttr((Element)element, (String)"sector", (Object)this.sector);
        XMLUtil.trySetAttr((Element)element, (String)"swap", (Object)String.valueOf(this.swap));
        XMLUtil.trySetAttr((Element)element, (String)"orderSizeMultiplier", (Object)String.valueOf(this.orderSizeMultiplier));
        XMLUtil.trySetAttr((Element)element, (String)"orderSizeStep", (Object)String.valueOf(this.orderSizeStep));
        XMLUtil.trySetAttr((Element)element, (String)"broker", (Object)String.valueOf(this.broker));
        return element;
    }

    public void setFromXML(Element element) {
        this.connection = this.internIfNotNull(element.getAttributeValue("connection"));
        this.instrument = this.internIfNotNull(element.getAttributeValue("instrument"));
        this.description = this.internIfNotNull(element.getAttributeValue("description"));
        this.tickSize = XMLUtil.tryGetDoubleAttr((Element)element, (String)"tickSize");
        this.tickStep = XMLUtil.tryGetDoubleAttr((Element)element, (String)"tickStep");
        this.minDistance = XMLUtil.getDoubleAttr((Element)element, (String)"minDistance", (double)0.0);
        this.tickValueInMoney = XMLUtil.tryGetDoubleAttr((Element)element, (String)"tickValueInMoney");
        this.filename = this.internIfNotNull(element.getAttributeValue("filename"));
        this.dateFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"dateFrom");
        this.dateTo = XMLUtil.tryGetLongAttr((Element)element, (String)"dateTo");
        this.rows = XMLUtil.tryGetIntAttr((Element)element, (String)"rows");
        this.totalDays = XMLUtil.tryGetIntAttr((Element)element, (String)"totalDays");
        this.defaultSpread = XMLUtil.tryGetDoubleAttr((Element)element, (String)"defaultSpread");
        this.defaultSlippage = XMLUtil.getDoubleAttr((Element)element, (String)"defaultSlippage", (double)0.0);
        this.decimals = XMLUtil.tryGetIntAttr((Element)element, (String)"decimals");
        this.timeframe = this.internIfNotNull(element.getAttributeValue("timeframe"));
        this.commissions = this.internIfNotNull(element.getAttributeValue("commissions"));
        this.pointValue = XMLUtil.tryGetDoubleAttr((Element)element, (String)"pointValue");
        this.dataType = XMLUtil.tryGetIntAttr((Element)element, (String)"dataType");
        this.recognizedFromOrders = XMLUtil.tryGetBoolAttr((Element)element, (String)"recognizedFromOrders");
        this.alias = this.internIfNotNull(element.getAttributeValue("alias"));
        this.exchange = this.internIfNotNull(element.getAttributeValue("exchange"));
        this.country = this.internIfNotNull(element.getAttributeValue("country"));
        this.sector = this.internIfNotNull(element.getAttributeValue("sector"));
        this.swap = this.internIfNotNull(element.getAttributeValue("swap"));
        this.orderSizeMultiplier = XMLUtil.getDoubleAttr((Element)element, (String)"orderSizeMultiplier", (double)1.0);
        this.orderSizeStep = XMLUtil.getDoubleAttr((Element)element, (String)"orderSizeStep", (double)0.0);
        this.broker = XMLUtil.getIntAttr((Element)element, (String)"broker", (int)-1);
    }

    private String internIfNotNull(String string) {
        if (string == null) {
            return null;
        }
        return string.intern();
    }

    public InstrumentInfo clone() {
        InstrumentInfo instrumentInfo = new InstrumentInfo();
        instrumentInfo.connection = this.connection;
        instrumentInfo.instrument = this.instrument;
        instrumentInfo.description = this.description;
        instrumentInfo.tickSize = this.tickSize;
        instrumentInfo.tickStep = this.tickStep;
        instrumentInfo.tickValueInMoney = this.tickValueInMoney;
        instrumentInfo.filename = this.filename;
        instrumentInfo.dateFrom = this.dateFrom;
        instrumentInfo.dateTo = this.dateTo;
        instrumentInfo.rows = this.rows;
        instrumentInfo.totalDays = this.totalDays;
        instrumentInfo.defaultSpread = this.defaultSpread;
        instrumentInfo.defaultSlippage = this.defaultSlippage;
        instrumentInfo.decimals = this.decimals;
        instrumentInfo.timeframe = this.timeframe;
        instrumentInfo.commissions = this.commissions;
        instrumentInfo.pointValue = this.pointValue;
        instrumentInfo.dataType = this.dataType;
        instrumentInfo.recognizedFromOrders = this.recognizedFromOrders;
        instrumentInfo.alias = this.alias;
        instrumentInfo.exchange = this.exchange;
        instrumentInfo.country = this.country;
        instrumentInfo.sector = this.sector;
        instrumentInfo.swap = this.swap;
        instrumentInfo.orderSizeMultiplier = this.orderSizeMultiplier;
        instrumentInfo.orderSizeStep = this.orderSizeStep;
        instrumentInfo.minDistance = this.minDistance;
        instrumentInfo.broker = this.broker;
        return instrumentInfo;
    }
}

