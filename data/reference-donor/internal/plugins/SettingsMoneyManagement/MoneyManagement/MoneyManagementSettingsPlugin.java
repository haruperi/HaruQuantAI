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
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.RiskManagementMethod
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.propertygrid.IPGParameter
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.MoneyManagement;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Money management servlet plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class MoneyManagementSettingsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(MoneyManagementSettingsPlugin.class);
    private static final String tabTitle = "Money management";

    public Handler getHandler() {
        return null;
    }

    public String getProduct() {
        return "SQUANTAlgoWizardAlgoWizardStandaloneAlgoWizardCloud";
    }

    public int getPreferredPosition() {
        return 20;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elRiskMoneyManagement = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        Element elMoneyManagement = XMLUtil.tryAddElement((Element)elRiskMoneyManagement, (String)"MoneyManagement");
        try {
            XMLUtil.getChildElem((Element)elMoneyManagement, (String)"Method");
        }
        catch (Exception e) {
            Element elMethod = XMLUtil.tryAddElement((Element)elMoneyManagement, (String)"Method");
            elMethod.setAttribute("use", "true");
            Element elParams = XMLUtil.tryAddElement((Element)elMethod, (String)"Params");
            Element elParameter = XMLUtil.tryAddElement((Element)elParams, (String)"Param");
            if (this.isCloudEngineTask(elSettings)) {
                elMethod.setAttribute("type", "PickerRiskFixedPctOfAccount");
                elParameter.setAttribute("key", "Risk");
                elParameter.setAttribute("className", "PickerRiskFixedPctOfAccount");
                elParameter.setText("10");
            }
            elMethod.setAttribute("type", "FixedSize");
            elParameter.setAttribute("key", "Size");
            elParameter.setAttribute("className", "FixedSize");
            elParameter.setText("0.1");
        }
        try {
            XMLUtil.getChildElem((Element)elMoneyManagement, (String)"InitialCapital");
        }
        catch (Exception e) {
            Element elInitialCapital = XMLUtil.tryAddElement((Element)elMoneyManagement, (String)"InitialCapital");
            elInitialCapital.setText("10000");
        }
        Element elRiskManagement = XMLUtil.tryAddElement((Element)elRiskMoneyManagement, (String)"RiskManagement");
        try {
            XMLUtil.getChildElem((Element)elRiskManagement, (String)"Method");
        }
        catch (Exception e) {
            Element elMethod = XMLUtil.tryAddElement((Element)elRiskManagement, (String)"Method");
            elMethod.setAttribute("type", "AllowAllTrades");
            elMethod.setAttribute("use", "true");
            elMethod.addContent((Content)new Element("Params"));
        }
    }

    private boolean isCloudEngineTask(Element elSettings) {
        try {
            Element elSetup = XMLUtil.getChildElem((Element)elSettings, (String)"Data").getChild("Setups").getChild("Setup");
            return Engines.isAWCloudEngine((int)Engines.getEngine((String)elSetup.getAttributeValue("engine")));
        }
        catch (Exception e) {
            return false;
        }
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        Element elMoneyManagement = null;
        Element elRiskManagement = null;
        try {
            Element elRiskMoneyManagement = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
            elMoneyManagement = XMLUtil.getChildElem((Element)elRiskMoneyManagement, (String)"MoneyManagement");
            elRiskManagement = XMLUtil.getChildElem((Element)elRiskMoneyManagement, (String)"RiskManagement");
        }
        catch (Exception e) {
            data.addError(tabTitle, null, e.getMessage());
            return;
        }
        try {
            MoneyManagementMethod mmMethod = ProjectConfigHelper.getMoneyManagement((Element)elMoneyManagement);
            if (this.isCloudEngineTask(elSettings) && !"SP,SA".equals(mmMethod.getEngine())) {
                data.addError(tabTitle, null, L.t((String)"The specified MM method %s is not supported by Stockpicker engine.", (Object[])new Object[]{mmMethod.printFormatedName()}));
            }
            data.addParam("MoneyManagement.Method", (Serializable)mmMethod);
            double initialCapital = Double.parseDouble(XMLUtil.getChildElem((Element)elMoneyManagement, (String)"InitialCapital").getValue());
            data.addParam("MoneyManagement.InitialCapital", (Serializable)Double.valueOf(initialCapital));
        }
        catch (Exception e) {
            data.addError(tabTitle, null, "Cannot load MoneyManagement settings. " + e.getMessage());
        }
        try {
            data.addParam("RiskManagement", (Serializable)ProjectConfigHelper.getRiskManagement((Element)elRiskManagement));
        }
        catch (Exception e) {
            data.addError(tabTitle, null, "Cannot load RiskManagement settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elMoneyManagement = null;
        Element elRiskManagement = null;
        try {
            Element elRiskMoneyManagement = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
            elMoneyManagement = XMLUtil.getChildElem((Element)elRiskMoneyManagement, (String)"MoneyManagement");
            elRiskManagement = XMLUtil.getChildElem((Element)elRiskMoneyManagement, (String)"RiskManagement");
        }
        catch (Exception e) {
            return;
        }
        MoneyManagementMethod mmMethod = ProjectConfigHelper.getMoneyManagement((Element)elMoneyManagement);
        RiskManagementMethod rmMethod = ProjectConfigHelper.getRiskManagement((Element)elRiskManagement);
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Initial capital").put("value", mmMethod.getInitialCapital()));
        String mm = mmMethod.getName();
        String mmParams = "";
        ArrayList params = mmMethod.getParams();
        for (IPGParameter parameter : params) {
            mmParams = mmParams + parameter.getName() + " " + parameter.print() + ",";
        }
        if (mmParams.length() > 0) {
            mm = mm + " - " + mmParams;
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Money Management method", (Object[])new Object[0])).put("value", (Object)mm));
        String rm = rmMethod.getName();
        String rmParams = "";
        params = rmMethod.getParams();
        for (IPGParameter parameter : params) {
            rmParams = rmParams + parameter.getName() + " " + parameter.print() + ",";
        }
        if (rmParams.length() > 0) {
            rm = rm + " - " + rmParams;
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Risk Management method", (Object[])new Object[0])).put("value", (Object)rm));
    }

    public String getSettingName() {
        return "RiskMoneyManagement";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

