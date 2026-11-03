/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyFingerprint
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyFingerprint");
    public String recordName;
    public int exactFingerprint;
    public String exactFingerprintStr;
    public int trades;
    public double profit;
    public double drawdown;
    public double fitness;
    public int tradesHash;

    public StrategyFingerprint() {
    }

    public StrategyFingerprint(ResultsGroup resultsGroup) {
        this.recordName = resultsGroup.getName();
        this.fitness = resultsGroup.getFitness();
        try {
            SQStats sQStats = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127);
            if (sQStats != null) {
                this.trades = sQStats.getInt("NumberOfTrades");
                this.profit = sQStats.getDouble("NetProfit");
                this.drawdown = sQStats.getDouble("Drawdown");
            }
            this.tradesHash = 0;
            OrdersList ordersList = resultsGroup.orders();
            for (int i = 0; i < Math.min(5, ordersList.size()); ++i) {
                Order order = ordersList.get(i);
                long l = order.OpenTime;
                l = SQTime.setSecond((long)l, (int)0);
                l = SQTime.setMiliSeconds((long)l, (int)0);
                this.tradesHash = (int)((long)this.tradesHash + l);
                l = order.OpenTime;
                l = SQTime.setSecond((long)l, (int)0);
                l = SQTime.setMiliSeconds((long)l, (int)0);
                this.tradesHash = (int)((long)this.tradesHash + l);
            }
            this.exactFingerprintStr = String.format("%.2f__%d__%d", this.profit, this.trades, this.tradesHash);
            this.exactFingerprint = this.exactFingerprintStr.hashCode();
        }
        catch (Exception exception) {
            Log.error("Cannot initialize strateyg fingerprint");
        }
    }

    public Element getXML() {
        Element element = new Element("Fingerprint");
        XMLUtil.trySetAttr((Element)element, (String)"strategyName", (Object)this.recordName);
        XMLUtil.trySetAttr((Element)element, (String)"exact", (Object)this.exactFingerprint);
        XMLUtil.trySetAttr((Element)element, (String)"trades", (Object)this.trades);
        XMLUtil.trySetAttr((Element)element, (String)"profit", (Object)this.profit);
        XMLUtil.trySetAttr((Element)element, (String)"drawdown", (Object)this.drawdown);
        XMLUtil.trySetAttr((Element)element, (String)"fitness", (Object)this.fitness);
        XMLUtil.trySetAttr((Element)element, (String)"tradesHash", (Object)this.tradesHash);
        return element;
    }

    public void setFromXML(Element element) {
        this.recordName = element.getAttributeValue("strategyName");
        this.exactFingerprint = XMLUtil.tryGetIntAttr((Element)element, (String)"exact");
        this.trades = XMLUtil.tryGetIntAttr((Element)element, (String)"trades");
        this.profit = XMLUtil.tryGetDoubleAttr((Element)element, (String)"profit");
        this.drawdown = XMLUtil.tryGetDoubleAttr((Element)element, (String)"drawdown");
        this.fitness = XMLUtil.tryGetDoubleAttr((Element)element, (String)"fitness");
        this.tradesHash = XMLUtil.tryGetIntAttr((Element)element, (String)"tradesHash");
    }
}

