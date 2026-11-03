/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import org.jdom2.Content;
import org.jdom2.Element;

public class OptProfileChecksLevels
implements IXMLAble {
    public boolean evalProfitOptCheck;
    public boolean evalAvgProfitCheck;
    public boolean evalUniformDistrCheck;
    public boolean evalTopProfitCheck;
    public int profitableOptPct;
    public double avgProfit;
    public int uniformDistrChanges;
    public double stdevAvgProfit;

    public OptProfileChecksLevels clone() {
        OptProfileChecksLevels optProfileChecksLevels = new OptProfileChecksLevels();
        optProfileChecksLevels.evalProfitOptCheck = this.evalProfitOptCheck;
        optProfileChecksLevels.evalAvgProfitCheck = this.evalAvgProfitCheck;
        optProfileChecksLevels.evalUniformDistrCheck = this.evalUniformDistrCheck;
        optProfileChecksLevels.evalTopProfitCheck = this.evalTopProfitCheck;
        optProfileChecksLevels.profitableOptPct = this.profitableOptPct;
        optProfileChecksLevels.avgProfit = this.avgProfit;
        optProfileChecksLevels.uniformDistrChanges = this.uniformDistrChanges;
        optProfileChecksLevels.stdevAvgProfit = this.stdevAvgProfit;
        return optProfileChecksLevels;
    }

    public Element getXML() {
        Element element = new Element("OptProfileChecksLevels");
        element.addContent((Content)new Element("ProfitableOptPct").setText(this.profitableOptPct + "").setAttribute("use", this.evalProfitOptCheck + ""));
        element.addContent((Content)new Element("AvgProfit").setText(this.avgProfit + "").setAttribute("use", this.evalAvgProfitCheck + ""));
        element.addContent((Content)new Element("UniformDistrChanges").setText(this.uniformDistrChanges + "").setAttribute("use", this.evalUniformDistrCheck + ""));
        element.addContent((Content)new Element("StdevAvgProfit").setText(this.stdevAvgProfit + "").setAttribute("use", this.evalTopProfitCheck + ""));
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.profitableOptPct = XMLUtil.getInt((Element)element, (String)"ProfitableOptPct", (int)30);
        this.avgProfit = XMLUtil.getDouble((Element)element, (String)"AvgProfit", (double)0.0);
        this.uniformDistrChanges = XMLUtil.getInt((Element)element, (String)"UniformDistrChanges", (int)5);
        this.stdevAvgProfit = XMLUtil.getDouble((Element)element, (String)"StdevAvgProfit", (double)1.0);
        this.evalProfitOptCheck = XMLUtil.getBoolean((Element)XMLUtil.tryAddElement((Element)element, (String)"ProfitableOptPct"), (String)"use", (boolean)true);
        this.evalAvgProfitCheck = XMLUtil.getBoolean((Element)XMLUtil.tryAddElement((Element)element, (String)"AvgProfit"), (String)"use", (boolean)true);
        this.evalUniformDistrCheck = XMLUtil.getBoolean((Element)XMLUtil.tryAddElement((Element)element, (String)"UniformDistrChanges"), (String)"use", (boolean)true);
        this.evalTopProfitCheck = XMLUtil.getBoolean((Element)XMLUtil.tryAddElement((Element)element, (String)"StdevAvgProfit"), (String)"use", (boolean)true);
    }
}

