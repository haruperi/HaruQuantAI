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
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Settings.impl.CallExternalScript;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
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
@Name(name="Settings Call external script")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsCallExternalScript
implements ISettingTabPlugin {
    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elCallExternalScript = null;
        try {
            elCallExternalScript = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
        try {
            String file = XMLUtil.getNodeValue((Element)elCallExternalScript, (String)"File");
            if (file == null || file.trim().isEmpty()) {
                throw new Exception(L.t((String)"File not set.", (Object[])new Object[0]));
            }
            data.addParam("File", (Serializable)((Object)file));
            String params = XMLUtil.getStringAttr((Element)elCallExternalScript.getChild("File"), (String)"params", null);
            data.addParam("Params", (Serializable)((Object)params));
            Element elWaitFor = XMLUtil.getChildElem((Element)elCallExternalScript, (String)"WaitFor");
            String type = elWaitFor.getText();
            data.addParam("Type", (Serializable)((Object)type));
            if (type.equals("time")) {
                int hours = Integer.parseInt(elWaitFor.getAttributeValue("hours"));
                int minutes = Integer.parseInt(elWaitFor.getAttributeValue("minutes"));
                long time = hours * 3600 * 1000 + minutes * 60 * 1000;
                data.addParam("MaxBuildRunTime", (Serializable)Long.valueOf(time));
            } else {
                data.addParam("MaxBuildRunTime", (Serializable)Long.valueOf(0L));
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, L.t((String)"Cannot load Call external script settings. ", (Object[])new Object[0]) + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "CallExternalScript";
    }

    public String getName() {
        return L.tsq((String)"Call external script");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

