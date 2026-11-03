/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
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
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Notes;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Notes setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class NotesSettingsPlugin
implements ISettingTabPlugin {
    public static final Logger Log = LoggerFactory.getLogger(NotesSettingsPlugin.class);

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 100;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        XMLUtil.tryAddElement((Element)elSettings, (String)"Notes");
        try {
            Element elNotes = XMLUtil.getChildElem((Element)elSettings, (String)"Notes");
            String content = elNotes.getTextNormalize();
            content = content.replace("<div>", " ");
            content = content.replace("&nbsp;", " ");
            content = SQUtils.removeHtmlTags((String)content);
            data.addParam("Notes", (Serializable)((Object)content));
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elNotes = XMLUtil.getChildElem((Element)elSettings, (String)"Notes");
        String content = elNotes.getTextNormalize();
        content = content.replace("<div>", " ");
        content = content.replace("&nbsp;", " ");
        content = SQUtils.removeHtmlTags((String)content);
        settingsArray.put((Object)new JSONObject().put("key", (Object)"Notes").put("value", (Object)content));
    }

    public String getSettingName() {
        return "Notes";
    }

    public String getName() {
        return L.tsq((String)"Note");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

