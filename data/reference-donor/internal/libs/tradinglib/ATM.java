/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ATMExit;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.atm.ATMTypes;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ATM
implements Serializable {
    private static final Logger Log = LoggerFactory.getLogger(ATM.class);
    private int atmType;
    private int sizeDecimals = 1;
    private double minimalSize = 0.1;
    private ArrayList<ATMExit> exits;
    private ATMGenerateConfig generateConfig;

    public ATM(Element element) throws Exception {
        this(element, false);
    }

    public ATM(Element element, boolean bl) throws Exception {
        try {
            boolean bl2;
            this.sizeDecimals = XMLUtil.getIntAttr((Element)element, (String)"sizeDecimals", (int)1);
            this.minimalSize = XMLUtil.getDoubleAttr((Element)element, (String)"minSize", (double)0.1);
            this.exits = new ArrayList();
            boolean bl3 = bl2 = bl ? true : XMLUtil.getBooleanAttr((Element)element, (String)"enable", (boolean)false);
            if (!bl2) {
                this.atmType = 0;
                return;
            }
            this.atmType = ATMTypes.recognize(element.getAttributeValue("scaleOutType"), 2);
            List list = element.getChildren("ATM");
            boolean bl4 = false;
            for (int i = 0; i < list.size(); ++i) {
                Element element2 = (Element)list.get(i);
                String string = element2.getAttributeValue("id");
                if (string == null || !string.equals("global")) continue;
                Element element3 = XMLUtil.getChildElem((Element)element2, (String)"Exits");
                List list2 = element3.getChildren("Exit");
                for (int j = 0; j < list2.size(); ++j) {
                    Element element4 = (Element)list2.get(j);
                    ATMExit aTMExit = new ATMExit(j, element4, this.sizeDecimals, this.minimalSize);
                    this.exits.add(aTMExit);
                }
                bl4 = true;
                break;
            }
            if (!bl4) {
                throw new Exception(L.t((String)"Global ATM config not found", (Object[])new Object[0]));
            }
            Element element5 = element.getChild("GenerateConfig");
            if (element5 != null) {
                this.generateConfig = new ATMGenerateConfig();
                this.generateConfig.init(element5, this.sizeDecimals, this.minimalSize);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot get ATM settings.", (Throwable)exception);
            throw new Exception("Cannot get ATM settings - " + exception.getMessage());
        }
    }

    public ATM getClone() {
        return this;
    }

    public static void setForOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase) {
        ATM aTM;
        if (iLiveOrder.isClosedOrder() || (aTM = strategyBase.getATM()) != null) {
            // empty if block
        }
    }

    public boolean isApplicable(StrategyBase strategyBase, double d, double d2, byte by) {
        ATM aTM = strategyBase.getATM();
        if (aTM == null) {
            return false;
        }
        if (this.atmType == 0) {
            return false;
        }
        return aTM.getExitsCount() > 0;
    }

    public int getExitsCount() {
        return this.exits == null ? 0 : this.exits.size();
    }

    public ATMExit getExit(int n) {
        if (this.exits == null || n < 0 || n >= this.exits.size()) {
            return null;
        }
        return this.exits.get(n);
    }

    public int getType() {
        return this.atmType;
    }

    public int getSizeDecimals() {
        return this.sizeDecimals;
    }

    public double getMinimalSize() {
        return this.minimalSize;
    }

    public static ATM createFromStrategy(Element element) throws Exception {
        Element element2 = element.getChild("ATMs");
        if (element2 == null) {
            return null;
        }
        List list = element2.getChildren("ATM");
        if (list == null || list.isEmpty()) {
            return null;
        }
        return new ATM(element2, true);
    }

    public static Element setConfigATMToStrategy(ATM aTM, Element element, boolean bl) {
        if (aTM == null) {
            return element;
        }
        Element element2 = aTM.getXML();
        Element element3 = element.getChild("ATMs");
        if (element3 != null) {
            element.removeChild("ATMs");
        }
        Element element4 = new Element("ATMs");
        element.addContent((Content)element4);
        element4.setAttribute("enable", Boolean.toString(bl));
        element4.setAttribute("source", "config");
        element4.addContent((Content)element2);
        return element;
    }

    private Element getXML() {
        Element element = new Element("ATM");
        element.setAttribute("id", "global");
        element.setAttribute("sizeDecimals", Integer.toString(this.sizeDecimals));
        element.setAttribute("minimalSize", Double.toString(this.minimalSize));
        Element element2 = new Element("Exits");
        element.addContent((Content)element2);
        if (this.exits != null) {
            for (int i = 0; i < this.exits.size(); ++i) {
                ATMExit aTMExit = this.exits.get(i);
                Element element3 = aTMExit.getXML();
                element2.addContent((Content)element3);
            }
        }
        return element;
    }

    public static Element setSourceAndEnable(Element element, String string, boolean bl) {
        Element element2 = element.getChild("ATMs");
        if (element2 == null) {
            element2 = new Element("ATMs");
            element.addContent((Content)element2);
            if (string == null) {
                element2.setAttribute("source", "none");
            }
        }
        element2.setAttribute("enable", Boolean.toString(bl));
        if (string != null) {
            element2.setAttribute("source", string);
        }
        return element;
    }

    public boolean isUsed() {
        return this.atmType != 0;
    }

    public ATMGenerateConfig getGenerateConfig() {
        return this.generateConfig;
    }

    public void changeToStrategy() {
        this.atmType = 1;
    }
}

