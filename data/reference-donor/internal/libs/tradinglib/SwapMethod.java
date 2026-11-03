/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.SwapTypes;
import java.io.Serializable;
import org.jdom2.Element;

public class SwapMethod
implements IXMLAble,
Serializable {
    private boolean use;
    private String type;
    private double longSwap;
    private double shortSwap;
    private String tripleSwapOn;
    private String rolloutHour;
    private int[] rolloutHourHHMM;

    public SwapMethod() {
    }

    public SwapMethod(boolean bl, String string, double d, double d2, String string2, String string3) {
        this.use = bl;
        this.type = string;
        this.longSwap = d;
        this.shortSwap = d2;
        this.tripleSwapOn = string2;
        this.rolloutHour = string3;
        try {
            this.rolloutHourHHMM = SQTime.getHHMM((String)string3);
        }
        catch (Exception exception) {
            this.rolloutHourHHMM = new int[]{23, 0};
        }
    }

    public Element getXML() {
        Element element = new Element("Swap");
        element.setAttribute("use", String.valueOf(this.use));
        element.setAttribute("type", this.type != null ? this.type : "");
        element.setAttribute("long", String.valueOf(this.longSwap));
        element.setAttribute("short", String.valueOf(this.shortSwap));
        element.setAttribute("tripleSwapOn", this.tripleSwapOn != null ? this.tripleSwapOn : "");
        element.setAttribute("rolloutHour", this.rolloutHour != null ? this.rolloutHour : "23:00");
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.use = XMLUtil.getBooleanAttr((Element)element, (String)"use", (boolean)false);
        this.type = XMLUtil.getStringAttr((Element)element, (String)"type", null);
        this.longSwap = XMLUtil.getDoubleAttr((Element)element, (String)"long", (double)0.0);
        this.shortSwap = XMLUtil.getDoubleAttr((Element)element, (String)"short", (double)0.0);
        this.tripleSwapOn = XMLUtil.getStringAttr((Element)element, (String)"tripleSwapOn", null);
        this.rolloutHour = XMLUtil.getStringAttr((Element)element, (String)"rolloutHour", (String)"23:00");
        try {
            this.rolloutHourHHMM = SQTime.getHHMM((String)this.rolloutHour);
        }
        catch (Exception exception) {
            this.rolloutHourHHMM = new int[]{23, 0};
        }
    }

    public boolean isUsed() {
        return this.use;
    }

    public String getType() {
        return this.type;
    }

    public double getLongSwap() {
        return this.longSwap;
    }

    public double getShortSwap() {
        return this.shortSwap;
    }

    public String getTripleSwapOn() {
        return this.tripleSwapOn;
    }

    public int getRolloutHour() {
        try {
            return this.rolloutHourHHMM[0];
        }
        catch (Exception exception) {
            return 23;
        }
    }

    public int getRolloutMinute() {
        try {
            return this.rolloutHourHHMM[1];
        }
        catch (Exception exception) {
            return 0;
        }
    }

    public SwapMethod clone() {
        SwapMethod swapMethod = new SwapMethod();
        swapMethod.use = this.use;
        swapMethod.type = this.type;
        swapMethod.longSwap = this.longSwap;
        swapMethod.shortSwap = this.shortSwap;
        swapMethod.tripleSwapOn = this.tripleSwapOn;
        swapMethod.rolloutHour = this.rolloutHour;
        return swapMethod;
    }

    public String getTypeSymbol() {
        return SwapTypes.toString(this.getType());
    }

    public String printFormatedName() {
        if (this.isUsed()) {
            return String.format("Long %s%s, Short: %s%s, Triple on %s", this.getLongSwap(), this.getTypeSymbol(), this.getShortSwap(), this.getTypeSymbol(), this.getTripleSwapOn());
        }
        return "No swap";
    }
}

