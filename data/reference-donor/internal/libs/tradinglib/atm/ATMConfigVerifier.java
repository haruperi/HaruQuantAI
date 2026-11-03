/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.atm;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.task.settings.blocks.ConfigVerifier;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ATMConfigVerifier {
    private static final Logger Log = LoggerFactory.getLogger(ConfigVerifier.class);

    public static void verifyConfig(Element element) throws Exception {
        ATMConfigVerifier.verifyConfig(element, null);
    }

    public static void verifyConfig(Element element, TaskSettingsData taskSettingsData) throws Exception {
        if (element == null) {
            ATMConfigVerifier.addError(taskSettingsData, L.t((String)"Invalid XML configuration - missing Settings element.", (Object[])new Object[0]));
        } else {
            try {
                ATMConfigVerifier.checkATM(element);
            }
            catch (Exception exception) {
                ATMConfigVerifier.addError(taskSettingsData, exception.getMessage());
            }
        }
    }

    public static void checkATM(Element element) throws Exception {
        Element element2 = element.getChild("RiskMoneyManagement");
        if (element2 == null) {
            return;
        }
        double d = ATMConfigVerifier.getFixedSizeFromMM(element2);
        if (d == 0.0) {
            return;
        }
        Element element3 = element.getChild("ATMs");
        if (element3 == null) {
            return;
        }
        boolean bl = XMLUtil.getBooleanAttr((Element)element3, (String)"enable", (boolean)false);
        if (!bl) {
            return;
        }
        int n = ATMConfigVerifier.getNumberOfExits(element3);
        if (n <= 0) {
            return;
        }
        double d2 = XMLUtil.getDoubleAttr((Element)element3, (String)"minSize", (double)0.1);
        if (d2 == d && n > 1) {
            throw new Exception(L.t((String)"Minimal ATM exit size equals to your fixed size in Money Management, but you have multiple ATM exits.", (Object[])new Object[0]) + L.t((String)"This means it is not possible to use more than one exit !", (Object[])new Object[0]));
        }
    }

    private static int getNumberOfExits(Element element) {
        Element element2 = element.getChild("ATM");
        if (element2 == null) {
            return 0;
        }
        Element element3 = element2.getChild("Exits");
        if (element3 == null) {
            return 0;
        }
        List list = element3.getChildren("Exit");
        if (list == null) {
            return 0;
        }
        return list.size();
    }

    private static double getFixedSizeFromMM(Element element) {
        Element element2 = element.getChild("MoneyManagement");
        if (element2 == null) {
            return 0.0;
        }
        List list = element2.getChildren("Method");
        if (list == null) {
            return 0.0;
        }
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element3 = (Element)list.get(i);
            String string2 = element3.getAttributeValue("use");
            if (string2 == null || !string2.equals("true") || (string = element3.getAttributeValue("type")) == null || !string.equals("FixedSize")) continue;
            Element element4 = element3.getChild("Params");
            if (element4 == null) break;
            double d = XMLUtil.getItemDoubleParam((Element)element4, (String)"Size", (double)0.0);
            return d;
        }
        return 0.0;
    }

    private static void addError(TaskSettingsData taskSettingsData, String string) throws Exception {
        if (taskSettingsData == null) {
            throw new Exception(L.t((String)"Money Management / ATM settings", (Object[])new Object[0]) + " - " + string);
        }
        taskSettingsData.addError(L.t((String)"Money Management / ATM settings", (Object[])new Object[0]), null, string);
    }
}

