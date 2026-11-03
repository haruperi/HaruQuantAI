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
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.project.ProjectConditions
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.StopAndStart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.project.ProjectConditions;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="StopAndStart settings plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsStopAndStartPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SettingsStopAndStartPlugin.class);
    private ServletContextHandler dataContext;

    public Handler getHandler() {
        return null;
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 70;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elStopAndStart = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        XMLUtil.tryAddElement((Element)elStopAndStart, (String)"Conditions");
        Element elStartProject = XMLUtil.tryAddElement((Element)elStopAndStart, (String)"StartProject");
        if (elStartProject.getAttributeValue("use") == null) {
            elStartProject.setAttribute("use", "false");
        }
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        Element elStopAndStart = elSettings.getChild(this.getSettingName());
        Element elConditions = elStopAndStart.getChild("Conditions");
        try {
            ArrayList conditions = ProjectConditions.loadFromConfig((Element)elConditions);
            data.addParam("ProjectConditions", (Serializable)conditions);
        }
        catch (Exception e) {
            data.addError(this.getName(), null, e.getMessage());
        }
        Element elStartProject = elStopAndStart.getChild("StartProject");
        try {
            if (XMLUtil.elementIs((Element)elStartProject, (String)"use")) {
                data.addParam("ProjectToStart", (Serializable)((Object)elStartProject.getText()));
            }
        }
        catch (Exception e) {
            data.addError(this.getName(), null, e.getMessage());
        }
        try {
            data.addParam("SkipToFirstProject", (Serializable)Boolean.valueOf(XMLUtil.getBooleanAttr((Element)elStartProject, (String)"skipToFirstProject", (boolean)false)));
        }
        catch (Exception e) {
            data.addError(this.getName(), null, e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elRankings = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        IFitnessFunction ff = ProjectConfigHelper.getFitnessFunction((Element)elRankings);
        Element elMaxStrategies = XMLUtil.getChildElem((Element)elRankings, (String)"MaxStrategies");
        String maxStrategies = elMaxStrategies != null ? "" + Integer.parseInt(elMaxStrategies.getText()) : "N/A";
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Maximum top strategies to store", (Object[])new Object[0])).put("value", (Object)maxStrategies));
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Fitness computation", (Object[])new Object[0])).put("value", (Object)ff.getFitnessName()));
    }

    public String getSettingName() {
        return "StopAndStart";
    }

    public String getName() {
        return L.tsq((String)"Stop & Start");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

