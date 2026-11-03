/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.volumeProfile.VolumeProfileBlocks
 *  com.strategyquant.lib.volumeProfile.VolumeProfileSubscription
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.blocks.random.BlockDefinition
 *  com.strategyquant.tradinglib.blocks.random.BlocksConfig
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.task.settings.blocks.ConfigVerifier
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Blocks;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.volumeProfile.VolumeProfileBlocks;
import com.strategyquant.lib.volumeProfile.VolumeProfileSubscription;
import com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.task.settings.blocks.ConfigVerifier;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="Blocks servlet plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class BlocksSettingsPlugin
implements ISettingTabPlugin,
IServletPlugin,
IProgram {
    public static final Logger Log = LoggerFactory.getLogger(BlocksSettingsPlugin.class);
    private static final String tabTitle = "Building Blocks";
    private ServletContextHandler dataContext;
    private BlocksServlet servlet;

    public Handler getHandler() {
        if (this.dataContext == null) {
            if (this.servlet == null) {
                this.servlet = new BlocksServlet();
            }
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/blocks/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 30;
    }

    public void initPlugin() throws Exception {
        this.servlet = new BlocksServlet();
        Program.register((String)"Blocks", (IProgram)this);
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (this.servlet == null) {
            this.servlet = new BlocksServlet();
        }
        return this.servlet.execute(methodName, parameters == null || parameters.length == 0 ? new HashMap<String, String[]>() : (Map)parameters[0], null);
    }

    private void fixSettings(Element elSettings) {
        this.fixCustomBlocks(elSettings);
    }

    private void fixCustomBlocks(Element elSettings) {
        try {
            JSONArray customBlocks = CustomBlocks.getAsBuildingBlocks();
            HashMap<String, JSONObject> cbMap = new HashMap<String, JSONObject>();
            for (int i = 0; i < customBlocks.length(); ++i) {
                JSONObject cb = customBlocks.getJSONObject(i);
                String key = cb.getString("key");
                cbMap.put(key, cb);
            }
            Element elBlocksSet = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
            Element elBuildingBlocks = XMLUtil.tryAddElement((Element)elBlocksSet, (String)"BuildingBlocks");
            List elBlocks = elBuildingBlocks.getChildren("Block");
            for (int i = 0; i < elBlocks.size(); ++i) {
                Element elGenerated;
                JSONObject cb;
                Element elBlock = (Element)elBlocks.get(i);
                String key = elBlock.getAttributeValue("key");
                if (key == null || !key.startsWith("CBlock_") || (cb = (JSONObject)cbMap.get(key)) == null || (elGenerated = elBlock.getChild("Generated")) == null) continue;
                List elParams = elGenerated.getChildren("Param");
                JSONArray cbParams = cb.getJSONArray("params");
                if (elParams.size() == cbParams.length()) continue;
                Log.info("Fixing CB with key '" + key + "' - updating params, expected count: " + cbParams.length() + ", existing count: " + elParams.size());
                elGenerated.removeChildren("Param");
                for (int p = 0; p < cbParams.length(); ++p) {
                    JSONObject cbParam = cbParams.getJSONObject(p);
                    Element elParam = new Element("Param");
                    for (String attrKey : cbParam.keySet()) {
                        String atrValue = cbParam.get(attrKey).toString();
                        elParam.setAttribute(attrKey, atrValue);
                    }
                    elGenerated.addContent((Content)elParam);
                }
            }
        }
        catch (Exception e) {
            Log.error("Error while fixing Custom blocks in settings.", (Throwable)e);
        }
    }

    private void disableVPBlocksIfInactive(Element elBuildingBlocks) {
        if (VolumeProfileSubscription.getInstance().isActive()) {
            return;
        }
        for (Element elBlock : elBuildingBlocks.getChildren("Block")) {
            String baseKey;
            String key = elBlock.getAttributeValue("key");
            if (key == null || !VolumeProfileBlocks.contains((String)(baseKey = key.contains(".") ? key.substring(key.lastIndexOf(".") + 1) : key))) continue;
            elBlock.setAttribute("use", "false");
        }
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elExitTypes;
        Element elOrderTypes;
        Element elBuildingBlocks;
        BlocksConfig blocksConfig = null;
        this.fixSettings(elSettings);
        try {
            Element elBlocks = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
            elBuildingBlocks = XMLUtil.tryAddElement((Element)elBlocks, (String)"BuildingBlocks");
            elOrderTypes = XMLUtil.tryAddElement((Element)elBlocks, (String)"OrderTypes");
            elExitTypes = XMLUtil.tryAddElement((Element)elBlocks, (String)"ExitTypes");
            Element elCustomData = XMLUtil.tryAddElement((Element)elBlocks, (String)"CustomData");
            this.disableVPBlocksIfInactive(elBuildingBlocks);
            data.addParam("BuildingBlocks", (Serializable)elBuildingBlocks);
            data.addParam("OrderTypes", (Serializable)elOrderTypes);
            data.addParam("ExitTypes", (Serializable)elExitTypes);
            data.addParam("CustomData", (Serializable)elCustomData);
        }
        catch (Exception e) {
            Log.error("Cannot load blocks config from XML file.", (Throwable)e);
            data.addError(tabTitle, null, "Cannot load blocks config from XML file. Error: " + e.getMessage());
            return;
        }
        try {
            blocksConfig = BlocksConfig.getConfig();
            ConfigVerifier.verifyConfig((Element)elSettings, (BlocksConfig)blocksConfig, (TaskSettingsData)data);
        }
        catch (Exception e) {
            Log.error("Cannot load blocks config from XML file.", (Throwable)e);
            data.addError(tabTitle, null, "Cannot load blocks config from XML file. Error: " + e.getMessage());
            return;
        }
        try {
            data.addParam("BlocksConfig", (Serializable)elSettings);
            data.addParam("BlocksDesciption", (Serializable)((Object)this.generateBlockDescription(elBuildingBlocks, elOrderTypes, elExitTypes)));
        }
        catch (Exception e) {
            Log.error("Error while converting simple blocks.", (Throwable)e);
            data.addError(tabTitle, null, "Error while converting simple blocks. Error: " + e.getMessage());
            return;
        }
    }

    private String generateBlockDescription(Element elBuildingBlocks, Element elOrderTypes, Element elExitTypes) {
        int countBlocks = XMLUtil.countElements((String)"Block", (Element)elBuildingBlocks, (int)0);
        int countET = XMLUtil.countElements((String)"Block", (Element)elExitTypes, (int)0);
        return L.t((String)"%d entry blocks, %d exit types", (Object[])new Object[]{countBlocks, countET});
    }

    public String getSettingName() {
        return "Blocks";
    }

    public String getName() {
        return L.tsq((String)"Building blocks");
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elBlocks = elSettings.getChild("Blocks");
        if (elBlocks == null) {
            return;
        }
        Element elBuildingBlocks = elSettings.getChild("BuildingBlocks");
        if (elBuildingBlocks == null) {
            return;
        }
        Element elOrderTypes = elSettings.getChild("OrderTypes");
        if (elOrderTypes == null) {
            return;
        }
        Element elExitTypes = elSettings.getChild("ExitTypes");
        if (elExitTypes == null) {
            return;
        }
        Element elCustomData = elSettings.getChild("CustomData");
        if (elCustomData == null) {
            return;
        }
        BlocksConfig blocksConfig = BlocksConfig.getConfig();
        this.addBlocks(elBuildingBlocks, settingsArray, blocksConfig);
        this.addBlocks(elOrderTypes, settingsArray, blocksConfig);
        this.addBlocks(elExitTypes, settingsArray, blocksConfig);
        this.addBlocks(elCustomData, settingsArray, blocksConfig);
    }

    private void addBlocks(Element blocks, JSONArray data, BlocksConfig blocksConfig) {
        for (Element elBlock : blocks.getChildren("Block")) {
            String key = elBlock.getAttributeValue("key");
            BlockDefinition block = blocksConfig.getBlock(key);
            if (XMLUtil.elementIsNot((Element)elBlock, (String)"use")) continue;
            String blockName = block != null ? block.getName() : key;
            data.put((Object)new JSONObject().put("key", (Object)blockName).put("value", (Object)L.t((String)"yes", (Object[])new Object[0])));
        }
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("stockpickerDefaultBlocks", (Object)this.servlet.loadStockpickerDefaultBlocks());
        return data;
    }
}

