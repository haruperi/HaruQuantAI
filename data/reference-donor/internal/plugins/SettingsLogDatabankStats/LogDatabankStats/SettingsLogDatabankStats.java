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
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.LogDatabankStats;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Log databank stats setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsLogDatabankStats
implements ISettingTabPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SettingsLogDatabankStats.class);

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 500;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elLogDatabankStats = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        try {
            String databankName = "Results";
            if (elLogDatabankStats.getChild("Databank") != null) {
                databankName = XMLUtil.getNodeValue((Element)elLogDatabankStats, (String)"Databank", (String)"Results");
            }
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            data.addParam("DatabankSource", (Serializable)databank);
            ArrayList<Object[]> logStats = new ArrayList<Object[]>();
            List logStatsEls = elLogDatabankStats.getChildren("LogStats");
            for (int a = 0; a < logStatsEls.size(); ++a) {
                Element logStatsEl = (Element)logStatsEls.get(a);
                String type = XMLUtil.getAttr((Element)logStatsEl, (String)"type", (String)"sum");
                Object[] logStatsItem = new Object[3];
                logStatsItem[0] = type;
                logStatsItem[1] = ProjectConfigHelper.getConditions((Element)logStatsEl.getChild("Conditions"));
                Object object = logStatsItem[2] = logStatsEl.getChild("Column") != null ? ProjectConfigHelper.getConditionValue((Element)logStatsEl.getChild("Column")) : null;
                if (!(type.equals("sum") || type.equals("avg") || type.equals("count"))) {
                    throw new Exception(L.t((String)"Invalid stats type. Must be one of (sum, avg, count).", (Object[])new Object[0]));
                }
                if ((type.equals("sum") || type.equals("avg")) && logStatsItem[2] == null) {
                    throw new Exception(L.t((String)"Missing column (stats name) definition.", (Object[])new Object[0]));
                }
                logStats.add(logStatsItem);
            }
            data.addParam("LogStats", logStats);
        }
        catch (Exception e) {
            data.addError(this.getName(), null, "Cannot load settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "LogDatabankStats";
    }

    public String getName() {
        return L.tsq((String)"Log databank stats");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

