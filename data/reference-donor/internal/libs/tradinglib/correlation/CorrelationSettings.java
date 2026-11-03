/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.correlation;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.correlation.CorrelationTypes;
import java.io.Serializable;
import org.jdom2.Element;

public class CorrelationSettings
implements Serializable {
    public double maxCorrelation;
    public CorrelationType correlationType;
    public int correlationPeriod;
    public boolean allowNegativeCorrelation;
    public boolean addEmptyPeriods;

    public void loadFromXml(Element element) throws Exception {
        this.maxCorrelation = XMLUtil.getDouble((Element)element, (String)"CorrMax", (double)0.3);
        String string = XMLUtil.getNodeValue((Element)element, (String)"CorrType", (String)"ProfitLoss");
        this.correlationType = (CorrelationType)CorrelationTypes.getInstance().findClassByName(string);
        this.correlationPeriod = XMLUtil.getInt((Element)element, (String)"CorrPeriod", (int)10);
        this.allowNegativeCorrelation = XMLUtil.getBoolean((Element)element, (String)"CorrAllowNegative", (boolean)true);
        this.addEmptyPeriods = XMLUtil.getBoolean((Element)element, (String)"CorrAddEmptyPeriods", (boolean)false);
    }
}

