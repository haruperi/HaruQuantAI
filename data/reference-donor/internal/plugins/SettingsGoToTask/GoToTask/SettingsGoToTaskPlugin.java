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
 *  com.strategyquant.tradinglib.project.ProjectConditions
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Settings.impl.GoToTask;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.project.ProjectConditions;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.Serializable;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Settings GoToTask plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsGoToTaskPlugin
implements ISettingTabPlugin {
    private static final String tabTitle = "Go To Task";

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elGoToTask = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        Element elConditions = XMLUtil.tryAddElement((Element)elGoToTask, (String)"Conditions");
        try {
            elGoToTask = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
            elConditions = XMLUtil.tryAddElement((Element)elGoToTask, (String)"Conditions");
        }
        catch (Exception e) {
            data.addError(tabTitle, null, e.getMessage());
            return;
        }
        String goToTaskName = elGoToTask.getAttributeValue("task");
        if (goToTaskName == null) {
            data.addError(tabTitle, "Task", L.t((String)"Task not set.", (Object[])new Object[0]));
            return;
        }
        try {
            SQProject project = ProjectEngine.get((String)projectName);
            Element taskEl = project.getTaskConfigByName(goToTaskName);
            if (taskEl == null) {
                data.addError(tabTitle, "Task", L.t((String)"Task with name '%s' not found.", (Object[])new Object[]{goToTaskName}));
                return;
            }
            boolean active = Boolean.parseBoolean(XMLUtil.tryGetAttr((Element)taskEl, (String)"active", (String)"true"));
            if (!active) {
                data.addError(tabTitle, "Task", L.t((String)"Task '%s' is disabled.", (Object[])new Object[]{goToTaskName}));
                return;
            }
        }
        catch (Exception e) {
            data.addError(tabTitle, null, e.getMessage());
        }
        try {
            ArrayList conditions = ProjectConditions.loadFromConfig((Element)elConditions);
            data.addParam("ProjectConditions", (Serializable)conditions);
            data.addParam("GoToTaskName", (Serializable)((Object)goToTaskName));
            data.addParam("GoToTaskResetEvaluatedCycles", (Serializable)Boolean.valueOf(XMLUtil.getBooleanAttr((Element)elGoToTask, (String)"resetEvaluatedCycles", (boolean)false)));
            data.addParam("GoToTaskResetActivatedCycles", (Serializable)Boolean.valueOf(XMLUtil.getBooleanAttr((Element)elGoToTask, (String)"resetActivatedCycles", (boolean)false)));
        }
        catch (Exception e) {
            data.addError(tabTitle, null, e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "GoToTask";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

