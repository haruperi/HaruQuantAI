/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.sizes;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.sizes.AbstractATMPositionSize;
import com.strategyquant.tradinglib.atm.sizes.SizeAllRemaining;
import com.strategyquant.tradinglib.atm.sizes.SizeFixedLots;
import com.strategyquant.tradinglib.atm.sizes.SizePercents;
import com.strategyquant.tradinglib.task.settings.buildmode.JSONAble;
import org.jdom2.Element;

public class ATMSizes
extends JSONAble {
    public static final String PERCENTS = "SizePercents";
    public static final String FIXED_SIZE = "SizeFixedLots";
    public static final String ALL_REMAINING = "SizeAllRemaining";

    public static AbstractATMPositionSize create(Element element, int n, double d) throws Exception {
        String string;
        switch (string = XMLUtil.getStringAttr((Element)element, (String)"key", (String)PERCENTS)) {
            case "SizePercents": {
                return new SizePercents(element, n, d);
            }
            case "SizeFixedLots": {
                return new SizeFixedLots(element, n, d);
            }
            case "SizeAllRemaining": {
                return new SizeAllRemaining(element, n, d);
            }
        }
        throw new Exception(L.t((String)"Unknown position size type '%s'", (Object[])new Object[]{string}));
    }
}

