/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import org.jdom2.Element;

public class ATMMoveSL2BE {
    public boolean MoveSL2BE;
    public boolean MoveSL2BEAddPips;
    public int Type;
    public int AddPipsValue;

    public ATMMoveSL2BE(Element element) {
        this.MoveSL2BE = XMLUtil.getItemBoolParam((Element)element, (String)"MoveSL2BE", (boolean)false);
        this.MoveSL2BEAddPips = XMLUtil.getItemBoolParam((Element)element, (String)"MoveSL2BEAddPips", (boolean)false);
        this.Type = XMLUtil.getItemIntParam((Element)element, (String)"Type", (int)1);
        this.AddPipsValue = XMLUtil.getItemIntParam((Element)element, (String)"AddPipsValue", (int)10);
    }

    public void apply(LiveOrderObj liveOrderObj) {
    }

    public Element getXML() {
        Element element = new Element("MoveSL2BE");
        XMLUtil.setItemBoolParam((Element)element, (String)"MoveSL2BE", (boolean)this.MoveSL2BE);
        XMLUtil.setItemBoolParam((Element)element, (String)"MoveSL2BEAddPips", (boolean)this.MoveSL2BEAddPips);
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)this.Type);
        XMLUtil.setItemIntParam((Element)element, (String)"AddPipsValue", (int)this.AddPipsValue);
        return element;
    }

    public String toString() {
        String string = "Move SL 2 BE";
        if (this.MoveSL2BEAddPips && this.Type == 1) {
            string = string + String.format(" + %d pips", this.AddPipsValue);
        }
        return string;
    }
}

