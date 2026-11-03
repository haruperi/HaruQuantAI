/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItemProperties;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public class TradingOptionsModifier {
    public static void modifyTradingOptions(TradingOptions tradingOptions, Element element, Element element2) throws Exception {
        Object object;
        int n;
        Object object2;
        Object object3;
        Element element3 = null;
        if (element2 != null) {
            object3 = element2.getChild("Options");
            object2 = XMLUtil.tryAddElement((Element)object3, (String)"BuildTradingOptions");
            element3 = XMLUtil.tryAddElement((Element)object2, (String)"Params");
        }
        object3 = new Variables(element);
        object2 = new HashMap();
        for (n = 0; n < ((ArrayList)object3).size(); ++n) {
            object = (Variable)((ArrayList)object3).get(n);
            ((HashMap)object2).put(((Variable)object).getId(), object);
        }
        for (n = 0; n < tradingOptions.size(); ++n) {
            object = (TradingOption)tradingOptions.get(n);
            String string = object.getClass().getSimpleName();
            ArrayList<IPGParameter> arrayList = ((ParametersTableItemProperties)object).getParams();
            for (int i = 0; i < arrayList.size(); ++i) {
                IPGParameter iPGParameter = arrayList.get(i);
                String string2 = iPGParameter.getKey();
                String string3 = String.format("%s.%s", string, string2);
                if (!((HashMap)object2).containsKey(string3)) continue;
                Variable variable = (Variable)((HashMap)object2).get(string3);
                String string4 = variable.getValue();
                if (variable.getInternalType() == 5) {
                    string4 = "" + SQTime.HHMMToMinutes((int)Integer.parseInt(string4)) * 60;
                }
                ((ParametersTableItemProperties)object).setParameterValue(iPGParameter.getKey(), string4);
                if (element3 == null) continue;
                List list = element3.getChildren("Param");
                boolean bl = false;
                for (int j = list.size() - 1; j >= 0; --j) {
                    Element element4 = (Element)list.get(j);
                    String string5 = element4.getAttributeValue("className");
                    String string6 = element4.getAttributeValue("key");
                    if (string5 == null || string6 == null || !string5.equals(string) || !string6.equals(string2)) continue;
                    element4.setText(string4);
                    bl = true;
                    break;
                }
                if (bl) continue;
                element3.addContent((Content)new Element("Param").setAttribute("className", string).setAttribute("key", string2).setText(string4));
            }
        }
    }
}

