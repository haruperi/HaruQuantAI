/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMMoveSL2BE;
import com.strategyquant.tradinglib.atm.exits.ATMExitLevels;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import com.strategyquant.tradinglib.atm.sizes.ATMSizes;
import com.strategyquant.tradinglib.atm.sizes.AbstractATMPositionSize;
import java.io.Serializable;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ATMExit
implements Serializable {
    private static final Logger Log = LoggerFactory.getLogger(ATMExit.class);
    public AbstractATMPositionSize positionSize;
    public AbstractExitLevel exitLevel;
    public ATMMoveSL2BE moveSL2BE;
    private int exitIndex;
    private Element elExit;
    private int sizeDecimals;
    private double minimalSize;

    public ATMExit(int n, Element element, int n2, double d) throws Exception {
        try {
            Object object;
            this.exitIndex = n;
            this.elExit = element;
            this.sizeDecimals = n2;
            this.minimalSize = d;
            Element element2 = XMLUtil.getChildElem((Element)element, (String)"PositionSizes");
            List list = element2.getChildren("PositionSize");
            for (int i = 0; i < list.size(); ++i) {
                object = (Element)list.get(i);
                if (!XMLUtil.elementIs((Element)object, (String)"use")) continue;
                this.positionSize = ATMSizes.create((Element)object, n2, d);
                break;
            }
            Element element3 = XMLUtil.getChildElem((Element)element, (String)"ExitLevels");
            object = element3.getChildren("ExitLevel");
            for (int i = 0; i < object.size(); ++i) {
                Element element4 = (Element)object.get(i);
                if (!XMLUtil.elementIs((Element)element4, (String)"use")) continue;
                this.exitLevel = ATMExitLevels.create(element4, n);
                break;
            }
            if (this.exitLevel == null) {
                throw new Exception("Exit level not defined.");
            }
            Element element5 = XMLUtil.getChildElem((Element)element, (String)"MoveSL2BE");
            this.moveSL2BE = new ATMMoveSL2BE(element5);
        }
        catch (Exception exception) {
            throw new Exception(String.format("ATM Exit #%d - %s", n + 1, exception.getMessage()));
        }
    }

    public double computeSize(double d, double d2, boolean bl) {
        if (d2 >= d) {
            return 0.0;
        }
        return Math.min(this.positionSize.computeSize(d, d2, bl), SQUtils.round((double)(d - d2), (int)this.sizeDecimals));
    }

    public void setForOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, double d2) throws TradingException {
        this.exitLevel.setForOrder(iLiveOrder, strategyBase, d, d2);
    }

    public static String toString(byte by, byte by2) {
        return String.format("Exit #%d - %s", by2 + 1, OrderCloseTypes.toString(by));
    }

    public String toString() {
        if (this.moveSL2BE.MoveSL2BE) {
            return String.format("%s %s + %s", this.positionSize.toString(), this.exitLevel.toString(), this.moveSL2BE.toString());
        }
        return String.format("%s %s", this.positionSize.toString(), this.exitLevel.toString());
    }

    public Element getXML() {
        Element element = new Element("Exit");
        Element element2 = new Element("PositionSizes");
        element.addContent((Content)element2);
        Element element3 = this.positionSize.getXML();
        element3.setAttribute("use", "true");
        element2.addContent((Content)element3);
        Element element4 = new Element("ExitLevels");
        element.addContent((Content)element4);
        Element element5 = this.exitLevel.getXML();
        element5.setAttribute("use", "true");
        element4.addContent((Content)element5);
        Element element6 = this.moveSL2BE.getXML();
        element.addContent((Content)element6);
        return element;
    }

    public ATMExit clone() {
        try {
            return new ATMExit(this.exitIndex, this.elExit, this.sizeDecimals, this.minimalSize);
        }
        catch (Exception exception) {
            return null;
        }
    }
}

