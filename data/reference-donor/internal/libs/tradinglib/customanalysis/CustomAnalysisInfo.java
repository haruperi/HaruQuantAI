/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.customanalysis;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisMethodsList;
import java.io.Serializable;
import org.jdom2.Element;

public class CustomAnalysisInfo
implements Serializable {
    public boolean filter = false;
    public String inputArgs;
    public CustomAnalysisMethod method = null;
    public CustomAnalysisMethod perStrategy1 = null;
    public CustomAnalysisMethod perStrategy2 = null;
    public CustomAnalysisMethod fullDatabank1 = null;
    public CustomAnalysisMethod fullDatabank2 = null;
    public String inputArgsPerStrategy1;
    public String inputArgsPerStrategy2;
    public String inputArgsFullDatabank1;
    public String inputArgsFullDatabank2;

    public void loadRankingConfig(Element element) throws Exception {
        if (element == null) {
            return;
        }
        this.filter = XMLUtil.getBooleanAttr((Element)element, (String)"filter", (boolean)false);
        this.inputArgs = XMLUtil.getStringAttr((Element)element, (String)"inputArgs", (String)"");
        String string = XMLUtil.getStringAttr((Element)element, (String)"method", (String)"none");
        if (!string.equals("none")) {
            this.method = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(string);
        }
    }

    public void loadTaskConfig(Element element) throws Exception {
        if (element == null) {
            return;
        }
        this.filter = XMLUtil.getNodeBooleanValue((Element)element, (String)"Filter", (boolean)false);
        this.inputArgsPerStrategy1 = XMLUtil.getNodeValue((Element)element, (String)"InputArgsPerStrategy1", (String)"");
        this.inputArgsPerStrategy2 = XMLUtil.getNodeValue((Element)element, (String)"InputArgsPerStrategy2", (String)"");
        this.inputArgsFullDatabank1 = XMLUtil.getNodeValue((Element)element, (String)"InputArgsFullDatabank1", (String)"");
        this.inputArgsFullDatabank2 = XMLUtil.getNodeValue((Element)element, (String)"InputArgsFullDatabank2", (String)"");
        String string = XMLUtil.getNodeValue((Element)element, (String)"PerStrategy1", (String)"none");
        if (!string.equals("none")) {
            this.perStrategy1 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(string);
        }
        if (!(string = XMLUtil.getNodeValue((Element)element, (String)"PerStrategy2", (String)"none")).equals("none")) {
            this.perStrategy2 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(string);
        }
        if (!(string = XMLUtil.getNodeValue((Element)element, (String)"FullDatabank1", (String)"none")).equals("none")) {
            this.fullDatabank1 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(string);
        }
        if (!(string = XMLUtil.getNodeValue((Element)element, (String)"FullDatabank2", (String)"none")).equals("none")) {
            this.fullDatabank2 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(string);
        }
    }
}

