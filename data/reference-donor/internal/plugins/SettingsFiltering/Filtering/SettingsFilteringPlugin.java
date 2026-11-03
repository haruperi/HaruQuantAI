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
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Settings.impl.Filtering;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Settings Filtering plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsFilteringPlugin
implements ISettingTabPlugin {
    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elFiltering = null;
        try {
            elFiltering = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
        try {
            int actionType = Integer.parseInt(XMLUtil.getChildElem((Element)elFiltering, (String)"ActionType").getText());
            Databank srcDatabank = ProjectConfigHelper.getDatabankByType((String)projectName, (String)"Source", (Element)elSettings);
            Databank tgtDatabank = ProjectConfigHelper.getDatabankByType((String)projectName, (String)"Target", (Element)elSettings);
            if (srcDatabank == null) {
                throw new Exception(L.t((String)"Source databank not found", (Object[])new Object[0]));
            }
            if (actionType != 0 && tgtDatabank == null) {
                throw new Exception(L.t((String)"Target databank not found", (Object[])new Object[0]));
            }
            data.addParam("DatabankSource", (Serializable)srcDatabank);
            data.addParam("DatabankTarget", (Serializable)tgtDatabank);
            data.addParam("ActionType", (Serializable)Integer.valueOf(actionType));
            data.addParam("ConditionsType", (Serializable)Integer.valueOf(Integer.parseInt(XMLUtil.getChildElem((Element)elFiltering, (String)"ConditionsType").getText())));
            data.addParam("Conditions", (Serializable)ProjectConfigHelper.getConditions((Element)elFiltering.getChild("Conditions")));
            data.addParam("MaxStrategiesFilter", (Serializable)Integer.valueOf(XMLUtil.getInt((Element)elFiltering, (String)"MaxStrategies", (int)0)));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, L.t((String)"Cannot load Filtering settings. ", (Object[])new Object[0]) + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "Filtering";
    }

    public String getName() {
        return L.tsq((String)"Filtering");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

