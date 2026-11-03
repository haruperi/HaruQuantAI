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
package com.strategyquant.plugin.Settings.impl.CreatePortfolio;

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
@Name(name="Settings CreatePortfolio plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsCreatePortfolio
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
        Element elCreatePortfolio = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        try {
            data.addParam("MaxStrategies", (Serializable)Integer.valueOf(XMLUtil.getInt((Element)elCreatePortfolio, (String)"MaxStrategies", (int)100)));
            Databank sourceDatabank = ProjectConfigHelper.getInputDatabank((String)projectName, (Element)elCreatePortfolio.getParentElement());
            if (sourceDatabank == null) {
                throw new Exception(L.t((String)"Source databank not found", (Object[])new Object[0]));
            }
            data.addParam("DatabankSource", (Serializable)sourceDatabank);
            Databank targetDatabank = ProjectConfigHelper.getOutputDatabank((String)projectName, (Element)elCreatePortfolio.getParentElement());
            if (targetDatabank == null) {
                throw new Exception(L.t((String)"Target databank not found", (Object[])new Object[0]));
            }
            data.addParam("DatabankTarget", (Serializable)targetDatabank);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot load SaveToFiles settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "CreatePortfolio";
    }

    public String getName() {
        return L.tsq((String)"Save to files");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

