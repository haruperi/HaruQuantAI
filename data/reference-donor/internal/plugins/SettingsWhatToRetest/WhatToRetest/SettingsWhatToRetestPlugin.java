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
package com.strategyquant.plugin.Settings.impl.WhatToRetest;

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
@Name(name="What To Retest setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsWhatToRetestPlugin
implements ISettingTabPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SettingsWhatToRetestPlugin.class);

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        XMLUtil.tryAddElement((Element)elSettings, (String)"Databanks");
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        Databank resultsDb = null;
        try {
            resultsDb = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)"Results");
        }
        catch (Exception e1) {
            String message = "Project '" + projectName + "' doesn't exist in ProjectEngine";
            Log.error(message);
            data.addError(this.getSettingName(), null, message);
        }
        Databank inputDb = null;
        try {
            inputDb = ProjectConfigHelper.getInputDatabank((String)projectName, (Element)elSettings);
        }
        catch (Exception e) {
            inputDb = resultsDb;
        }
        Databank outputDb = null;
        try {
            outputDb = ProjectConfigHelper.getOutputDatabank((String)projectName, (Element)elSettings);
        }
        catch (Exception e) {
            outputDb = resultsDb;
        }
        try {
            data.addParam("DatabankSource", (Serializable)inputDb);
            data.addParam("DatabankTarget", (Serializable)outputDb);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
        }
        try {
            Element elDatabanks = elSettings.getChild("Databanks");
            if (elDatabanks == null) {
                return;
            }
            String retestSelected = elDatabanks.getAttributeValue("retestSelected", "false");
            if (!retestSelected.equals("true")) {
                return;
            }
            ArrayList<String> strategiesToRetest = new ArrayList<String>();
            Element elSelectedStrategies = elSettings.getChild("SelectedStrategies");
            if (elSelectedStrategies != null) {
                List strategiesElems = elSelectedStrategies.getChildren("Strategy");
                for (int a = 0; a < strategiesElems.size(); ++a) {
                    Element elStrategy = (Element)strategiesElems.get(a);
                    strategiesToRetest.add(elStrategy.getText());
                }
            }
            data.addParam("StrategiesToRetest", strategiesToRetest);
        }
        catch (Exception e) {
            Log.error("Cannot load strategies to retest", (Throwable)e);
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "Databanks";
    }

    public String getName() {
        return L.tsq((String)"What to retest");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

