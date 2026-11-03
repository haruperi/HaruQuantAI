/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.instrument.InstrumentManager
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
package com.strategyquant.plugin.Settings.impl.LoadFromFiles;

import com.strategyquant.datalib.instrument.InstrumentManager;
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
import java.io.File;
import java.io.Serializable;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Settings LoadFromFiles plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsLoadFromFiles
implements ISettingTabPlugin {
    private static final String tabTitle = "Load from files";

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elLoadFromFiles = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        try {
            String srcDirectory = XMLUtil.getChildElem((Element)elLoadFromFiles, (String)"SourceDirectory").getText();
            data.addParam("SourceDirectory", (Serializable)((Object)srcDirectory));
            if (srcDirectory.isEmpty()) {
                throw new Exception(L.t((String)"Source directory is not set.", (Object[])new Object[0]));
            }
            if (!new File(srcDirectory).exists()) {
                throw new Exception(L.t((String)"Source directory doesn't exist.", (Object[])new Object[0]));
            }
            data.addParam("IncludeSubdirectories", (Serializable)Boolean.valueOf(Boolean.parseBoolean(XMLUtil.getChildElem((Element)elLoadFromFiles, (String)"IncludeSubdirectories").getText())));
            Databank targetDatabank = ProjectConfigHelper.getInputDatabank((String)projectName, (Element)elLoadFromFiles.getParentElement());
            if (targetDatabank == null) {
                throw new Exception(L.t((String)"Target databank not found", (Object[])new Object[0]));
            }
            data.addParam("DatabankTarget", (Serializable)targetDatabank);
            int unrecognizedInstrumentAction = XMLUtil.getInt((Element)elLoadFromFiles, (String)"UnrecognizedInstrumentAction", (int)0);
            data.addParam("UnrecognizedInstrumentAction", (Serializable)Integer.valueOf(unrecognizedInstrumentAction));
            if (unrecognizedInstrumentAction == 1) {
                String instrument = XMLUtil.getChildElem((Element)elLoadFromFiles, (String)"UnrecognizedInstrumentValue").getText();
                if (!InstrumentManager.checkInstrumentExists((String)instrument)) {
                    throw new Exception(L.t((String)"Instrument doesn't exist.", (Object[])new Object[0]));
                }
                data.addParam("Instrument", (Serializable)((Object)instrument));
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot load LoadFromFiles settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "LoadFromFiles";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

