/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.atm.ATMTypes
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.task.settings.partstoimprove.PartsToImprove
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.PartsToImprove;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.atm.ATMTypes;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.task.settings.partstoimprove.PartsToImprove;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Parts to improve setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class PartsToImproveSettingsPlugin
implements ISettingTabPlugin {
    public static final Logger Log = LoggerFactory.getLogger(PartsToImproveSettingsPlugin.class);
    private static final String tabTitle = "Parts to improve";

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 6;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elXRShortImprovement;
        Element elXRLongImprovement;
        Element elExitRules;
        Element elOTShortImprovement;
        Element elOrderTypes;
        Element elOTLongImprovement;
        Element elERShortImprovement;
        Element elERLongImprovement;
        Element elBT = elSettings.getChild("WhatToBuild");
        if (elBT == null) {
            return;
        }
        Element elST = elBT.getChild("StrategyType");
        if (elST == null) {
            return;
        }
        String strategyType = elST.getAttributeValue("type");
        if (!strategyType.equals("improve")) {
            return;
        }
        Element elPartsToImprove = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        Element elEntryRules = XMLUtil.tryAddElement((Element)elPartsToImprove, (String)"EntryRules");
        if (elEntryRules.getAttributeValue("symmetry") == null) {
            elEntryRules.setAttribute("symmetry", "true");
        }
        if ((elERLongImprovement = XMLUtil.tryAddElement((Element)elEntryRules, (String)"LongImprovement")).getAttributeValue("use") == null) {
            elERLongImprovement.setAttribute("use", "true");
        }
        if (elERLongImprovement.getAttributeValue("action") == null) {
            elERLongImprovement.setAttribute("action", "add-or-replace");
        }
        if ((elERShortImprovement = XMLUtil.tryAddElement((Element)elEntryRules, (String)"ShortImprovement")).getAttributeValue("use") == null) {
            elERShortImprovement.setAttribute("use", "true");
        }
        if (elERShortImprovement.getAttributeValue("action") == null) {
            elERShortImprovement.setAttribute("action", "add-or-replace");
        }
        if ((elOTLongImprovement = XMLUtil.tryAddElement((Element)(elOrderTypes = XMLUtil.tryAddElement((Element)elPartsToImprove, (String)"OrderTypes")), (String)"LongImprovement")).getAttributeValue("use") == null) {
            elOTLongImprovement.setAttribute("use", "true");
        }
        if ((elOTShortImprovement = XMLUtil.tryAddElement((Element)elOrderTypes, (String)"ShortImprovement")).getAttributeValue("use") == null) {
            elOTShortImprovement.setAttribute("use", "true");
        }
        if ((elExitRules = XMLUtil.tryAddElement((Element)elPartsToImprove, (String)"ExitRules")).getAttributeValue("symmetry") == null) {
            elExitRules.setAttribute("symmetry", "true");
        }
        if ((elXRLongImprovement = XMLUtil.tryAddElement((Element)elExitRules, (String)"LongImprovement")).getAttributeValue("use") == null) {
            elXRLongImprovement.setAttribute("use", "true");
        }
        if (elXRLongImprovement.getAttributeValue("action") == null) {
            elXRLongImprovement.setAttribute("action", "add-or-replace");
        }
        if ((elXRShortImprovement = XMLUtil.tryAddElement((Element)elExitRules, (String)"ShortImprovement")).getAttributeValue("use") == null) {
            elXRShortImprovement.setAttribute("use", "true");
        }
        if (elXRShortImprovement.getAttributeValue("action") == null) {
            elXRShortImprovement.setAttribute("action", "add-or-replace");
        }
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        Element elBT = elSettings.getChild("WhatToBuild");
        if (elBT == null) {
            return;
        }
        Element elST = elBT.getChild("StrategyType");
        if (elST == null) {
            return;
        }
        String strategyType = elST.getAttributeValue("type");
        if (!strategyType.equals("improve")) {
            return;
        }
        Element elPartsToImprove = null;
        try {
            elPartsToImprove = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
        PartsToImprove partsToImprove = new PartsToImprove();
        if (this.checkRules(elPartsToImprove, "EntryRules", partsToImprove, data) && this.checkRules(elPartsToImprove, "ExitRules", partsToImprove, data) && this.checkRules(elPartsToImprove, "OrderTypes", partsToImprove, data)) {
            try {
                data.addParam("PartsToImprove", (Serializable)partsToImprove);
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), null, "Cannot load Parts to improve - " + e.getMessage());
            }
        }
        this.verifyConfig(elPartsToImprove, elSettings, data);
    }

    private void verifyConfig(Element elPartsToImprove, Element elSettings, TaskSettingsData data) {
        boolean improveATM = Boolean.parseBoolean(XMLUtil.getAttr((Element)elPartsToImprove, (String)"improveATM", (String)"false"));
        boolean somethingImproved = false;
        List list1 = elPartsToImprove.getChildren();
        for (int i = 0; i < list1.size(); ++i) {
            Element elP = (Element)list1.get(i);
            List list2 = elP.getChildren();
            for (int j = 0; j < list2.size(); ++j) {
                Element elI = (Element)list2.get(j);
                boolean use = Boolean.parseBoolean(XMLUtil.getAttr((Element)elI, (String)"use", (String)"false"));
                if (!use) continue;
                somethingImproved = true;
                break;
            }
            if (somethingImproved) break;
        }
        if (!somethingImproved && !improveATM) {
            data.addError(this.getSettingName(), null, "You didn't select to improve any part of the strategy!");
        }
        if (improveATM) {
            Element elATMs = elSettings.getChild("ATMs");
            if (elATMs == null) {
                return;
            }
            boolean enable = XMLUtil.getBooleanAttr((Element)elATMs, (String)"enable", (boolean)false);
            if (!enable) {
                data.addError(this.getSettingName(), null, "You have chosen to improve ATM, but you didn't enabled ATM in ATM settings tab!");
            } else {
                int atmType = ATMTypes.recognize((String)elATMs.getAttributeValue("scaleOutType"), (int)2);
                if (atmType != 3) {
                    data.addError(this.getSettingName(), null, "You have chosen to improve ATM, but you didn't set ATM config to 'Generate' in ATM settings tab!");
                }
            }
        }
    }

    private boolean checkRules(Element elPartsToImprove, String elemName, PartsToImprove partsToImprove, TaskSettingsData data) {
        Element rulesElem = elPartsToImprove.getChild(elemName);
        if (rulesElem == null) {
            data.addError(this.getSettingName(), null, "Element '" + elemName + "' not found in config");
            return false;
        }
        Element elLongImprovement = rulesElem.getChild("LongImprovement");
        if (elLongImprovement == null) {
            data.addError(this.getSettingName(), null, elemName + " - Element 'LongImprovement' not found in config");
            return false;
        }
        Element elShortImprovement = rulesElem.getChild("ShortImprovement");
        if (elShortImprovement == null) {
            data.addError(this.getSettingName(), null, elemName + " - Element 'ShortImprovement' not found in config");
            return false;
        }
        boolean success = true;
        boolean isEntryRules = elemName.equals("EntryRules");
        boolean isExitRules = elemName.equals("ExitRules");
        boolean useLong = XMLUtil.elementIs((Element)elLongImprovement, (String)"use");
        boolean useShort = XMLUtil.elementIs((Element)elShortImprovement, (String)"use");
        if (isEntryRules || isExitRules) {
            String longActionType = elLongImprovement.getAttributeValue("action");
            try {
                this.checkActionType(longActionType);
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), null, elemName + " - Invalid long improvement action type '" + longActionType + "'");
                success = false;
            }
            String shortActionType = elShortImprovement.getAttributeValue("action");
            try {
                this.checkActionType(shortActionType);
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), null, elemName + " - Invalid short improvement action type '" + shortActionType + "'");
                success = false;
            }
            if (isEntryRules) {
                partsToImprove.useEntryLongImprovement = useLong;
                partsToImprove.useEntryShortImprovement = useShort;
                partsToImprove.entryLongAction = longActionType;
                partsToImprove.entryShortAction = shortActionType;
            } else {
                partsToImprove.useExitLongImprovement = useLong;
                partsToImprove.useExitShortImprovement = useShort;
                partsToImprove.exitLongAction = longActionType;
                partsToImprove.exitShortAction = shortActionType;
            }
        } else {
            partsToImprove.useOrderLongImprovement = useLong;
            partsToImprove.useOrderShortImprovement = useShort;
        }
        partsToImprove.improveATM = XMLUtil.getBooleanAttr((Element)elPartsToImprove, (String)"improveATM", (boolean)false);
        return success;
    }

    private void checkActionType(String type) throws Exception {
        switch (type) {
            case "add-or-replace": 
            case "replace": 
            case "add": {
                return;
            }
        }
        throw new Exception("");
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "PartsToImprove";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

