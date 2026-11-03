/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.customData.ct;

import com.strategyquant.datalib.customData.ct.CTCustomIndicator;
import com.strategyquant.datalib.customData.ct.CTCustomIndicatorOutput;
import com.strategyquant.lib.XMLUtil;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CTCustomIndicators
extends HashMap<String, CTCustomIndicator> {
    public static final Logger Log = LoggerFactory.getLogger(CTCustomIndicators.class);

    public CTCustomIndicators(Element element) throws Exception {
        try {
            List list = element.getChildren("Item");
            for (Element element2 : list) {
                CTCustomIndicator cTCustomIndicator = new CTCustomIndicator(element2);
                if (this.containsKey(cTCustomIndicator.fileName)) continue;
                this.put(cTCustomIndicator.fileName, cTCustomIndicator);
            }
        }
        catch (Exception exception) {
            throw new Exception("Failed to load Custom Indicators - " + exception.getMessage(), exception);
        }
    }

    public void addSourceCodesToItem(Element element, String string) throws Exception {
        CTCustomIndicatorOutput cTCustomIndicatorOutput;
        element.setAttribute("cdataIndyName", string);
        CTCustomIndicator cTCustomIndicator = (CTCustomIndicator)this.get(string);
        if (cTCustomIndicator == null) {
            Log.error("Cannot load data info for CustomIndicator {}", (Object)string);
            element.setAttribute("mt4", "");
            element.setAttribute("mt5", "");
            element.setAttribute("el", "");
            element.setAttribute("jf", "");
            return;
        }
        String string2 = null;
        Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#Output#");
        if (element2 != null) {
            string2 = element2.getText();
        }
        if ((cTCustomIndicatorOutput = cTCustomIndicator.outputs.get(string2)) == null) {
            throw new Exception(String.format("CustomIndicator[%s].Output '%s' not found.", string, string2));
        }
        try {
            String string3 = cTCustomIndicatorOutput.mt4;
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("mt4", string3);
            string3 = cTCustomIndicatorOutput.mt5;
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("mt5", string3);
            string3 = cTCustomIndicatorOutput.el;
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("el", string3);
            string3 = cTCustomIndicatorOutput.jf;
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("jf", string3);
        }
        catch (Exception exception) {
            Log.error("Cannot load Src value", (Throwable)exception);
        }
    }
}

