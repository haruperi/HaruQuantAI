/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.exits;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import com.strategyquant.tradinglib.atm.exits.FixedProfit;
import com.strategyquant.tradinglib.atm.exits.MultipleOfOriginalPT;
import com.strategyquant.tradinglib.atm.exits.MultipleOfOriginalSL;
import com.strategyquant.tradinglib.atm.exits.None;
import com.strategyquant.tradinglib.atm.exits.TrailingStop;
import com.strategyquant.tradinglib.task.settings.buildmode.JSONAble;
import org.jdom2.Element;

public class ATMExitLevels
extends JSONAble {
    public static final String SL_BASED = "MultipleOfOriginalSL";
    public static final String PT_BASED = "MultipleOfOriginalPT";
    public static final String FIXED_PROFIT = "FixedProfit";
    public static final String TRAILING_STOP = "TrailingStop";
    public static final String NONE = "None";

    public static AbstractExitLevel create(Element element, int n) throws Exception {
        String string;
        switch (string = XMLUtil.getStringAttr((Element)element, (String)"key", (String)SL_BASED)) {
            case "MultipleOfOriginalSL": {
                return new MultipleOfOriginalSL(element, n);
            }
            case "MultipleOfOriginalPT": {
                return new MultipleOfOriginalPT(element, n);
            }
            case "FixedProfit": {
                return new FixedProfit(element, n);
            }
            case "TrailingStop": {
                return new TrailingStop(element, n);
            }
            case "None": {
                return new None(element, n);
            }
        }
        throw new Exception(L.t((String)"Unknown exit level type '%s'", (Object[])new Object[]{string}));
    }
}

