/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.SQStats;
import org.jdom2.Content;
import org.jdom2.Element;

public class WalkForwardPeriod
implements IXMLAble {
    public long optimizeFrom = 0L;
    public long optimizeTo = 0L;
    public long runFrom = 0L;
    public long runTo = 0L;
    public boolean futurePeriod = false;
    public String testParameters = null;
    public SQStats optimizationStatData = null;
    public SQStats runStatData = null;

    public Element getXML() {
        Element element = new Element("WalkForwardPeriod");
        XMLUtil.trySetAttr((Element)element, (String)"optimizeFrom", (Object)this.optimizeFrom);
        XMLUtil.trySetAttr((Element)element, (String)"optimizeTo", (Object)this.optimizeTo);
        XMLUtil.trySetAttr((Element)element, (String)"runFrom", (Object)this.runFrom);
        XMLUtil.trySetAttr((Element)element, (String)"runTo", (Object)this.runTo);
        XMLUtil.trySetAttr((Element)element, (String)"futurePeriod", (Object)this.futurePeriod);
        XMLUtil.trySetAttr((Element)element, (String)"testParameters", (Object)this.testParameters);
        Element element2 = new Element("OptimizationStats");
        element.addContent((Content)element2);
        Element element3 = XMLUtil.valueToElement((String)"stats", (Object)this.optimizationStatData);
        if (element3 != null) {
            element2.addContent((Content)element3);
        }
        Element element4 = new Element("RunStats");
        element.addContent((Content)element4);
        Element element5 = XMLUtil.valueToElement((String)"stats", (Object)this.runStatData);
        if (element5 != null) {
            element4.addContent((Content)element5);
        }
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.optimizeFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"optimizeFrom");
        this.optimizeTo = XMLUtil.tryGetLongAttr((Element)element, (String)"optimizeTo");
        this.runFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"runFrom");
        this.runTo = XMLUtil.tryGetLongAttr((Element)element, (String)"runTo");
        this.futurePeriod = XMLUtil.tryGetBoolAttr((Element)element, (String)"futurePeriod");
        this.testParameters = element.getAttributeValue("testParameters");
        if (element.getChild("OptimizationStats").getChild("stats").getChild("SQStats") != null) {
            if (this.optimizationStatData == null) {
                this.optimizationStatData = new SQStats();
            }
            this.optimizationStatData.setFromXML(element.getChild("OptimizationStats").getChild("stats").getChild("SQStats"));
        }
        if (element.getChild("RunStats").getChild("stats") != null && element.getChild("RunStats").getChild("stats").getChild("SQStats") != null) {
            if (this.runStatData == null) {
                this.runStatData = new SQStats();
            }
            this.runStatData.setFromXML(element.getChild("RunStats").getChild("stats").getChild("SQStats"));
        }
    }
}

